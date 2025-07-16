"""
Modelos base para sistema multitenant.

Este módulo fornece classes base que implementam funcionalidades
multitenant para modelos Django, incluindo managers e querysets
que automaticamente filtram dados por tenant.
"""

from django.db import models
from django.core.exceptions import ValidationError
from .utils import get_current_tenant


class TenantAwareManager(models.Manager):
    """
    Manager base para modelos tenant-aware.
    
    Este manager garante que todas as operações sejam automaticamente
    filtradas pelo tenant atual, proporcionando isolamento de dados.
    """

    def get_queryset(self):
        """
        Retorna o QuerySet base filtrado pelo tenant atual.
        
        Returns:
            QuerySet: QuerySet filtrado pelo tenant
        """
        queryset = super().get_queryset()
        
        # Aplica filtro de tenant automaticamente
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            queryset = queryset.filter(tenant=tenant)
        elif tenant and hasattr(self.model, '_meta'):
            # Verifica se o modelo tem campo tenant implícito
            tenant_fields = [f for f in self.model._meta.fields 
                           if f.name in ['tenant', 'tenant_id']]
            if tenant_fields:
                queryset = queryset.filter(**{tenant_fields[0].name: tenant})
        
        return queryset

    def create(self, **kwargs):
        """
        Cria um novo objeto associado ao tenant atual.
        
        Args:
            **kwargs: Argumentos para criação do objeto
            
        Returns:
            Model: Instância do objeto criado
        """
        # Adiciona o tenant atual automaticamente
        tenant = get_current_tenant()
        if tenant and 'tenant' not in kwargs:
            if hasattr(self.model, 'tenant'):
                kwargs['tenant'] = tenant
            elif hasattr(self.model, 'tenant_id'):
                kwargs['tenant_id'] = tenant.id
        
        return super().create(**kwargs)

    def bulk_create(self, objs, **kwargs):
        """
        Cria múltiplos objetos associados ao tenant atual.
        
        Args:
            objs: Lista de objetos a serem criados
            **kwargs: Argumentos adicionais
            
        Returns:
            list: Lista de objetos criados
        """
        # Adiciona o tenant atual a todos os objetos
        tenant = get_current_tenant()
        if tenant:
            for obj in objs:
                if hasattr(obj, 'tenant') and not obj.tenant:
                    obj.tenant = tenant
                elif hasattr(obj, 'tenant_id') and not obj.tenant_id:
                    obj.tenant_id = tenant.id
        
        return super().bulk_create(objs, **kwargs)


class TenantAwareModel(models.Model):
    """
    Modelo base abstrato para modelos que devem ser isolados por tenant.
    
    Este modelo adiciona automaticamente:
    - Campo tenant (ForeignKey para Tenant)
    - Manager que filtra automaticamente por tenant
    - Validações para garantir isolamento de dados
    - Métodos utilitários para operações tenant-aware
    """
    
    # Campo tenant será adicionado automaticamente
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        help_text="Tenant ao qual este registro pertence"
    )
    
    # Manager padrão que filtra por tenant
    objects = TenantAwareManager()
    
    # Manager que não filtra por tenant (para operações administrativas)
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
        # Adiciona índice no campo tenant para performance
        indexes = [
            models.Index(fields=['tenant']),
        ]

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que o tenant seja definido.
        """
        # Define o tenant atual se não foi especificado
        if not self.tenant_id:
            current_tenant = get_current_tenant()
            if current_tenant:
                self.tenant = current_tenant
            else:
                raise ValidationError(
                    "Não é possível salvar o objeto sem um tenant definido. "
                    "Certifique-se de que há um tenant no contexto atual."
                )
        
        # Valida se o tenant está ativo
        if self.tenant and not self.tenant.is_active:
            raise ValidationError(
                f"Não é possível salvar dados para o tenant inativo: {self.tenant.name}"
            )
        
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validações customizadas para garantir integridade dos dados.
        """
        super().clean()
        
        # Valida se o tenant está definido
        if not self.tenant_id:
            current_tenant = get_current_tenant()
            if not current_tenant:
                raise ValidationError(
                    "Tenant é obrigatório para este modelo."
                )
            self.tenant = current_tenant
        
        # Valida se o tenant está ativo
        if self.tenant and not self.tenant.is_active:
            raise ValidationError(
                f"Tenant {self.tenant.name} está inativo."
            )

    def delete(self, *args, **kwargs):
        """
        Sobrescreve o método delete para adicionar validações de tenant.
        """
        # Verifica se o tenant atual tem permissão para deletar
        current_tenant = get_current_tenant()
        if current_tenant and self.tenant != current_tenant:
            raise ValidationError(
                "Não é possível deletar objetos de outros tenants."
            )
        
        super().delete(*args, **kwargs)

    @classmethod
    def get_for_tenant(cls, tenant):
        """
        Retorna um QuerySet filtrado para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            QuerySet: QuerySet filtrado pelo tenant
        """
        return cls.all_objects.filter(tenant=tenant)

    @classmethod
    def create_for_tenant(cls, tenant, **kwargs):
        """
        Cria um novo objeto para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            **kwargs: Argumentos para criação do objeto
            
        Returns:
            Model: Instância do objeto criado
        """
        kwargs['tenant'] = tenant
        return cls.objects.create(**kwargs)

    def is_owned_by_tenant(self, tenant):
        """
        Verifica se este objeto pertence ao tenant especificado.
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            bool: True se o objeto pertence ao tenant
        """
        return self.tenant == tenant

    def get_tenant_context_data(self):
        """
        Retorna dados de contexto do tenant para este objeto.
        
        Returns:
            dict: Dados de contexto do tenant
        """
        return {
            'tenant_id': self.tenant.id,
            'tenant_name': self.tenant.name,
            'tenant_subdomain': self.tenant.subdomain,
            'tenant_schema': self.tenant.schema_name,
        }


class TenantAwareQuerySet(models.QuerySet):
    """
    QuerySet customizado que adiciona métodos específicos para multitenant.
    """

    def for_tenant(self, tenant):
        """
        Filtra o QuerySet para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            QuerySet: QuerySet filtrado pelo tenant
        """
        return self.filter(tenant=tenant)

    def exclude_tenant(self, tenant):
        """
        Exclui registros de um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            QuerySet: QuerySet sem registros do tenant especificado
        """
        return self.exclude(tenant=tenant)

    def current_tenant(self):
        """
        Filtra o QuerySet para o tenant atual.
        
        Returns:
            QuerySet: QuerySet filtrado pelo tenant atual
        """
        tenant = get_current_tenant()
        if tenant:
            return self.for_tenant(tenant)
        return self.none()

    def active_tenants_only(self):
        """
        Filtra apenas registros de tenants ativos.
        
        Returns:
            QuerySet: QuerySet com registros apenas de tenants ativos
        """
        return self.filter(tenant__is_active=True)

    def bulk_create_for_tenant(self, tenant, objs, **kwargs):
        """
        Cria múltiplos objetos para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            objs: Lista de objetos a serem criados
            **kwargs: Argumentos adicionais para bulk_create
            
        Returns:
            list: Lista de objetos criados
        """
        # Adiciona o tenant a todos os objetos
        for obj in objs:
            obj.tenant = tenant
        
        return self.bulk_create(objs, **kwargs)

    def update_for_tenant(self, tenant, **kwargs):
        """
        Atualiza registros de um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            **kwargs: Campos a serem atualizados
            
        Returns:
            int: Número de registros atualizados
        """
        return self.for_tenant(tenant).update(**kwargs)

    def delete_for_tenant(self, tenant):
        """
        Deleta registros de um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            tuple: (número de objetos deletados, detalhes por tipo)
        """
        return self.for_tenant(tenant).delete()

    def count_by_tenant(self):
        """
        Conta registros agrupados por tenant.
        
        Returns:
            dict: Dicionário com contagem por tenant
        """
        from django.db.models import Count
        
        result = {}
        counts = self.values('tenant__name').annotate(count=Count('id'))
        
        for item in counts:
            result[item['tenant__name']] = item['count']
        
        return result

    def latest_by_tenant(self, tenant, field_name='id'):
        """
        Retorna o registro mais recente de um tenant.
        
        Args:
            tenant: Instância do modelo Tenant
            field_name: Nome do campo para ordenação (padrão: 'id')
            
        Returns:
            Model: Instância do objeto mais recente
        """
        return self.for_tenant(tenant).latest(field_name)

    def earliest_by_tenant(self, tenant, field_name='id'):
        """
        Retorna o registro mais antigo de um tenant.
        
        Args:
            tenant: Instância do modelo Tenant
            field_name: Nome do campo para ordenação (padrão: 'id')
            
        Returns:
            Model: Instância do objeto mais antigo
        """
        return self.for_tenant(tenant).earliest(field_name)


class TenantAwareManagerFromQuerySet(models.Manager):
    """
    Manager que usa o TenantAwareQuerySet customizado.
    """

    def get_queryset(self):
        """
        Retorna o QuerySet customizado filtrado pelo tenant atual.
        
        Returns:
            TenantAwareQuerySet: QuerySet customizado
        """
        queryset = TenantAwareQuerySet(self.model, using=self._db)
        
        # Aplica filtro de tenant automaticamente
        tenant = get_current_tenant()
        if tenant:
            queryset = queryset.for_tenant(tenant)
        
        return queryset

    def for_tenant(self, tenant):
        """
        Retorna um QuerySet para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            QuerySet: QuerySet filtrado pelo tenant
        """
        return self.get_queryset().for_tenant(tenant)

    def all_tenants(self):
        """
        Retorna um QuerySet com dados de todos os tenants.
        
        Returns:
            QuerySet: QuerySet sem filtro de tenant
        """
        return TenantAwareQuerySet(self.model, using=self._db)

    def create_for_tenant(self, tenant, **kwargs):
        """
        Cria um objeto para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            **kwargs: Argumentos para criação
            
        Returns:
            Model: Objeto criado
        """
        kwargs['tenant'] = tenant
        return self.create(**kwargs)

    def get_or_create_for_tenant(self, tenant, defaults=None, **kwargs):
        """
        Obtém ou cria um objeto para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            defaults: Valores padrão para criação
            **kwargs: Argumentos para busca
            
        Returns:
            tuple: (objeto, criado)
        """
        kwargs['tenant'] = tenant
        return self.get_or_create(defaults=defaults, **kwargs)

    def update_or_create_for_tenant(self, tenant, defaults=None, **kwargs):
        """
        Atualiza ou cria um objeto para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            defaults: Valores padrão para criação/atualização
            **kwargs: Argumentos para busca
            
        Returns:
            tuple: (objeto, criado)
        """
        kwargs['tenant'] = tenant
        return self.update_or_create(defaults=defaults, **kwargs)


class SharedModel(models.Model):
    """
    Modelo base abstrato para modelos compartilhados entre todos os tenants.
    
    Este modelo deve ser usado para dados que não são específicos de um tenant,
    como configurações globais, logs de sistema, etc.
    """
    
    class Meta:
        abstract = True
        # Marca o modelo como compartilhado para o database router
        shared = True

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que seja salvo no schema compartilhado.
        """
        # Para modelos compartilhados, sempre usa o database padrão
        kwargs.setdefault('using', 'default')
        super().save(*args, **kwargs)


class TenantSpecificModel(TenantAwareModel):
    """
    Modelo base para dados específicos de tenant com funcionalidades extras.
    
    Este modelo estende TenantAwareModel com funcionalidades adicionais
    como auditoria, soft delete, etc.
    """
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.CharField(max_length=255, blank=True, verbose_name="Criado por")
    updated_by = models.CharField(max_length=255, blank=True, verbose_name="Atualizado por")
    
    # Soft delete
    is_deleted = models.BooleanField(default=False, verbose_name="Deletado")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Deletado em")
    deleted_by = models.CharField(max_length=255, blank=True, verbose_name="Deletado por")
    
    # Manager que exclui registros deletados por padrão
    objects = TenantAwareManagerFromQuerySet()
    all_objects = models.Manager()  # Inclui registros deletados
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'is_deleted']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'updated_at']),
        ]

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para adicionar informações de auditoria.
        """
        # Adiciona informações do usuário atual se disponível
        from .utils import get_current_tenant
        
        current_tenant = get_current_tenant()
        if current_tenant and hasattr(current_tenant, 'current_user'):
            user_info = str(current_tenant.current_user)
            if not self.pk:  # Novo registro
                self.created_by = user_info
            self.updated_by = user_info
        
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, soft=True):
        """
        Sobrescreve o método delete para implementar soft delete.
        
        Args:
            using: Database a ser usado
            keep_parents: Manter registros pai
            soft: Se True, faz soft delete; se False, delete real
        """
        if soft:
            # Soft delete
            self.is_deleted = True
            self.deleted_at = models.functions.Now()
            
            # Adiciona informações do usuário atual se disponível
            current_tenant = get_current_tenant()
            if current_tenant and hasattr(current_tenant, 'current_user'):
                self.deleted_by = str(current_tenant.current_user)
            
            self.save(using=using)
        else:
            # Delete real
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restaura um registro que foi soft deleted.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = ''
        self.save()

    @classmethod
    def get_deleted_objects(cls, tenant=None):
        """
        Retorna objetos que foram soft deleted.
        
        Args:
            tenant: Tenant específico (opcional)
            
        Returns:
            QuerySet: QuerySet com objetos deletados
        """
        queryset = cls.all_objects.filter(is_deleted=True)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset

    def get_audit_trail(self):
        """
        Retorna informações de auditoria do objeto.
        
        Returns:
            dict: Informações de auditoria
        """
        return {
            'created_at': self.created_at,
            'created_by': self.created_by,
            'updated_at': self.updated_at,
            'updated_by': self.updated_by,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at,
            'deleted_by': self.deleted_by,
        }


def tenant_model_factory(model_name, fields=None, meta_options=None):
    """
    Factory function para criar modelos tenant-aware dinamicamente.
    
    Args:
        model_name: Nome do modelo
        fields: Dicionário com campos do modelo
        meta_options: Opções da classe Meta
        
    Returns:
        type: Classe do modelo criado
    """
    if fields is None:
        fields = {}
    
    if meta_options is None:
        meta_options = {}
    
    # Adiciona campos padrão
    fields.update({
        '__module__': __name__,
        'Meta': type('Meta', (), meta_options),
    })
    
    # Cria a classe do modelo
    return type(model_name, (TenantAwareModel,), fields)


def get_tenant_model_stats(tenant):
    """
    Obtém estatísticas de modelos para um tenant específico.
    
    Args:
        tenant: Instância do modelo Tenant
        
    Returns:
        dict: Estatísticas dos modelos
    """
    from django.apps import apps
    
    stats = {}
    
    # Itera sobre todos os modelos registrados
    for model in apps.get_models():
        # Verifica se o modelo é tenant-aware
        if (hasattr(model, 'tenant') and 
            hasattr(model, 'objects') and 
            hasattr(model.objects, 'for_tenant')):
            
            model_name = f"{model._meta.app_label}.{model._meta.model_name}"
            try:
                count = model.objects.for_tenant(tenant).count()
                stats[model_name] = count
            except Exception:
                stats[model_name] = 'error'
    
    return stats


def validate_tenant_data_integrity(tenant):
    """
    Valida a integridade dos dados de um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
        
    Returns:
        dict: Resultado da validação
    """
    from django.apps import apps
    
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'model_counts': {},
    }
    
    try:
        # Verifica cada modelo tenant-aware
        for model in apps.get_models():
            if (hasattr(model, 'tenant') and 
                hasattr(model, 'objects') and 
                hasattr(model.objects, 'for_tenant')):
                
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                
                try:
                    # Conta registros do tenant
                    count = model.objects.for_tenant(tenant).count()
                    result['model_counts'][model_name] = count
                    
                    # Verifica se há registros órfãos (sem tenant)
                    orphan_count = model.all_objects.filter(tenant__isnull=True).count()
                    if orphan_count > 0:
                        result['warnings'].append(
                            f"{model_name}: {orphan_count} registros órfãos encontrados"
                        )
                    
                    # Verifica se há registros de tenants inativos
                    inactive_count = model.all_objects.filter(
                        tenant__is_active=False
                    ).count()
                    if inactive_count > 0:
                        result['warnings'].append(
                            f"{model_name}: {inactive_count} registros de tenants inativos"
                        )
                        
                except Exception as e:
                    result['errors'].append(f"{model_name}: {str(e)}")
                    result['valid'] = False
    
    except Exception as e:
        result['errors'].append(f"Erro geral na validação: {str(e)}")
        result['valid'] = False
    
    return result
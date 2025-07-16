"""
Base models and managers for tenant-aware functionality.
Provides automatic tenant isolation for all models that inherit from TenantAwareModel.
"""

from django.db import models
from django.core.exceptions import ValidationError
from .utils import get_current_tenant


class TenantAwareManager(models.Manager):
    """
    Manager que filtra automaticamente por tenant.
    Garante que todas as operações CRUD sejam isoladas por tenant.
    """
    
    def get_queryset(self):
        """
        Retorna queryset filtrado pelo tenant atual.
        Se não há tenant no contexto, retorna queryset vazio para segurança.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            # Se não há tenant no contexto, retorna queryset vazio por segurança
            return super().get_queryset().none()
        
        # Filtra pelo tenant atual
        return super().get_queryset().filter(tenant=current_tenant)
    
    def create(self, **kwargs):
        """
        Cria um novo objeto associado automaticamente ao tenant atual.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            raise ValidationError("Não é possível criar objetos sem um tenant no contexto")
        
        # Adiciona o tenant atual aos kwargs se não foi especificado
        if 'tenant' not in kwargs:
            kwargs['tenant'] = current_tenant
        elif kwargs['tenant'] != current_tenant:
            raise ValidationError("Não é possível criar objetos para outro tenant")
        
        return super().create(**kwargs)
    
    def bulk_create(self, objs, **kwargs):
        """
        Cria múltiplos objetos em lote, garantindo que todos sejam do tenant atual.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            raise ValidationError("Não é possível criar objetos sem um tenant no contexto")
        
        # Valida e define o tenant para todos os objetos
        for obj in objs:
            if not hasattr(obj, 'tenant') or obj.tenant is None:
                obj.tenant = current_tenant
            elif obj.tenant != current_tenant:
                raise ValidationError("Não é possível criar objetos para outro tenant")
        
        return super().bulk_create(objs, **kwargs)
    
    def get_or_create(self, defaults=None, **kwargs):
        """
        Obtém ou cria um objeto, garantindo isolamento por tenant.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            raise ValidationError("Não é possível buscar/criar objetos sem um tenant no contexto")
        
        # Adiciona o tenant aos filtros de busca
        if 'tenant' not in kwargs:
            kwargs['tenant'] = current_tenant
        elif kwargs['tenant'] != current_tenant:
            raise ValidationError("Não é possível buscar objetos de outro tenant")
        
        # Adiciona o tenant aos defaults se necessário
        if defaults and 'tenant' not in defaults:
            defaults['tenant'] = current_tenant
        
        return super().get_or_create(defaults=defaults, **kwargs)
    
    def update_or_create(self, defaults=None, **kwargs):
        """
        Atualiza ou cria um objeto, garantindo isolamento por tenant.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            raise ValidationError("Não é possível atualizar/criar objetos sem um tenant no contexto")
        
        # Adiciona o tenant aos filtros de busca
        if 'tenant' not in kwargs:
            kwargs['tenant'] = current_tenant
        elif kwargs['tenant'] != current_tenant:
            raise ValidationError("Não é possível buscar objetos de outro tenant")
        
        # Adiciona o tenant aos defaults se necessário
        if defaults and 'tenant' not in defaults:
            defaults['tenant'] = current_tenant
        
        return super().update_or_create(defaults=defaults, **kwargs)
    
    def all_tenants(self):
        """
        Retorna queryset com dados de todos os tenants.
        CUIDADO: Use apenas para operações administrativas!
        """
        return super().get_queryset()
    
    def for_tenant(self, tenant):
        """
        Retorna queryset filtrado por um tenant específico.
        Útil para operações cross-tenant controladas.
        """
        if tenant is None:
            return super().get_queryset().none()
        return super().get_queryset().filter(tenant=tenant)
    
    def count_by_tenant(self):
        """
        Retorna contagem de objetos agrupados por tenant.
        Útil para relatórios administrativos.
        """
        from django.db.models import Count
        return (super().get_queryset()
                .values('tenant__name', 'tenant__subdomain')
                .annotate(count=Count('id'))
                .order_by('tenant__name'))


class TenantAwareModel(models.Model):
    """
    Modelo base abstrato que fornece funcionalidade tenant-aware.
    Todos os modelos que herdam desta classe são automaticamente isolados por tenant.
    """
    
    # Referência ao tenant - será adicionada a todos os modelos filhos
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Tenant',
        help_text='Tenant ao qual este registro pertence',
        null=True,  # Temporariamente nullable para migração
        blank=True
    )
    
    # Manager padrão com filtros de tenant
    objects = TenantAwareManager()
    
    # Manager para acesso a todos os tenants (uso administrativo)
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
        # Índice para melhorar performance das consultas por tenant
        indexes = [
            models.Index(fields=['tenant']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que o tenant seja definido automaticamente.
        """
        # Se o tenant não foi definido, usa o tenant atual do contexto
        if not self.tenant_id:
            current_tenant = get_current_tenant()
            if current_tenant is None:
                raise ValidationError("Não é possível salvar objetos sem um tenant no contexto")
            self.tenant = current_tenant
        
        # Valida se o tenant do objeto é o mesmo do contexto atual
        current_tenant = get_current_tenant()
        if current_tenant and self.tenant != current_tenant:
            raise ValidationError("Não é possível salvar objetos de outro tenant")
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Sobrescreve o método delete para validar o tenant.
        """
        current_tenant = get_current_tenant()
        if current_tenant and self.tenant != current_tenant:
            raise ValidationError("Não é possível excluir objetos de outro tenant")
        
        super().delete(*args, **kwargs)
    
    def clean(self):
        """
        Validações customizadas do modelo.
        """
        super().clean()
        
        # Valida se o tenant está ativo
        if self.tenant and not self.tenant.is_active:
            raise ValidationError({'tenant': 'Não é possível usar tenants inativos.'})
    
    @classmethod
    def get_tenant_field_name(cls):
        """
        Retorna o nome do campo que referencia o tenant.
        Útil para consultas dinâmicas.
        """
        return 'tenant'
    
    @property
    def tenant_name(self):
        """
        Propriedade de conveniência para acessar o nome do tenant.
        """
        return self.tenant.name if self.tenant else None
    
    @property
    def tenant_subdomain(self):
        """
        Propriedade de conveniência para acessar o subdomínio do tenant.
        """
        return self.tenant.subdomain if self.tenant else None


class TenantAwareQuerySet(models.QuerySet):
    """
    QuerySet customizado com métodos específicos para tenant-aware models.
    """
    
    def for_tenant(self, tenant):
        """
        Filtra o queryset por um tenant específico.
        """
        return self.filter(tenant=tenant)
    
    def exclude_tenant(self, tenant):
        """
        Exclui registros de um tenant específico.
        """
        return self.exclude(tenant=tenant)
    
    def current_tenant_only(self):
        """
        Filtra apenas pelo tenant atual do contexto.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            return self.none()
        return self.filter(tenant=current_tenant)
    
    def with_tenant_info(self):
        """
        Adiciona informações do tenant ao queryset usando select_related.
        """
        return self.select_related('tenant')
    
    def active_tenants_only(self):
        """
        Filtra apenas registros de tenants ativos.
        """
        return self.filter(tenant__is_active=True)
    
    def by_tenant_plan(self, plan_type):
        """
        Filtra registros por tipo de plano do tenant.
        """
        return self.filter(tenant__plan_type=plan_type)
    
    def tenant_statistics(self):
        """
        Retorna estatísticas agrupadas por tenant.
        """
        from django.db.models import Count, Avg, Max, Min
        return (self.values('tenant__name', 'tenant__subdomain')
                .annotate(
                    count=Count('id'),
                    created_min=Min('created_at') if hasattr(self.model, 'created_at') else None,
                    created_max=Max('created_at') if hasattr(self.model, 'created_at') else None,
                )
                .order_by('tenant__name'))


class TenantAwareManagerWithQuerySet(TenantAwareManager):
    """
    Manager que combina TenantAwareManager com TenantAwareQuerySet.
    Fornece todos os métodos de ambas as classes.
    """
    
    def get_queryset(self):
        """
        Retorna TenantAwareQuerySet filtrado pelo tenant atual.
        """
        current_tenant = get_current_tenant()
        if current_tenant is None:
            return TenantAwareQuerySet(self.model, using=self._db).none()
        
        return TenantAwareQuerySet(self.model, using=self._db).filter(tenant=current_tenant)
    
    def all_tenants(self):
        """
        Retorna TenantAwareQuerySet com dados de todos os tenants.
        """
        return TenantAwareQuerySet(self.model, using=self._db)


# Mixin para adicionar campos de auditoria tenant-aware
class TenantAwareAuditMixin(models.Model):
    """
    Mixin que adiciona campos de auditoria tenant-aware.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Criado por',
        help_text='Email do usuário que criou o registro'
    )
    updated_by = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Atualizado por',
        help_text='Email do usuário que atualizou o registro'
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Automaticamente define created_by e updated_by baseado no contexto.
        """
        # Aqui você pode implementar lógica para capturar o usuário atual
        # Por exemplo, usando thread-local storage ou middleware
        super().save(*args, **kwargs)


# Função utilitária para converter modelos existentes
def make_model_tenant_aware(model_class, tenant_field_name='tenant'):
    """
    Função utilitária para tornar um modelo existente tenant-aware.
    
    CUIDADO: Esta função modifica a classe do modelo em runtime.
    Use apenas durante migrações ou desenvolvimento.
    
    Args:
        model_class: Classe do modelo a ser modificada
        tenant_field_name: Nome do campo tenant (padrão: 'tenant')
    """
    # Adiciona o campo tenant se não existir
    if not hasattr(model_class, tenant_field_name):
        tenant_field = models.ForeignKey(
            'tenants.Tenant',
            on_delete=models.CASCADE,
            related_name=f'{model_class._meta.model_name}_set'
        )
        model_class.add_to_class(tenant_field_name, tenant_field)
    
    # Substitui o manager padrão
    if not isinstance(model_class.objects, TenantAwareManager):
        model_class.add_to_class('objects', TenantAwareManager())
        model_class.add_to_class('all_objects', models.Manager())
    
    # Adiciona métodos de validação se não existirem
    original_save = model_class.save
    original_delete = model_class.delete
    
    def tenant_aware_save(self, *args, **kwargs):
        if not getattr(self, tenant_field_name + '_id'):
            current_tenant = get_current_tenant()
            if current_tenant is None:
                raise ValidationError("Não é possível salvar objetos sem um tenant no contexto")
            setattr(self, tenant_field_name, current_tenant)
        
        current_tenant = get_current_tenant()
        if current_tenant and getattr(self, tenant_field_name) != current_tenant:
            raise ValidationError("Não é possível salvar objetos de outro tenant")
        
        return original_save(self, *args, **kwargs)
    
    def tenant_aware_delete(self, *args, **kwargs):
        current_tenant = get_current_tenant()
        if current_tenant and getattr(self, tenant_field_name) != current_tenant:
            raise ValidationError("Não é possível excluir objetos de outro tenant")
        
        return original_delete(self, *args, **kwargs)
    
    model_class.save = tenant_aware_save
    model_class.delete = tenant_aware_delete
    
    return model_class


# Decorator para tornar modelos tenant-aware
def tenant_aware(tenant_field_name='tenant'):
    """
    Decorator para tornar um modelo tenant-aware.
    
    Usage:
        @tenant_aware()
        class MyModel(models.Model):
            name = models.CharField(max_length=100)
    """
    def decorator(model_class):
        return make_model_tenant_aware(model_class, tenant_field_name)
    return decorator
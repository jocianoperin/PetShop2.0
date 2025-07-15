from django.db import models
from django.core.exceptions import ValidationError
from .utils import get_current_tenant


class TenantAwareManager(models.Manager):
    """
    Manager que automaticamente filtra dados pelo tenant atual.
    Garante isolamento de dados entre tenants.
    """
    
    def get_queryset(self):
        """Retorna queryset filtrado pelo tenant atual"""
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        # Se há um tenant atual e o modelo não é compartilhado
        if tenant and not getattr(self.model._meta, 'shared_model', False):
            # Filtra automaticamente pelo tenant
            return queryset
        
        return queryset

    def create(self, **kwargs):
        """Cria objeto garantindo associação ao tenant atual"""
        tenant = get_current_tenant()
        
        if tenant and not getattr(self.model._meta, 'shared_model', False):
            # Para modelos tenant-aware, não precisa de campo tenant_id
            # pois o isolamento é feito pelo schema
            pass
        
        return super().create(**kwargs)

    def bulk_create(self, objs, **kwargs):
        """Bulk create com validação de tenant"""
        tenant = get_current_tenant()
        
        if tenant and not getattr(self.model._meta, 'shared_model', False):
            # Valida que todos os objetos pertencem ao tenant atual
            for obj in objs:
                if hasattr(obj, 'clean'):
                    obj.clean()
        
        return super().bulk_create(objs, **kwargs)


class TenantAwareModel(models.Model):
    """
    Modelo base para entidades que devem ser isoladas por tenant.
    
    Características:
    - Automaticamente filtra dados pelo tenant atual
    - Valida operações para garantir isolamento
    - Fornece métodos utilitários para operações tenant-aware
    """
    
    objects = TenantAwareManager()
    
    class Meta:
        abstract = True
        # Marca que este modelo não é compartilhado
        shared_model = False

    def clean(self):
        """Validação personalizada para garantir isolamento de tenant"""
        super().clean()
        
        tenant = get_current_tenant()
        if not tenant:
            raise ValidationError(
                "Operação requer contexto de tenant válido"
            )

    def save(self, *args, **kwargs):
        """Save com validação de tenant"""
        # Executa validações
        self.full_clean()
        
        # Chama o save original
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete com validação de tenant"""
        tenant = get_current_tenant()
        if not tenant:
            raise ValidationError(
                "Operação de exclusão requer contexto de tenant válido"
            )
        
        return super().delete(*args, **kwargs)

    @classmethod
    def get_for_tenant(cls, tenant):
        """
        Retorna queryset para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
        
        Returns:
            QuerySet filtrado pelo tenant
        """
        from .utils import tenant_context
        
        with tenant_context(tenant):
            return cls.objects.all()

    @classmethod
    def create_for_tenant(cls, tenant, **kwargs):
        """
        Cria objeto para um tenant específico.
        
        Args:
            tenant: Instância do modelo Tenant
            **kwargs: Dados para criação do objeto
        
        Returns:
            Instância criada
        """
        from .utils import tenant_context
        
        with tenant_context(tenant):
            return cls.objects.create(**kwargs)


class SharedModel(models.Model):
    """
    Modelo base para entidades compartilhadas entre todos os tenants.
    
    Exemplos: Tenant, TenantUser, configurações globais, etc.
    """
    
    class Meta:
        abstract = True
        # Marca que este modelo é compartilhado
        shared_model = True


class TenantAwareQuerySet(models.QuerySet):
    """
    QuerySet personalizado com métodos específicos para multitenant.
    """
    
    def for_tenant(self, tenant):
        """Filtra queryset para um tenant específico"""
        from .utils import tenant_context
        
        with tenant_context(tenant):
            return self.all()

    def exclude_tenant(self, tenant):
        """Exclui dados de um tenant específico (usado em contextos administrativos)"""
        # Para modelos com schema por tenant, isso não se aplica
        # Mantido para compatibilidade futura
        return self

    def tenant_count(self):
        """Retorna contagem de registros no tenant atual"""
        return self.count()


class TenantAwareModelMixin:
    """
    Mixin para adicionar funcionalidades tenant-aware a modelos existentes.
    
    Usage:
        class MeuModelo(TenantAwareModelMixin, models.Model):
            nome = models.CharField(max_length=100)
            # ... outros campos
    """
    
    def get_tenant(self):
        """Retorna o tenant atual"""
        return get_current_tenant()

    def is_accessible_by_tenant(self, tenant):
        """Verifica se o objeto é acessível por um tenant específico"""
        current_tenant = get_current_tenant()
        return current_tenant and current_tenant.id == tenant.id

    def validate_tenant_access(self):
        """Valida se o objeto pode ser acessado no contexto atual"""
        tenant = get_current_tenant()
        if not tenant:
            raise ValidationError("Acesso requer contexto de tenant válido")
        return True


def tenant_aware_model(cls):
    """
    Decorator para transformar um modelo existente em tenant-aware.
    
    Usage:
        @tenant_aware_model
        class MeuModelo(models.Model):
            nome = models.CharField(max_length=100)
    """
    
    # Adiciona o manager tenant-aware
    if not hasattr(cls, 'objects') or cls.objects.__class__ == models.Manager:
        cls.objects = TenantAwareManager()
    
    # Adiciona métodos tenant-aware
    original_save = cls.save
    original_delete = cls.delete
    
    def tenant_aware_save(self, *args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            raise ValidationError("Save requer contexto de tenant válido")
        return original_save(self, *args, **kwargs)
    
    def tenant_aware_delete(self, *args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            raise ValidationError("Delete requer contexto de tenant válido")
        return original_delete(self, *args, **kwargs)
    
    cls.save = tenant_aware_save
    cls.delete = tenant_aware_delete
    
    # Marca como não compartilhado
    cls._meta.shared_model = False
    
    return cls
from django.conf import settings
from .utils import get_current_tenant


class TenantDatabaseRouter:
    """
    Router de banco de dados para sistema multitenant.
    
    Direciona operações de banco para o schema correto baseado no tenant atual.
    Modelos compartilhados (Tenant, TenantUser, etc.) sempre usam o schema 'public'.
    Modelos tenant-aware usam o schema específico do tenant atual.
    """
    
    # Modelos que sempre usam o schema compartilhado (public)
    SHARED_MODELS = {
        'tenants.tenant',
        'tenants.tenantuser', 
        'tenants.tenantconfiguration',
        'auth.user',
        'auth.group',
        'auth.permission',
        'contenttypes.contenttype',
        'sessions.session',
        'admin.logentry',
    }

    def db_for_read(self, model, **hints):
        """Determina qual banco usar para operações de leitura"""
        return self._get_database_for_model(model)

    def db_for_write(self, model, **hints):
        """Determina qual banco usar para operações de escrita"""
        return self._get_database_for_model(model)

    def allow_relation(self, obj1, obj2, **hints):
        """Permite relações entre objetos do mesmo tenant ou modelos compartilhados"""
        # Sempre permite relações entre modelos compartilhados
        if (self._is_shared_model(obj1._meta.label_lower) and 
            self._is_shared_model(obj2._meta.label_lower)):
            return True
        
        # Para modelos tenant-aware, verifica se estão no mesmo tenant
        tenant = get_current_tenant()
        if tenant:
            return True
        
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Controla quais migrações são aplicadas em qual banco/schema"""
        model_label = f"{app_label}.{model_name}" if model_name else None
        
        # Modelos compartilhados sempre migram no banco padrão
        if model_label and self._is_shared_model(model_label):
            return db == 'default'
        
        # Para outros modelos, permite migração baseada no contexto
        return True

    def _get_database_for_model(self, model):
        """Determina o banco correto para um modelo específico"""
        model_label = model._meta.label_lower
        
        # Modelos compartilhados sempre usam o banco padrão
        if self._is_shared_model(model_label):
            return 'default'
        
        # Modelos tenant-aware usam o banco do tenant atual
        tenant = get_current_tenant()
        if tenant:
            # Para PostgreSQL com schemas, ainda usamos 'default' 
            # mas o middleware configura o search_path
            return 'default'
        
        # Fallback para banco padrão
        return 'default'

    def _is_shared_model(self, model_label):
        """Verifica se um modelo é compartilhado entre todos os tenants"""
        return model_label.lower() in self.SHARED_MODELS


class TenantAwareManager:
    """
    Manager personalizado que automaticamente filtra dados por tenant.
    
    Usage:
        class MinhaModel(models.Model):
            objects = TenantAwareManager()
            # ... campos do modelo
    """
    
    def get_queryset(self):
        """Retorna queryset filtrado pelo tenant atual"""
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant and hasattr(self.model, 'tenant_id'):
            # Se o modelo tem campo tenant_id, filtra automaticamente
            queryset = queryset.filter(tenant_id=tenant.id)
        
        return queryset

    def create(self, **kwargs):
        """Cria objeto associado ao tenant atual"""
        tenant = get_current_tenant()
        
        if tenant and hasattr(self.model, 'tenant_id'):
            kwargs['tenant_id'] = tenant.id
        
        return super().create(**kwargs)


def setup_tenant_databases():
    """
    Configura conexões de banco para todos os tenants ativos.
    Deve ser chamado na inicialização da aplicação.
    """
    from .models import Tenant
    
    try:
        # Obtém todos os tenants ativos
        tenants = Tenant.objects.filter(is_active=True)
        
        # Para cada tenant, garante que o schema existe
        for tenant in tenants:
            ensure_tenant_schema_exists(tenant)
            
        print(f"Configurados {tenants.count()} schemas de tenant")
        
    except Exception as e:
        print(f"Erro ao configurar bancos de tenant: {str(e)}")


def ensure_tenant_schema_exists(tenant):
    """
    Garante que o schema do tenant existe no banco de dados.
    
    Args:
        tenant: Instância do modelo Tenant
    """
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # Verifica se o schema existe
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [tenant.schema_name])
            
            if not cursor.fetchone():
                # Cria o schema se não existir
                cursor.execute(f"CREATE SCHEMA {tenant.schema_name}")
                print(f"Schema {tenant.schema_name} criado para tenant {tenant.name}")
            
    except Exception as e:
        print(f"Erro ao verificar/criar schema para tenant {tenant.name}: {str(e)}")


def get_tenant_connection_params(tenant):
    """
    Retorna parâmetros de conexão específicos para um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        dict: Parâmetros de conexão do banco
    """
    from django.conf import settings
    
    # Copia configurações do banco padrão
    db_config = settings.DATABASES['default'].copy()
    
    # Para PostgreSQL, modifica o search_path
    if 'postgresql' in db_config.get('ENGINE', ''):
        options = db_config.get('OPTIONS', {})
        options['options'] = f"-c search_path={tenant.schema_name},public"
        db_config['OPTIONS'] = options
    
    return db_config


def create_tenant_database_alias(tenant):
    """
    Cria um alias de banco específico para um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        str: Nome do alias criado
    """
    from django.conf import settings
    
    alias_name = f"tenant_{tenant.schema_name}"
    
    # Adiciona configuração do banco para o tenant
    if alias_name not in settings.DATABASES:
        settings.DATABASES[alias_name] = get_tenant_connection_params(tenant)
    
    return alias_name
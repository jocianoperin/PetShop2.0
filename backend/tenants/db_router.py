"""
Database router para sistema multitenant.

Este router implementa a lógica de roteamento automático de queries
para o schema correto baseado no tenant atual. Suporta tanto SQLite
(desenvolvimento) quanto PostgreSQL (produção).
"""

from django.conf import settings
from django.db import connection, models
from .utils import get_current_tenant, _is_postgresql


class TenantDatabaseRouter:
    """
    Router de banco de dados para sistema multitenant.
    
    Implementa roteamento automático baseado no tenant atual:
    - Para PostgreSQL: usa schemas separados por tenant
    - Para SQLite: usa prefixos de tabela (simulação de schemas)
    
    O router intercepta todas as operações de banco e direciona
    para o schema/database correto baseado no contexto atual.
    """

    def db_for_read(self, model, **hints):
        """
        Determina qual database usar para operações de leitura.
        
        Args:
            model: Modelo Django sendo consultado
            **hints: Dicas adicionais sobre a operação
            
        Returns:
            str: Nome do database a ser usado ou None para usar o padrão
        """
        # Modelos do sistema compartilhado sempre usam 'default'
        if self._is_shared_model(model):
            return 'default'
        
        # Modelos tenant-aware usam o database do tenant atual
        tenant = get_current_tenant()
        if tenant:
            return self._get_tenant_database_alias(tenant)
        
        # Se não há tenant no contexto, usa o database padrão
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Determina qual database usar para operações de escrita.
        
        Args:
            model: Modelo Django sendo modificado
            **hints: Dicas adicionais sobre a operação
            
        Returns:
            str: Nome do database a ser usado ou None para usar o padrão
        """
        # Mesma lógica que db_for_read
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        """
        Determina se uma relação entre dois objetos é permitida.
        
        Args:
            obj1: Primeiro objeto da relação
            obj2: Segundo objeto da relação
            **hints: Dicas adicionais sobre a relação
            
        Returns:
            bool: True se a relação é permitida, False caso contrário, None para padrão
        """
        # Permite relações entre modelos do mesmo tenant
        db_set = {'default'}
        
        # Adiciona o database do tenant atual se existir
        tenant = get_current_tenant()
        if tenant:
            db_set.add(self._get_tenant_database_alias(tenant))
        
        # Verifica se ambos os objetos estão no mesmo conjunto de databases
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        
        # Permite relações entre modelos compartilhados
        if (self._is_shared_model(obj1.__class__) and 
            self._is_shared_model(obj2.__class__)):
            return True
        
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determina se uma migração deve ser aplicada em um database específico.
        
        Args:
            db: Nome do database
            app_label: Label da aplicação
            model_name: Nome do modelo (opcional)
            **hints: Dicas adicionais sobre a migração
            
        Returns:
            bool: True se a migração deve ser aplicada, False caso contrário, None para padrão
        """
        # Migrações do app 'tenants' sempre no database padrão
        if app_label == 'tenants':
            return db == 'default'
        
        # Migrações de apps do Django sempre no database padrão
        if app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
            return db == 'default'
        
        # Para outros apps, permite migração em qualquer database
        # (necessário para criar tabelas nos schemas dos tenants)
        return True

    def _is_shared_model(self, model):
        """
        Verifica se um modelo pertence ao schema compartilhado.
        
        Args:
            model: Classe do modelo Django
            
        Returns:
            bool: True se o modelo é compartilhado, False caso contrário
        """
        # Modelos do app 'tenants' são sempre compartilhados
        if hasattr(model, '_meta') and model._meta.app_label == 'tenants':
            return True
        
        # Modelos do Django são sempre compartilhados
        django_apps = ['auth', 'contenttypes', 'sessions', 'admin']
        if hasattr(model, '_meta') and model._meta.app_label in django_apps:
            return True
        
        # Verifica se o modelo tem a meta option 'shared'
        if hasattr(model, '_meta') and hasattr(model._meta, 'shared'):
            return model._meta.shared
        
        return False

    def _get_tenant_database_alias(self, tenant):
        """
        Obtém o alias do database para um tenant específico.
        
        Para PostgreSQL: usa o database padrão com schema diferente
        Para SQLite: poderia usar databases separados, mas usamos o padrão
        
        Args:
            tenant: Instância do modelo Tenant
            
        Returns:
            str: Alias do database
        """
        # Por enquanto, sempre usa 'default' pois o roteamento é feito via schema
        # Em implementações mais avançadas, poderia usar databases separados
        return 'default'


class TenantSchemaRouter:
    """
    Router especializado para gerenciamento de schemas PostgreSQL.
    
    Este router complementa o TenantDatabaseRouter fornecendo
    funcionalidades específicas para PostgreSQL schemas.
    """

    def __init__(self):
        self.current_schema = None

    def set_schema(self, schema_name):
        """
        Define o schema atual para as próximas operações.
        
        Args:
            schema_name: Nome do schema a ser usado
        """
        if not _is_postgresql():
            return
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name}, public")
                self.current_schema = schema_name
        except Exception as e:
            import logging
            logger = logging.getLogger('tenants')
            logger.error(f"Erro ao definir schema {schema_name}: {str(e)}")

    def get_current_schema(self):
        """
        Obtém o schema atualmente ativo.
        
        Returns:
            str: Nome do schema atual ou None
        """
        if not _is_postgresql():
            return None
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_schema()")
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None

    def ensure_tenant_schema(self, tenant):
        """
        Garante que o schema do tenant está ativo.
        
        Args:
            tenant: Instância do modelo Tenant
        """
        if not tenant or not _is_postgresql():
            return
        
        current_schema = self.get_current_schema()
        if current_schema != tenant.schema_name:
            self.set_schema(tenant.schema_name)

    def reset_to_public(self):
        """
        Reseta o schema para 'public' (padrão).
        """
        if _is_postgresql():
            self.set_schema('public')


# Instância global do router de schema
schema_router = TenantSchemaRouter()


class TenantAwareQuerySet:
    """
    Mixin para QuerySets que devem ser automaticamente filtrados por tenant.
    
    Este mixin pode ser usado em managers customizados para garantir
    que todas as queries sejam automaticamente filtradas pelo tenant atual.
    """

    def get_queryset(self):
        """
        Retorna o QuerySet base filtrado pelo tenant atual.
        
        Returns:
            QuerySet: QuerySet filtrado pelo tenant
        """
        queryset = super().get_queryset()
        
        # Aplica filtro de tenant se o modelo suportar
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            queryset = queryset.filter(tenant=tenant)
        
        return queryset


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


def get_tenant_database_settings(tenant):
    """
    Obtém as configurações de database para um tenant específico.
    
    Args:
        tenant: Instância do modelo Tenant
        
    Returns:
        dict: Configurações de database para o tenant
    """
    base_settings = settings.DATABASES['default'].copy()
    
    if _is_postgresql():
        # Para PostgreSQL, modifica o search_path
        options = base_settings.get('OPTIONS', {})
        options['options'] = f'-c search_path={tenant.schema_name},public'
        base_settings['OPTIONS'] = options
    else:
        # Para SQLite, poderia usar databases separados
        # Por enquanto, usa o mesmo database com prefixos de tabela
        pass
    
    return base_settings


def create_tenant_database_connection(tenant):
    """
    Cria uma conexão de database específica para um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
        
    Returns:
        DatabaseWrapper: Conexão de database configurada para o tenant
    """
    from django.db import connections
    from django.db.utils import ConnectionHandler
    
    # Obtém as configurações do tenant
    tenant_settings = get_tenant_database_settings(tenant)
    
    # Cria um alias único para o tenant
    tenant_alias = f"tenant_{tenant.schema_name}"
    
    # Adiciona a configuração ao handler de conexões
    if tenant_alias not in connections.databases:
        connections.databases[tenant_alias] = tenant_settings
    
    return connections[tenant_alias]


def execute_tenant_query(tenant, query, params=None):
    """
    Executa uma query SQL no contexto de um tenant específico.
    
    Args:
        tenant: Instância do modelo Tenant
        query: Query SQL a ser executada
        params: Parâmetros da query (opcional)
        
    Returns:
        Resultado da query
    """
    from .utils import tenant_context
    
    with tenant_context(tenant):
        with connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Retorna resultados para queries SELECT
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            
            return cursor.rowcount


def migrate_tenant_schema(tenant, app_label=None):
    """
    Executa migrações no schema de um tenant específico.
    
    Args:
        tenant: Instância do modelo Tenant
        app_label: Label da aplicação (opcional, migra todas se não especificado)
        
    Returns:
        bool: True se as migrações foram executadas com sucesso
    """
    from django.core.management import call_command
    from django.db import transaction
    from .utils import tenant_context
    
    try:
        with tenant_context(tenant):
            with transaction.atomic():
                if app_label:
                    call_command('migrate', app_label, verbosity=0, interactive=False)
                else:
                    call_command('migrate', verbosity=0, interactive=False)
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger('tenants')
        logger.error(f"Erro ao migrar schema do tenant {tenant.name}: {str(e)}")
        return False


def validate_tenant_schema(tenant):
    """
    Valida se o schema de um tenant está corretamente configurado.
    
    Args:
        tenant: Instância do modelo Tenant
        
    Returns:
        dict: Resultado da validação com status e detalhes
    """
    from .utils import tenant_context, list_tenant_tables
    
    result = {
        'valid': False,
        'schema_exists': False,
        'tables_count': 0,
        'missing_tables': [],
        'errors': []
    }
    
    try:
        # Verifica se o schema existe (PostgreSQL)
        if _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schema_name FROM information_schema.schemata 
                    WHERE schema_name = %s
                """, [tenant.schema_name])
                result['schema_exists'] = bool(cursor.fetchone())
        else:
            # Para SQLite, assume que o schema existe
            result['schema_exists'] = True
        
        if result['schema_exists']:
            # Lista tabelas no schema do tenant
            with tenant_context(tenant):
                tables = list_tenant_tables(tenant)
                result['tables_count'] = len(tables)
                
                # Verifica se as tabelas essenciais existem
                expected_tables = [
                    'api_cliente', 'api_animal', 'api_servico',
                    'api_agendamento', 'api_produto', 'api_venda'
                ]
                
                for table in expected_tables:
                    if table not in tables:
                        result['missing_tables'].append(table)
                
                result['valid'] = len(result['missing_tables']) == 0
        
    except Exception as e:
        result['errors'].append(str(e))
    
    return result


class DatabaseRoutingMiddleware:
    """
    Middleware adicional para garantir roteamento correto de database.
    
    Este middleware trabalha em conjunto com o TenantMiddleware
    para garantir que todas as operações de banco sejam roteadas
    corretamente para o schema do tenant.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Garante que o schema correto está ativo antes do processamento
        tenant = getattr(request, 'tenant', None)
        if tenant:
            schema_router.ensure_tenant_schema(tenant)
        
        response = self.get_response(request)
        
        # Reseta para o schema público após o processamento
        if tenant:
            schema_router.reset_to_public()
        
        return response


def get_tenant_connection_info():
    """
    Obtém informações sobre as conexões de database dos tenants.
    
    Returns:
        dict: Informações sobre conexões ativas
    """
    from django.db import connections
    
    info = {
        'total_connections': len(connections.all()),
        'tenant_connections': [],
        'default_connection': {
            'engine': connection.settings_dict['ENGINE'],
            'name': connection.settings_dict['NAME'],
        }
    }
    
    # Lista conexões específicas de tenants
    for alias, conn in connections.all():
        if alias.startswith('tenant_'):
            info['tenant_connections'].append({
                'alias': alias,
                'engine': conn.settings_dict['ENGINE'],
                'schema': alias.replace('tenant_', ''),
            })
    
    return info


def cleanup_tenant_connections():
    """
    Limpa conexões de database não utilizadas de tenants.
    
    Esta função pode ser chamada periodicamente para liberar recursos.
    """
    from django.db import connections
    
    # Fecha conexões de tenants não utilizadas
    for alias in list(connections.databases.keys()):
        if alias.startswith('tenant_') and alias in connections._connections:
            conn = connections._connections[alias]
            if hasattr(conn, 'close'):
                conn.close()
            del connections._connections[alias]


# Configurações padrão para o router
TENANT_DATABASE_ROUTER_SETTINGS = {
    'AUTO_ROUTE_TENANT_MODELS': True,
    'SHARED_APPS': ['tenants', 'auth', 'contenttypes', 'sessions', 'admin'],
    'TENANT_APPS': ['api'],
    'CACHE_TENANT_CONNECTIONS': True,
    'MAX_TENANT_CONNECTIONS': 100,
    'CONNECTION_TIMEOUT': 300,  # 5 minutos
}
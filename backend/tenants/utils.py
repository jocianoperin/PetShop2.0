import threading
from contextlib import contextmanager
from django.db import connection
from functools import wraps


# Thread-local storage para o tenant atual
_thread_local = threading.local()


def get_current_tenant():
    """Obtém o tenant atual do contexto da thread"""
    return getattr(_thread_local, 'current_tenant', None)


def set_current_tenant(tenant):
    """Define o tenant atual no contexto da thread"""
    _thread_local.current_tenant = tenant


def _is_postgresql():
    """Verifica se o banco de dados atual é PostgreSQL"""
    return 'postgresql' in connection.settings_dict['ENGINE']


@contextmanager
def tenant_context(tenant):
    """
    Context manager para executar operações em um tenant específico.
    
    Usage:
        with tenant_context(tenant):
            # Todas as operações de banco serão executadas no schema do tenant
            clientes = Cliente.objects.all()
    """
    old_tenant = get_current_tenant()
    set_current_tenant(tenant)
    
    # Configura o schema do banco (apenas para PostgreSQL)
    if tenant and _is_postgresql():
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
    
    try:
        yield tenant
    finally:
        # Restaura o tenant anterior
        set_current_tenant(old_tenant)
        if old_tenant and _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {old_tenant.schema_name}, public")
        elif _is_postgresql():
            # Volta para o schema padrão
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")


def tenant_required(view_func):
    """
    Decorator para views que requerem um tenant válido.
    
    Usage:
        @tenant_required
        def my_view(request):
            tenant = get_current_tenant()
            # ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Tenant requerido para esta operação',
                'code': 'TENANT_REQUIRED'
            }, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_admin_required(view_func):
    """
    Decorator para views que requerem um tenant válido e usuário admin.
    
    Usage:
        @tenant_admin_required
        def admin_view(request):
            tenant = get_current_tenant()
            # Usuário já é admin do tenant
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Tenant requerido para esta operação',
                'code': 'TENANT_REQUIRED'
            }, status=400)
        
        # Verifica se o usuário é admin do tenant
        if hasattr(request, 'user') and request.user.is_authenticated:
            from .models import TenantUser
            try:
                tenant_user = TenantUser.objects.get(
                    tenant=tenant,
                    email=request.user.email,
                    is_active=True
                )
                if tenant_user.role not in ['admin', 'manager']:
                    return JsonResponse({
                        'error': 'Permissões de administrador requeridas',
                        'code': 'ADMIN_REQUIRED'
                    }, status=403)
            except TenantUser.DoesNotExist:
                return JsonResponse({
                    'error': 'Usuário não encontrado no tenant',
                    'code': 'USER_NOT_IN_TENANT'
                }, status=403)
        else:
            return JsonResponse({
                'error': 'Autenticação requerida',
                'code': 'AUTHENTICATION_REQUIRED'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def with_tenant_context(tenant_id_or_subdomain):
    """
    Decorator para executar uma view em um contexto de tenant específico.
    
    Usage:
        @with_tenant_context('tenant-subdomain')
        def cross_tenant_view(request):
            # Executa no contexto do tenant especificado
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from .models import Tenant
            
            # Resolve o tenant
            try:
                if len(str(tenant_id_or_subdomain)) == 36:  # UUID
                    tenant = Tenant.objects.get(id=tenant_id_or_subdomain, is_active=True)
                else:  # Subdomain
                    tenant = Tenant.objects.get(subdomain=tenant_id_or_subdomain, is_active=True)
            except Tenant.DoesNotExist:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Tenant especificado não encontrado',
                    'code': 'TENANT_NOT_FOUND'
                }, status=404)
            
            # Executa no contexto do tenant
            with tenant_context(tenant):
                return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_tenant_schema_name(tenant_id=None):
    """
    Obtém o nome do schema para um tenant específico ou atual.
    
    Args:
        tenant_id: ID do tenant (opcional, usa o atual se não fornecido)
    
    Returns:
        str: Nome do schema do tenant
    """
    if tenant_id:
        from .models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            return tenant.schema_name
        except Tenant.DoesNotExist:
            return None
    
    tenant = get_current_tenant()
    return tenant.schema_name if tenant else None


def execute_in_tenant_schema(tenant, sql, params=None):
    """
    Executa SQL diretamente no schema de um tenant específico.
    
    Args:
        tenant: Instância do modelo Tenant
        sql: Query SQL para executar
        params: Parâmetros para a query (opcional)
    
    Returns:
        Resultado da query
    """
    with connection.cursor() as cursor:
        # Define o schema (apenas para PostgreSQL)
        if _is_postgresql():
            cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
        
        # Executa a query
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Retorna resultados se for uma query SELECT
        if sql.strip().upper().startswith('SELECT'):
            return cursor.fetchall()
        
        return cursor.rowcount


def create_tenant_schema(tenant):
    """
    Cria o schema no banco de dados para um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        bool: True se criado com sucesso, False caso contrário
    """
    # Para SQLite, não há schemas reais, então retorna True
    if not _is_postgresql():
        print(f"SQLite em uso - schema lógico criado para tenant {tenant.name}")
        return True
    
    try:
        with connection.cursor() as cursor:
            # Cria o schema
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant.schema_name}")
            
            # Define permissões básicas
            cursor.execute(f"GRANT USAGE ON SCHEMA {tenant.schema_name} TO current_user")
            cursor.execute(f"GRANT CREATE ON SCHEMA {tenant.schema_name} TO current_user")
            
        return True
    except Exception as e:
        print(f"Erro ao criar schema para tenant {tenant.name}: {str(e)}")
        return False


def drop_tenant_schema(tenant):
    """
    Remove o schema do banco de dados para um tenant.
    CUIDADO: Esta operação é irreversível!
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        bool: True se removido com sucesso, False caso contrário
    """
    # Para SQLite, não há schemas reais
    if not _is_postgresql():
        print(f"SQLite em uso - schema lógico removido para tenant {tenant.name}")
        return True
    
    try:
        with connection.cursor() as cursor:
            # Remove o schema e todo seu conteúdo
            cursor.execute(f"DROP SCHEMA IF EXISTS {tenant.schema_name} CASCADE")
        return True
    except Exception as e:
        print(f"Erro ao remover schema para tenant {tenant.name}: {str(e)}")
        return False


def list_tenant_tables(tenant):
    """
    Lista todas as tabelas no schema de um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        list: Lista de nomes das tabelas
    """
    try:
        with connection.cursor() as cursor:
            if _is_postgresql():
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, [tenant.schema_name])
            else:
                # Para SQLite, lista todas as tabelas (não há schemas)
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
            
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Erro ao listar tabelas do tenant {tenant.name}: {str(e)}")
        return []


def get_tenant_database_size(tenant):
    """
    Obtém o tamanho do banco de dados de um tenant.
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        int: Tamanho em bytes, ou None se erro
    """
    try:
        with connection.cursor() as cursor:
            if _is_postgresql():
                cursor.execute("""
                    SELECT pg_total_relation_size(schemaname||'.'||tablename) as size
                    FROM pg_tables 
                    WHERE schemaname = %s
                """, [tenant.schema_name])
                
                total_size = sum(row[0] or 0 for row in cursor.fetchall())
                return total_size
            else:
                # Para SQLite, retorna o tamanho do arquivo de banco
                import os
                db_path = connection.settings_dict['NAME']
                if os.path.exists(db_path):
                    return os.path.getsize(db_path)
                return 0
    except Exception as e:
        print(f"Erro ao obter tamanho do banco do tenant {tenant.name}: {str(e)}")
        return None


class TenantContextManager:
    """
    Classe para gerenciar contexto de tenant de forma mais avançada.
    Permite operações em lote e controle fino do contexto.
    """
    
    def __init__(self):
        self._context_stack = []
    
    def push_tenant(self, tenant):
        """Adiciona um tenant ao stack de contexto"""
        current_tenant = get_current_tenant()
        self._context_stack.append(current_tenant)
        set_current_tenant(tenant)
        
        # Configura o schema do banco (apenas para PostgreSQL)
        if tenant and _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
    
    def pop_tenant(self):
        """Remove o tenant atual do stack e restaura o anterior"""
        if self._context_stack:
            previous_tenant = self._context_stack.pop()
            set_current_tenant(previous_tenant)
            
            # Restaura o schema anterior
            if previous_tenant and _is_postgresql():
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {previous_tenant.schema_name}, public")
            elif _is_postgresql():
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public")
    
    def clear_context(self):
        """Limpa todo o contexto de tenant"""
        self._context_stack.clear()
        set_current_tenant(None)
        if _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")


# Instância global do gerenciador de contexto
_tenant_context_manager = TenantContextManager()


def push_tenant_context(tenant):
    """Adiciona um tenant ao contexto atual"""
    _tenant_context_manager.push_tenant(tenant)


def pop_tenant_context():
    """Remove o tenant atual do contexto"""
    _tenant_context_manager.pop_tenant()


def clear_tenant_context():
    """Limpa todo o contexto de tenant"""
    _tenant_context_manager.clear_context()


@contextmanager
def multi_tenant_context(*tenants):
    """
    Context manager para executar operações em múltiplos tenants sequencialmente.
    
    Usage:
        with multi_tenant_context(tenant1, tenant2, tenant3) as tenant_iterator:
            for tenant in tenant_iterator:
                # Operações executadas no contexto de cada tenant
                clientes = Cliente.objects.all()
    """
    original_tenant = get_current_tenant()
    
    def tenant_iterator():
        for tenant in tenants:
            with tenant_context(tenant):
                yield tenant
    
    try:
        yield tenant_iterator()
    finally:
        # Restaura o tenant original
        set_current_tenant(original_tenant)
        if original_tenant and _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {original_tenant.schema_name}, public")
        elif _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")


def get_tenant_from_request(request):
    """
    Extrai o tenant de um request Django.
    Útil para views que precisam acessar o tenant diretamente.
    
    Args:
        request: HttpRequest object
    
    Returns:
        Tenant: Instância do tenant ou None
    """
    return getattr(request, 'tenant', None)


def ensure_tenant_context(tenant):
    """
    Garante que um tenant específico está no contexto atual.
    Se não estiver, define o tenant no contexto.
    
    Args:
        tenant: Instância do modelo Tenant
    
    Returns:
        bool: True se o contexto foi alterado, False se já estava correto
    """
    current_tenant = get_current_tenant()
    if current_tenant != tenant:
        set_current_tenant(tenant)
        
        # Configura o schema do banco (apenas para PostgreSQL)
        if tenant and _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
        
        return True
    return False
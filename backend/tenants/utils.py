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
"""
Decorators para integração do sistema de monitoramento
com ViewSets e views existentes.
"""

from functools import wraps
from django.http import JsonResponse
from .monitoring import audit_logger, db_monitor
from .utils import get_current_tenant


def audit_action(action_type, resource_type=None):
    """
    Decorator para registrar ações de auditoria automaticamente
    
    Args:
        action_type: Tipo da ação (CREATE, UPDATE, DELETE, etc.)
        resource_type: Tipo do recurso sendo manipulado
    
    Usage:
        @audit_action('CREATE', 'cliente')
        def create_cliente(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            tenant = get_current_tenant()
            user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
            
            # Executa a view
            response = view_func(request, *args, **kwargs)
            
            # Registra auditoria apenas se a operação foi bem-sucedida
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                details = {
                    'resource_type': resource_type,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code
                }
                
                # Adiciona ID do recurso se disponível na resposta
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    if 'id' in response.data:
                        details['resource_id'] = response.data['id']
                
                audit_logger.log_action(action_type, user_id, details, tenant)
            
            return response
        return wrapper
    return decorator


def monitor_db_queries(view_func):
    """
    Decorator para monitorar queries de banco de dados
    
    Usage:
        @monitor_db_queries
        def my_view(request):
            # ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from django.db import connection
        from django.conf import settings
        
        # Só monitora se habilitado nas configurações
        if not getattr(settings, 'TENANT_MONITORING', {}).get('ENABLE_DB_MONITORING', True):
            return view_func(request, *args, **kwargs)
        
        # Captura queries antes da execução
        queries_before = len(connection.queries)
        
        # Executa a view
        response = view_func(request, *args, **kwargs)
        
        # Calcula queries executadas
        queries_after = len(connection.queries)
        queries_count = queries_after - queries_before
        
        # Registra no monitor se houver queries
        if queries_count > 0:
            tenant = get_current_tenant()
            if tenant:
                # Registra informações das queries
                recent_queries = connection.queries[queries_before:queries_after]
                for query in recent_queries:
                    db_monitor.log_query(
                        query['sql'],
                        None,  # params não disponíveis facilmente
                        float(query['time']),
                        str(tenant.id)
                    )
        
        return response
    return wrapper


def log_data_access(resource_type, action='READ'):
    """
    Decorator para registrar acesso a dados
    
    Args:
        resource_type: Tipo do recurso acessado
        action: Tipo de ação (READ, WRITE, DELETE)
    
    Usage:
        @log_data_access('cliente', 'READ')
        def list_clientes(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
            
            # Tenta extrair ID do recurso dos argumentos
            resource_id = kwargs.get('pk') or kwargs.get('id')
            
            # Registra o acesso
            audit_logger.log_data_access(user_id, resource_type, resource_id, action)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_tenant(view_func):
    """
    Decorator que garante que um tenant válido está presente
    
    Usage:
        @require_tenant
        def my_view(request):
            # tenant garantidamente disponível
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            return JsonResponse({
                'error': 'Tenant requerido para esta operação',
                'code': 'TENANT_REQUIRED'
            }, status=400)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def monitor_performance(threshold_seconds=5.0):
    """
    Decorator para monitorar performance de views
    
    Args:
        threshold_seconds: Limite de tempo para alertas
    
    Usage:
        @monitor_performance(2.0)
        def slow_view(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            import time
            import logging
            
            start_time = time.time()
            
            # Executa a view
            response = view_func(request, *args, **kwargs)
            
            # Calcula tempo de execução
            execution_time = time.time() - start_time
            
            # Log de performance se exceder o limite
            if execution_time > threshold_seconds:
                tenant = get_current_tenant()
                logger = logging.getLogger('tenants.monitoring')
                
                logger.warning(
                    f"Slow view detected: {view_func.__name__} took {execution_time:.3f}s",
                    extra={
                        'tenant_id': str(tenant.id) if tenant else None,
                        'tenant_name': tenant.name if tenant else None,
                        'view_name': view_func.__name__,
                        'execution_time': execution_time,
                        'threshold': threshold_seconds,
                        'path': request.path,
                        'method': request.method
                    }
                )
            
            return response
        return wrapper
    return decorator


class AuditViewSetMixin:
    """
    Mixin para ViewSets que adiciona auditoria automática
    """
    
    audit_resource_type = None  # Deve ser definido na classe filha
    
    def get_audit_resource_type(self):
        """Obtém o tipo de recurso para auditoria"""
        return self.audit_resource_type or self.__class__.__name__.lower().replace('viewset', '')
    
    def perform_create(self, serializer):
        """Override para adicionar auditoria na criação"""
        instance = serializer.save()
        
        # Registra auditoria
        user_id = getattr(self.request.user, 'id', None) if hasattr(self.request, 'user') else None
        details = {
            'resource_type': self.get_audit_resource_type(),
            'resource_id': str(instance.id) if hasattr(instance, 'id') else None,
            'method': 'CREATE'
        }
        audit_logger.log_action('CREATE', user_id, details)
        
        return instance
    
    def perform_update(self, serializer):
        """Override para adicionar auditoria na atualização"""
        instance = serializer.save()
        
        # Registra auditoria
        user_id = getattr(self.request.user, 'id', None) if hasattr(self.request, 'user') else None
        details = {
            'resource_type': self.get_audit_resource_type(),
            'resource_id': str(instance.id) if hasattr(instance, 'id') else None,
            'method': 'UPDATE',
            'changed_fields': list(serializer.validated_data.keys()) if hasattr(serializer, 'validated_data') else []
        }
        audit_logger.log_action('UPDATE', user_id, details)
        
        return instance
    
    def perform_destroy(self, instance):
        """Override para adicionar auditoria na exclusão"""
        # Registra auditoria antes de deletar
        user_id = getattr(self.request.user, 'id', None) if hasattr(self.request, 'user') else None
        details = {
            'resource_type': self.get_audit_resource_type(),
            'resource_id': str(instance.id) if hasattr(instance, 'id') else None,
            'method': 'DELETE'
        }
        audit_logger.log_action('DELETE', user_id, details)
        
        # Executa a exclusão
        instance.delete()
    
    def list(self, request, *args, **kwargs):
        """Override para adicionar auditoria na listagem"""
        response = super().list(request, *args, **kwargs)
        
        # Registra acesso aos dados
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        audit_logger.log_data_access(user_id, self.get_audit_resource_type(), None, 'LIST')
        
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """Override para adicionar auditoria na recuperação"""
        response = super().retrieve(request, *args, **kwargs)
        
        # Registra acesso aos dados
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        resource_id = kwargs.get('pk')
        audit_logger.log_data_access(user_id, self.get_audit_resource_type(), resource_id, 'READ')
        
        return response


def log_security_event(event_type):
    """
    Decorator para registrar eventos de segurança
    
    Args:
        event_type: Tipo do evento de segurança
    
    Usage:
        @log_security_event('UNAUTHORIZED_ACCESS')
        def protected_view(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                # Registra evento de segurança em caso de erro
                user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
                details = {
                    'path': request.path,
                    'method': request.method,
                    'error': str(e),
                    'ip_address': request.META.get('REMOTE_ADDR')
                }
                audit_logger.log_security_event(event_type, user_id, details)
                raise
        return wrapper
    return decorator


def cache_tenant_metrics(cache_timeout=300):
    """
    Decorator para cachear métricas de tenant
    
    Args:
        cache_timeout: Tempo de cache em segundos
    
    Usage:
        @cache_tenant_metrics(600)
        def get_tenant_stats(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            
            tenant = get_current_tenant()
            if not tenant:
                return view_func(request, *args, **kwargs)
            
            # Gera chave de cache
            cache_key = f"tenant_metrics_{tenant.id}_{view_func.__name__}"
            
            # Tenta obter do cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executa a view e cacheia o resultado
            result = view_func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout=cache_timeout)
            
            return result
        return wrapper
    return decorator
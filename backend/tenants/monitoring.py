"""
Sistema de monitoramento multitenant para captura de logs,
métricas de performance e auditoria de ações por tenant.
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from .utils import get_current_tenant


# Thread-local storage para métricas
_metrics_storage = threading.local()


class TenantMetrics:
    """Classe para armazenar métricas por tenant"""
    
    def __init__(self):
        self.request_count = 0
        self.response_times = deque(maxlen=100)  # Últimas 100 requisições
        self.error_count = 0
        self.db_queries = deque(maxlen=50)  # Últimas 50 queries
        self.actions = deque(maxlen=200)  # Últimas 200 ações
        self.last_activity = datetime.now()
        self.endpoints_usage = defaultdict(int)
        self.user_actions = defaultdict(int)
    
    def add_request(self, response_time, endpoint, status_code):
        """Adiciona uma requisição às métricas"""
        self.request_count += 1
        self.response_times.append(response_time)
        self.last_activity = datetime.now()
        self.endpoints_usage[endpoint] += 1
        
        if status_code >= 400:
            self.error_count += 1
    
    def add_db_query(self, query_info):
        """Adiciona informações de query do banco"""
        self.db_queries.append({
            'sql': query_info.get('sql', ''),
            'time': query_info.get('time', 0),
            'timestamp': datetime.now().isoformat()
        })
    
    def add_action(self, action_type, user_id, details):
        """Adiciona uma ação de auditoria"""
        self.actions.append({
            'type': action_type,
            'user_id': user_id,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if user_id:
            self.user_actions[user_id] += 1
    
    def get_avg_response_time(self):
        """Calcula tempo médio de resposta"""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)
    
    def get_error_rate(self):
        """Calcula taxa de erro"""
        if self.request_count == 0:
            return 0
        return (self.error_count / self.request_count) * 100
    
    def to_dict(self):
        """Converte métricas para dicionário"""
        return {
            'request_count': self.request_count,
            'avg_response_time': self.get_avg_response_time(),
            'error_count': self.error_count,
            'error_rate': self.get_error_rate(),
            'last_activity': self.last_activity.isoformat(),
            'db_queries_count': len(self.db_queries),
            'actions_count': len(self.actions),
            'top_endpoints': dict(sorted(
                self.endpoints_usage.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),
            'active_users': len(self.user_actions)
        }


# Armazenamento global de métricas por tenant
_tenant_metrics = {}
_metrics_lock = threading.Lock()


def get_tenant_metrics(tenant_id):
    """Obtém métricas para um tenant específico"""
    with _metrics_lock:
        if tenant_id not in _tenant_metrics:
            _tenant_metrics[tenant_id] = TenantMetrics()
        return _tenant_metrics[tenant_id]


class TenantLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para captura de logs com identificação de tenant,
    métricas de performance e auditoria de ações.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Configurar logger específico para tenant
        self.logger = logging.getLogger('tenants.monitoring')
        
        # Configurar handler personalizado se não existir
        if not any(isinstance(h, TenantLogHandler) for h in self.logger.handlers):
            tenant_handler = TenantLogHandler()
            tenant_handler.setLevel(logging.INFO)
            formatter = TenantLogFormatter()
            tenant_handler.setFormatter(formatter)
            self.logger.addHandler(tenant_handler)
    
    def process_request(self, request):
        """Processa o início da requisição"""
        # Marca o tempo de início
        request._tenant_start_time = time.time()
        
        # Obtém informações da requisição
        tenant = get_current_tenant()
        request._tenant_info = {
            'tenant_id': str(tenant.id) if tenant else None,
            'tenant_name': tenant.name if tenant else None,
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self._get_client_ip(request),
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        }
        
        # Log da requisição
        if tenant:
            self.logger.info(
                f"Request started: {request.method} {request.path}",
                extra={
                    'tenant_id': str(tenant.id),
                    'tenant_name': tenant.name,
                    'user_id': request._tenant_info['user_id'],
                    'ip_address': request._tenant_info['ip_address']
                }
            )
    
    def process_response(self, request, response):
        """Processa o final da requisição"""
        # Calcula tempo de resposta
        start_time = getattr(request, '_tenant_start_time', time.time())
        response_time = time.time() - start_time
        
        # Obtém informações da requisição
        tenant_info = getattr(request, '_tenant_info', {})
        tenant_id = tenant_info.get('tenant_id')
        
        if tenant_id:
            # Atualiza métricas do tenant
            metrics = get_tenant_metrics(tenant_id)
            metrics.add_request(
                response_time,
                request.path,
                response.status_code
            )
            
            # Log da resposta
            self.logger.info(
                f"Request completed: {request.method} {request.path} - "
                f"Status: {response.status_code} - Time: {response_time:.3f}s",
                extra={
                    'tenant_id': tenant_id,
                    'tenant_name': tenant_info.get('tenant_name'),
                    'user_id': tenant_info.get('user_id'),
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'ip_address': tenant_info.get('ip_address')
                }
            )
            
            # Log de erro se status >= 400
            if response.status_code >= 400:
                self.logger.warning(
                    f"Error response: {request.method} {request.path} - "
                    f"Status: {response.status_code}",
                    extra={
                        'tenant_id': tenant_id,
                        'tenant_name': tenant_info.get('tenant_name'),
                        'user_id': tenant_info.get('user_id'),
                        'status_code': response.status_code,
                        'error_type': 'http_error'
                    }
                )
        
        return response
    
    def process_exception(self, request, exception):
        """Processa exceções durante a requisição"""
        tenant_info = getattr(request, '_tenant_info', {})
        tenant_id = tenant_info.get('tenant_id')
        
        if tenant_id:
            # Atualiza métricas de erro
            metrics = get_tenant_metrics(tenant_id)
            metrics.error_count += 1
            
            # Log da exceção
            self.logger.error(
                f"Exception in request: {request.method} {request.path} - "
                f"Error: {str(exception)}",
                extra={
                    'tenant_id': tenant_id,
                    'tenant_name': tenant_info.get('tenant_name'),
                    'user_id': tenant_info.get('user_id'),
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception)
                },
                exc_info=True
            )
        
        return None  # Permite que a exceção continue sendo processada
    
    def _get_client_ip(self, request):
        """Obtém o IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TenantLogHandler(logging.Handler):
    """Handler personalizado para logs de tenant"""
    
    def __init__(self):
        super().__init__()
        self.logs_cache = defaultdict(deque)
        self.cache_max_size = 1000
    
    def emit(self, record):
        """Emite um log record"""
        try:
            # Obtém tenant_id do record
            tenant_id = getattr(record, 'tenant_id', None)
            
            if tenant_id:
                # Armazena o log em cache por tenant
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'tenant_id': tenant_id,
                    'tenant_name': getattr(record, 'tenant_name', None),
                    'user_id': getattr(record, 'user_id', None),
                    'ip_address': getattr(record, 'ip_address', None),
                    'response_time': getattr(record, 'response_time', None),
                    'status_code': getattr(record, 'status_code', None),
                    'exception_type': getattr(record, 'exception_type', None)
                }
                
                # Adiciona ao cache do tenant
                tenant_logs = self.logs_cache[tenant_id]
                tenant_logs.append(log_entry)
                
                # Limita o tamanho do cache
                if len(tenant_logs) > self.cache_max_size:
                    tenant_logs.popleft()
                
                # Salva no cache do Django para persistência
                cache_key = f"tenant_logs_{tenant_id}"
                cached_logs = cache.get(cache_key, [])
                cached_logs.append(log_entry)
                
                # Mantém apenas os últimos 500 logs no cache
                if len(cached_logs) > 500:
                    cached_logs = cached_logs[-500:]
                
                cache.set(cache_key, cached_logs, timeout=3600)  # 1 hora
        
        except Exception:
            # Em caso de erro no handler, não deve quebrar a aplicação
            pass
    
    def get_tenant_logs(self, tenant_id, limit=100):
        """Obtém logs de um tenant específico"""
        # Primeiro tenta o cache em memória
        if tenant_id in self.logs_cache:
            logs = list(self.logs_cache[tenant_id])
            return logs[-limit:] if len(logs) > limit else logs
        
        # Fallback para cache do Django
        cache_key = f"tenant_logs_{tenant_id}"
        cached_logs = cache.get(cache_key, [])
        return cached_logs[-limit:] if len(cached_logs) > limit else cached_logs


class TenantLogFormatter(logging.Formatter):
    """Formatter personalizado para logs de tenant"""
    
    def format(self, record):
        # Adiciona informações de tenant ao record
        tenant_id = getattr(record, 'tenant_id', 'unknown')
        tenant_name = getattr(record, 'tenant_name', 'unknown')
        
        # Formato base
        base_format = f"[{record.asctime}] {record.levelname} [{record.name}] [Tenant: {tenant_name}({tenant_id})] {record.getMessage()}"
        
        # Adiciona informações extras se disponíveis
        extras = []
        if hasattr(record, 'user_id') and record.user_id:
            extras.append(f"User: {record.user_id}")
        if hasattr(record, 'ip_address') and record.ip_address:
            extras.append(f"IP: {record.ip_address}")
        if hasattr(record, 'response_time') and record.response_time:
            extras.append(f"Time: {record.response_time:.3f}s")
        
        if extras:
            base_format += f" [{', '.join(extras)}]"
        
        return base_format


class TenantAuditLogger:
    """Classe para logging de auditoria específico por tenant"""
    
    def __init__(self):
        self.logger = logging.getLogger('tenants.audit')
    
    def log_action(self, action_type, user_id=None, details=None, tenant=None):
        """
        Registra uma ação de auditoria
        
        Args:
            action_type: Tipo da ação (CREATE, UPDATE, DELETE, LOGIN, etc.)
            user_id: ID do usuário que executou a ação
            details: Detalhes adicionais da ação
            tenant: Tenant específico (usa o atual se não fornecido)
        """
        if not tenant:
            tenant = get_current_tenant()
        
        if not tenant:
            return
        
        # Atualiza métricas do tenant
        metrics = get_tenant_metrics(str(tenant.id))
        metrics.add_action(action_type, user_id, details)
        
        # Log da ação
        self.logger.info(
            f"Action: {action_type}",
            extra={
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'user_id': user_id,
                'action_type': action_type,
                'action_details': json.dumps(details) if details else None
            }
        )
    
    def log_login(self, user_id, success=True, ip_address=None):
        """Registra tentativa de login"""
        action_type = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
        details = {'ip_address': ip_address} if ip_address else None
        self.log_action(action_type, user_id, details)
    
    def log_data_access(self, user_id, resource_type, resource_id, action='READ'):
        """Registra acesso a dados"""
        details = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        self.log_action(f'DATA_{action}', user_id, details)
    
    def log_configuration_change(self, user_id, config_key, old_value=None, new_value=None):
        """Registra mudança de configuração"""
        details = {
            'config_key': config_key,
            'old_value': old_value,
            'new_value': new_value
        }
        self.log_action('CONFIG_CHANGE', user_id, details)
    
    def log_security_event(self, event_type, user_id=None, details=None):
        """Registra evento de segurança"""
        self.log_action(f'SECURITY_{event_type}', user_id, details)


# Instância global do audit logger
audit_logger = TenantAuditLogger()


class TenantDatabaseMonitor:
    """Monitor para queries de banco de dados por tenant"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'TENANT_DB_MONITORING', True)
    
    def log_query(self, sql, params, duration, tenant_id=None):
        """Registra uma query do banco de dados"""
        if not self.enabled:
            return
        
        if not tenant_id:
            tenant = get_current_tenant()
            tenant_id = str(tenant.id) if tenant else None
        
        if tenant_id:
            metrics = get_tenant_metrics(tenant_id)
            metrics.add_db_query({
                'sql': sql[:500],  # Limita tamanho da query
                'params': str(params)[:200] if params else None,
                'time': duration
            })


# Instância global do database monitor
db_monitor = TenantDatabaseMonitor()


def get_tenant_metrics_summary(tenant_id):
    """
    Obtém resumo das métricas de um tenant
    
    Args:
        tenant_id: ID do tenant
    
    Returns:
        dict: Resumo das métricas
    """
    metrics = get_tenant_metrics(tenant_id)
    return metrics.to_dict()


def get_all_tenants_metrics():
    """
    Obtém métricas de todos os tenants
    
    Returns:
        dict: Métricas por tenant
    """
    with _metrics_lock:
        return {
            tenant_id: metrics.to_dict()
            for tenant_id, metrics in _tenant_metrics.items()
        }


def clear_tenant_metrics(tenant_id):
    """Limpa métricas de um tenant específico"""
    with _metrics_lock:
        if tenant_id in _tenant_metrics:
            del _tenant_metrics[tenant_id]


def get_tenant_logs(tenant_id, limit=100):
    """
    Obtém logs de um tenant específico
    
    Args:
        tenant_id: ID do tenant
        limit: Número máximo de logs
    
    Returns:
        list: Lista de logs
    """
    # Procura por handler TenantLogHandler
    logger = logging.getLogger('tenants.monitoring')
    for handler in logger.handlers:
        if isinstance(handler, TenantLogHandler):
            return handler.get_tenant_logs(tenant_id, limit)
    
    # Fallback para cache do Django
    cache_key = f"tenant_logs_{tenant_id}"
    cached_logs = cache.get(cache_key, [])
    return cached_logs[-limit:] if len(cached_logs) > limit else cached_logs


def get_system_health():
    """
    Obtém informações de saúde do sistema
    
    Returns:
        dict: Informações de saúde
    """
    total_tenants = len(_tenant_metrics)
    total_requests = sum(m.request_count for m in _tenant_metrics.values())
    total_errors = sum(m.error_count for m in _tenant_metrics.values())
    
    # Calcula tempo médio de resposta global
    all_response_times = []
    for metrics in _tenant_metrics.values():
        all_response_times.extend(metrics.response_times)
    
    avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
    
    return {
        'total_tenants': total_tenants,
        'total_requests': total_requests,
        'total_errors': total_errors,
        'global_error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
        'avg_response_time': avg_response_time,
        'active_tenants': len([
            m for m in _tenant_metrics.values()
            if (datetime.now() - m.last_activity).seconds < 3600  # Ativo na última hora
        ]),
        'timestamp': datetime.now().isoformat()
    }
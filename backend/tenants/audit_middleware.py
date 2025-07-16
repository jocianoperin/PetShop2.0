"""
Middleware para auditoria automática de todas as requisições.
Captura e registra automaticamente todas as operações realizadas no sistema.
"""

import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import resolve
from django.core.exceptions import PermissionDenied
from .audit_models import AuditLog, AuditEventType
from .utils import get_current_tenant


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoria automática de requisições.
    Registra todas as operações realizadas no sistema para conformidade LGPD.
    """
    
    # Endpoints que não precisam de auditoria detalhada
    EXEMPT_PATHS = [
        '/api/health/',
        '/api/docs/',
        '/admin/jsi18n/',
        '/static/',
        '/media/',
        '/favicon.ico'
    ]
    
    # Métodos HTTP que devem ser auditados
    AUDITED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Recursos que contêm dados sensíveis
    SENSITIVE_RESOURCES = [
        'clientes', 'animals', 'users', 'agendamentos',
        'vendas', 'produtos', 'servicos'
    ]

    def process_request(self, request):
        """Processa a requisição antes da view"""
        # Marcar início do processamento
        request._audit_start_time = time.time()
        
        # Verificar se deve auditar esta requisição
        if self._should_audit_request(request):
            request._should_audit = True
            
            # Capturar dados da requisição para auditoria
            request._audit_data = self._capture_request_data(request)
        else:
            request._should_audit = False

    def process_response(self, request, response):
        """Processa a resposta após a view"""
        if getattr(request, '_should_audit', False):
            self._audit_request(request, response)
        
        return response

    def process_exception(self, request, exception):
        """Processa exceções durante o processamento"""
        if getattr(request, '_should_audit', False):
            self._audit_exception(request, exception)

    def _should_audit_request(self, request):
        """Determina se a requisição deve ser auditada"""
        path = request.path
        
        # Verificar caminhos isentos
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return False
        
        # Auditar apenas requisições da API
        if not path.startswith('/api/'):
            return False
        
        # Sempre auditar métodos que modificam dados
        if request.method in self.AUDITED_METHODS:
            return True
        
        # Auditar GET em recursos sensíveis
        if request.method == 'GET' and self._is_sensitive_endpoint(path):
            return True
        
        return False

    def _is_sensitive_endpoint(self, path):
        """Verifica se o endpoint acessa dados sensíveis"""
        for resource in self.SENSITIVE_RESOURCES:
            if f'/{resource}/' in path or path.endswith(f'/{resource}'):
                return True
        return False

    def _capture_request_data(self, request):
        """Captura dados da requisição para auditoria"""
        data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
        }
        
        # Capturar dados do corpo da requisição (se aplicável)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if hasattr(request, 'data'):
                    # DRF request
                    data['request_data'] = self._sanitize_request_data(request.data)
                elif request.content_type == 'application/json':
                    # JSON request
                    body = json.loads(request.body.decode('utf-8'))
                    data['request_data'] = self._sanitize_request_data(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                data['request_data'] = {'error': 'Could not parse request body'}
        
        return data

    def _sanitize_request_data(self, data):
        """Remove dados sensíveis dos logs de auditoria"""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = [
            'password', 'senha', 'token', 'secret', 'key',
            'cpf', 'cnpj', 'rg', 'credit_card', 'cartao'
        ]
        
        sanitized = {}
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_data(value)
            else:
                sanitized[key] = value
        
        return sanitized

    def _audit_request(self, request, response):
        """Registra a auditoria da requisição"""
        try:
            tenant = get_current_tenant()
            if not tenant:
                return
            
            # Determinar tipo de evento e ação
            event_type, action = self._determine_event_type_and_action(request, response)
            
            # Extrair informações do recurso
            resource_type, resource_id = self._extract_resource_info(request)
            
            # Calcular tempo de processamento
            processing_time = time.time() - getattr(request, '_audit_start_time', time.time())
            
            # Determinar sucesso da operação
            success = 200 <= response.status_code < 400
            
            # Metadados adicionais
            metadata = {
                'processing_time_ms': round(processing_time * 1000, 2),
                'response_status': response.status_code,
                'request_size': len(request.body) if hasattr(request, 'body') else 0,
                'response_size': len(response.content) if hasattr(response, 'content') else 0
            }
            
            # Adicionar dados da requisição se disponível
            if hasattr(request, '_audit_data'):
                metadata.update(request._audit_data)
            
            # Registrar log de auditoria
            from .audit_system import log_audit_event
            log_audit_event(
                event_type=event_type,
                resource_type=resource_type,
                action=action,
                request=request,
                user=getattr(request, 'user', None),
                resource_id=resource_id,
                metadata=metadata,
                success=success,
                is_sensitive_data=self._is_sensitive_endpoint(request.path)
            )
            
        except Exception as e:
            # Log do erro sem interromper o fluxo
            import logging
            logger = logging.getLogger('tenant_audit')
            logger.error(f'Erro na auditoria: {str(e)}', exc_info=True)

    def _audit_exception(self, request, exception):
        """Registra auditoria quando ocorre exceção"""
        try:
            tenant = get_current_tenant()
            if not tenant:
                return
            
            # Determinar tipo de evento
            if isinstance(exception, PermissionDenied):
                event_type = AuditEventType.SECURITY_EVENT
                action = 'permission_denied'
            else:
                event_type = AuditEventType.SECURITY_EVENT
                action = 'exception'
            
            resource_type, resource_id = self._extract_resource_info(request)
            
            # Metadados da exceção
            metadata = {
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
            }
            
            if hasattr(request, '_audit_data'):
                metadata.update(request._audit_data)
            
            # Registrar log de auditoria
            from .audit_system import log_audit_event
            log_audit_event(
                event_type=event_type,
                resource_type=resource_type,
                action=action,
                request=request,
                user=getattr(request, 'user', None),
                resource_id=resource_id,
                metadata=metadata,
                success=False,
                error_message=str(exception),
                is_sensitive_data=self._is_sensitive_endpoint(request.path)
            )
            
        except Exception as e:
            # Log do erro sem interromper o fluxo
            import logging
            logger = logging.getLogger('tenant_audit')
            logger.error(f'Erro na auditoria de exceção: {str(e)}', exc_info=True)

    def _determine_event_type_and_action(self, request, response):
        """Determina o tipo de evento e ação baseado na requisição"""
        method = request.method
        path = request.path
        
        # Mapeamento de métodos HTTP para tipos de evento
        method_to_event = {
            'GET': AuditEventType.READ,
            'POST': AuditEventType.CREATE,
            'PUT': AuditEventType.UPDATE,
            'PATCH': AuditEventType.UPDATE,
            'DELETE': AuditEventType.DELETE
        }
        
        event_type = method_to_event.get(method, AuditEventType.DATA_ACCESS)
        
        # Ações específicas baseadas no endpoint
        if '/login' in path:
            return AuditEventType.LOGIN, 'login'
        elif '/logout' in path:
            return AuditEventType.LOGOUT, 'logout'
        elif '/export' in path:
            return AuditEventType.EXPORT, 'export'
        elif '/import' in path:
            return AuditEventType.IMPORT, 'import'
        elif '/lgpd' in path:
            return AuditEventType.LGPD_REQUEST, 'lgpd_request'
        
        return event_type, method.lower()

    def _extract_resource_info(self, request):
        """Extrai informações do recurso da URL"""
        try:
            # Usar o resolver do Django para extrair informações da URL
            resolver_match = resolve(request.path)
            
            # Extrair nome da view como tipo de recurso
            view_name = resolver_match.view_name or ''
            if ':' in view_name:
                resource_type = view_name.split(':')[-1]
            else:
                resource_type = view_name
            
            # Extrair ID do recurso dos kwargs da URL
            resource_id = None
            if 'pk' in resolver_match.kwargs:
                resource_id = resolver_match.kwargs['pk']
            elif 'id' in resolver_match.kwargs:
                resource_id = resolver_match.kwargs['id']
            
            # Fallback: extrair do path
            if not resource_type:
                path_parts = request.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    resource_type = path_parts[1]  # Assumindo /api/resource/
            
            return resource_type or 'unknown', resource_id
            
        except Exception:
            # Fallback simples
            path_parts = request.path.strip('/').split('/')
            resource_type = path_parts[1] if len(path_parts) >= 2 else 'unknown'
            return resource_type, None


class DataChangeAuditMiddleware(MiddlewareMixin):
    """
    Middleware para capturar alterações em dados pessoais.
    Trabalha em conjunto com signals do Django para rastrear mudanças.
    """
    
    def process_request(self, request):
        """Marca o início do processamento para rastreamento de mudanças"""
        request._data_change_tracking = True

    def process_response(self, request, response):
        """Finaliza o rastreamento de mudanças de dados"""
        # O rastreamento real é feito via signals do Django
        # Este middleware apenas marca o contexto
        return response


# Middleware para rate limiting baseado em auditoria
class AuditBasedRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware para rate limiting baseado em logs de auditoria.
    Previne abuso e ataques baseado no histórico de requisições.
    """
    
    def process_request(self, request):
        """Verifica rate limiting baseado em auditoria"""
        if not self._should_check_rate_limit(request):
            return None
        
        # Verificar rate limiting
        if self._is_rate_limited(request):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Muitas requisições em pouco tempo. Tente novamente mais tarde.'
            }, status=429)
        
        return None

    def _should_check_rate_limit(self, request):
        """Determina se deve verificar rate limiting"""
        # Aplicar rate limiting apenas em endpoints sensíveis
        sensitive_paths = ['/api/auth/', '/api/lgpd/', '/api/export/']
        return any(request.path.startswith(path) for path in sensitive_paths)

    def _is_rate_limited(self, request):
        """Verifica se a requisição deve ser limitada"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        tenant = get_current_tenant()
        if not tenant:
            return False
        
        # Obter IP do cliente
        ip_address = self._get_client_ip(request)
        
        # Verificar número de requisições na última hora
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_requests = AuditLog.objects.filter(
            tenant_id=tenant.id,
            ip_address=ip_address,
            timestamp__gte=one_hour_ago
        ).count()
        
        # Limite: 100 requisições por hora por IP
        return recent_requests > 100

    def _get_client_ip(self, request):
        """Extrai o IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
"""
Sistema de auditoria de acesso para conformidade LGPD.
Implementa rastreamento detalhado de todas as operações realizadas no sistema.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone
from .utils import get_current_tenant
from .audit_models import AuditLog, AuditEventType, LGPDRequest, DataChangeLog


# Configurar logger específico para auditoria
audit_logger = logging.getLogger('tenant_audit')

# Funções utilitárias para auditoria

def _get_client_ip(request):
    """Extrai o IP real do cliente considerando proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def _log_to_file(audit_log):
    """Registra o evento no arquivo de log estruturado"""
    log_data = {
        'timestamp': audit_log.timestamp.isoformat(),
        'tenant_id': str(audit_log.tenant_id),
        'user_id': str(audit_log.user_id) if audit_log.user_id else None,
        'user_email': audit_log.user_email,
        'event_type': audit_log.event_type,
        'resource_type': audit_log.resource_type,
        'resource_id': audit_log.resource_id,
        'action': audit_log.action,
        'ip_address': audit_log.ip_address,
        'success': audit_log.success,
        'is_sensitive_data': audit_log.is_sensitive_data
    }
    
    audit_logger.info(json.dumps(log_data, ensure_ascii=False))

def log_audit_event(event_type: str, resource_type: str, action: str, 
              request=None, user=None, resource_id: str = None,
              old_values: Dict = None, new_values: Dict = None,
              metadata: Dict = None, success: bool = True,
              error_message: str = None, is_sensitive_data: bool = False):
    """
    Função utilitária para registrar eventos de auditoria.
    """
    tenant = get_current_tenant()
    if not tenant:
        return None
    
    # Extrair informações da requisição
    ip_address = '127.0.0.1'
    user_agent = ''
    request_method = 'SYSTEM'  # Default para operações do sistema
    request_path = ''
    
    if request:
        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]  # Limitar tamanho
        request_method = request.method
        request_path = request.path[:500]  # Limitar tamanho
    
    # Informações do usuário
    user_id = None
    user_email = ''
    if user:
        user_id = getattr(user, 'id', None)
        user_email = getattr(user, 'email', '')
    
    # Criar log de auditoria
    audit_log = AuditLog.objects.create(
        tenant_id=tenant.id,
        user_id=user_id,
        user_email=user_email,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else '',
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        old_values=old_values or {},
        new_values=new_values or {},
        metadata=metadata or {},
        success=success,
        error_message=error_message or '',
        is_sensitive_data=is_sensitive_data
    )
    
    # Log estruturado para arquivo
    _log_to_file(audit_log)
    
    return audit_log

def audit_login(request, user, success=True, error_message=None):
    """Registra evento de login"""
    return log_audit_event(
        event_type=AuditEventType.LOGIN,
        resource_type='Authentication',
        action='login',
        request=request,
        user=user,
        success=success,
        error_message=error_message,
        metadata={'login_method': 'email_password'}
    )


def audit_logout(request, user):
    """Registra evento de logout"""
    return log_audit_event(
        event_type=AuditEventType.LOGOUT,
        resource_type='Authentication',
        action='logout',
        request=request,
        user=user
    )


def audit_data_access(request, user, resource_type, resource_id, action='read'):
    """Registra acesso a dados"""
    return log_audit_event(
        event_type=AuditEventType.DATA_ACCESS,
        resource_type=resource_type,
        action=action,
        request=request,
        user=user,
        resource_id=resource_id,
        is_sensitive_data=True
    )


def audit_crud_operation(request, user, resource_type, resource_id, 
                        operation, old_values=None, new_values=None):
    """Registra operações CRUD"""
    event_type_map = {
        'create': AuditEventType.CREATE,
        'read': AuditEventType.READ,
        'update': AuditEventType.UPDATE,
        'delete': AuditEventType.DELETE
    }
    
    return log_audit_event(
        event_type=event_type_map.get(operation, AuditEventType.DATA_ACCESS),
        resource_type=resource_type,
        action=operation,
        request=request,
        user=user,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        is_sensitive_data=_is_sensitive_resource(resource_type)
    )


def audit_lgpd_request(request_obj, action, user_email, details=None):
    """Registra ações relacionadas a solicitações LGPD"""
    return log_audit_event(
        event_type=AuditEventType.LGPD_REQUEST,
        resource_type='LGPDRequest',
        action=action,
        resource_id=str(request_obj.id),
        metadata={
            'request_type': request_obj.request_type,
            'requester_email': request_obj.requester_email,
            'status': request_obj.status,
            'details': details or {}
        },
        is_sensitive_data=True
    )


def _is_sensitive_resource(resource_type):
    """Determina se um tipo de recurso contém dados sensíveis"""
    sensitive_resources = [
        'Cliente', 'Animal', 'TenantUser', 'ConsentRecord',
        'EncryptedClienteData', 'EncryptedAnimalData'
    ]
    return resource_type in sensitive_resources


# Decorator para auditoria automática de views
def audit_view(resource_type=None, action=None, sensitive_data=False):
    """
    Decorator para adicionar auditoria automática a views.
    
    Usage:
        @audit_view(resource_type='Cliente', action='list')
        def list_clientes(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Executar a view
            try:
                response = view_func(request, *args, **kwargs)
                success = True
                error_message = None
            except Exception as e:
                response = None
                success = False
                error_message = str(e)
                raise
            finally:
                # Registrar auditoria
                log_audit_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource_type=resource_type or view_func.__name__,
                    action=action or request.method.lower(),
                    request=request,
                    user=getattr(request, 'user', None),
                    success=success,
                    error_message=error_message,
                    is_sensitive_data=sensitive_data
                )
            
            return response
        return wrapper
    return decorator
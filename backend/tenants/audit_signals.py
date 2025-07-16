"""
Signals do Django para auditoria automática de mudanças em dados.
Captura automaticamente todas as alterações em modelos para conformidade LGPD.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.exceptions import ObjectDoesNotExist
from .audit_models import AuditLog, DataChangeLog, AuditEventType
from .utils import get_current_tenant
from .models import TenantUser
import threading
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

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

def _audit_login(request, user, success=True, error_message=None):
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

def _audit_logout(request, user):
    """Registra evento de logout"""
    return log_audit_event(
        event_type=AuditEventType.LOGOUT,
        resource_type='Authentication',
        action='logout',
        request=request,
        user=user
    )


# Thread local storage para rastrear mudanças
_thread_local = threading.local()


def get_current_user():
    """Obtém o usuário atual do contexto da thread"""
    return getattr(_thread_local, 'current_user', None)


def set_current_user(user):
    """Define o usuário atual no contexto da thread"""
    _thread_local.current_user = user


# Middleware para capturar usuário atual
class CurrentUserMiddleware:
    """Middleware para capturar o usuário atual em signals"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, 'user', None))
        response = self.get_response(request)
        set_current_user(None)
        return response


# Modelos que devem ser auditados
AUDITED_MODELS = [
    'Cliente', 'Animal', 'Servico', 'Agendamento', 
    'Produto', 'Venda', 'TenantUser', 'TenantConfiguration',
    'EncryptedClienteData', 'EncryptedAnimalData', 'ConsentRecord'
]

# Campos que contêm dados pessoais
PERSONAL_DATA_FIELDS = {
    'Cliente': ['nome', 'email', 'telefone', 'endereco', 'cpf', 'rg'],
    'Animal': ['nome', 'observacoes'],
    'TenantUser': ['email', 'first_name', 'last_name'],
    'Agendamento': ['observacoes'],
    'Venda': ['observacoes'],
    'EncryptedClienteData': ['encrypted_data'],
    'EncryptedAnimalData': ['encrypted_data'],
    'ConsentRecord': ['consent_data']
}

# Campos que contêm dados sensíveis
SENSITIVE_DATA_FIELDS = {
    'Cliente': ['cpf', 'rg', 'email'],
    'Animal': ['observacoes'],  # Pode conter informações médicas
    'EncryptedClienteData': ['encrypted_data'],
    'EncryptedAnimalData': ['encrypted_data'],
    'ConsentRecord': ['consent_data']
}


@receiver(pre_save)
def capture_old_values(sender, instance, **kwargs):
    """Captura valores antigos antes da alteração"""
    if sender.__name__ not in AUDITED_MODELS:
        return
    
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_values = {}
            
            # Capturar valores de campos relevantes
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(old_instance, field_name, None)
                new_value = getattr(instance, field_name, None)
                
                if old_value != new_value:
                    instance._old_values[field_name] = old_value
                    
        except ObjectDoesNotExist:
            instance._old_values = {}
    else:
        instance._old_values = {}


@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
    """Audita criação e atualização de modelos"""
    if sender.__name__ not in AUDITED_MODELS:
        return
    
    tenant = get_current_tenant()
    if not tenant:
        return
    
    user = get_current_user()
    
    # Determinar tipo de operação
    operation = 'create' if created else 'update'
    event_type = AuditEventType.CREATE if created else AuditEventType.UPDATE
    
    # Capturar valores novos
    new_values = {}
    old_values = getattr(instance, '_old_values', {})
    
    for field in instance._meta.fields:
        field_name = field.name
        if created or field_name in old_values:
            new_values[field_name] = str(getattr(instance, field_name, None))
    
    # Registrar auditoria geral
    log_audit_event(
        event_type=event_type,
        resource_type=sender.__name__,
        action=operation,
        user=user,
        resource_id=str(instance.pk),
        old_values=old_values,
        new_values=new_values,
        is_sensitive_data=_has_sensitive_data(sender.__name__, old_values, new_values)
    )
    
    # Registrar mudanças detalhadas para dados pessoais
    if not created:
        _log_personal_data_changes(
            tenant, user, sender.__name__, instance, old_values, new_values
        )


@receiver(post_delete)
def audit_model_delete(sender, instance, **kwargs):
    """Audita exclusão de modelos"""
    if sender.__name__ not in AUDITED_MODELS:
        return
    
    tenant = get_current_tenant()
    if not tenant:
        return
    
    user = get_current_user()
    
    # Capturar valores do objeto excluído
    old_values = {}
    for field in instance._meta.fields:
        field_name = field.name
        old_values[field_name] = str(getattr(instance, field_name, None))
    
    # Registrar auditoria
    log_audit_event(
        event_type=AuditEventType.DELETE,
        resource_type=sender.__name__,
        action='delete',
        user=user,
        resource_id=str(instance.pk),
        old_values=old_values,
        is_sensitive_data=_has_sensitive_data(sender.__name__, old_values, {})
    )
    
    # Para exclusões de dados pessoais, registrar log detalhado
    if sender.__name__ in PERSONAL_DATA_FIELDS:
        _log_personal_data_deletion(tenant, user, sender.__name__, instance, old_values)


@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """Audita login de usuários"""
    _audit_login(request, user, success=True)
    
    # Atualizar último login se for TenantUser
    if hasattr(user, 'tenant'):
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])


@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """Audita logout de usuários"""
    if user:
        _audit_logout(request, user)


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    """Audita tentativas de login falhadas"""
    _audit_login(
        request, 
        None, 
        success=False, 
        error_message=f"Login failed for: {credentials.get('username', 'unknown')}"
    )


def _has_sensitive_data(model_name, old_values, new_values):
    """Verifica se as mudanças envolvem dados sensíveis"""
    sensitive_fields = SENSITIVE_DATA_FIELDS.get(model_name, [])
    
    for field in sensitive_fields:
        if field in old_values or field in new_values:
            return True
    
    return False


def _log_personal_data_changes(tenant, user, model_name, instance, old_values, new_values):
    """Registra mudanças detalhadas em dados pessoais"""
    personal_fields = PERSONAL_DATA_FIELDS.get(model_name, [])
    sensitive_fields = SENSITIVE_DATA_FIELDS.get(model_name, [])
    
    for field_name in old_values:
        if field_name in personal_fields:
            # Determinar categoria dos dados
            data_category = _get_data_category(model_name, field_name)
            
            # Criar log de mudança
            DataChangeLog.objects.create(
                tenant_id=tenant.id,
                table_name=model_name.lower(),
                record_id=str(instance.pk),
                field_name=field_name,
                old_value=str(old_values[field_name]),
                new_value=str(new_values.get(field_name, '')),
                changed_by=user.id if user else None,
                is_personal_data=True,
                is_sensitive_data=field_name in sensitive_fields,
                data_category=data_category
            )


def _log_personal_data_deletion(tenant, user, model_name, instance, old_values):
    """Registra exclusão de dados pessoais"""
    personal_fields = PERSONAL_DATA_FIELDS.get(model_name, [])
    sensitive_fields = SENSITIVE_DATA_FIELDS.get(model_name, [])
    
    for field_name in personal_fields:
        if field_name in old_values:
            data_category = _get_data_category(model_name, field_name)
            
            DataChangeLog.objects.create(
                tenant_id=tenant.id,
                table_name=model_name.lower(),
                record_id=str(instance.pk),
                field_name=field_name,
                old_value=str(old_values[field_name]),
                new_value='[DELETED]',
                changed_by=user.id if user else None,
                change_reason='Data deletion',
                is_personal_data=True,
                is_sensitive_data=field_name in sensitive_fields,
                data_category=data_category
            )


def _get_data_category(model_name, field_name):
    """Determina a categoria dos dados pessoais"""
    categories = {
        'nome': 'identification',
        'email': 'contact',
        'telefone': 'contact',
        'endereco': 'address',
        'cpf': 'document',
        'rg': 'document',
        'observacoes': 'notes',
        'first_name': 'identification',
        'last_name': 'identification',
        'encrypted_data': 'encrypted_personal',
        'consent_data': 'consent'
    }
    
    return categories.get(field_name, 'other')


# Função para registrar auditoria manual
def manual_audit_log(event_type, resource_type, action, user=None, 
                    resource_id=None, old_values=None, new_values=None,
                    metadata=None, is_sensitive_data=False):
    """
    Função para registrar auditoria manual quando necessário.
    
    Usage:
        manual_audit_log(
            event_type=AuditEventType.LGPD_REQUEST,
            resource_type='Cliente',
            action='data_export',
            user=request.user,
            resource_id='123',
            metadata={'export_format': 'json'}
        )
    """
    return log_audit_event(
        event_type=event_type,
        resource_type=resource_type,
        action=action,
        user=user,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        metadata=metadata,
        is_sensitive_data=is_sensitive_data
    )


# Função para auditoria de consentimento LGPD
def audit_consent_change(consent_record, action, user, details=None):
    """Audita mudanças em consentimentos LGPD"""
    return log_audit_event(
        event_type=AuditEventType.CONSENT_CHANGE,
        resource_type='ConsentRecord',
        action=action,
        user=user,
        resource_id=str(consent_record.id),
        metadata={
            'consent_type': consent_record.consent_type,
            'consent_status': consent_record.consent_status,
            'data_subject_email': consent_record.data_subject_email,
            'details': details or {}
        },
        is_sensitive_data=True
    )


# Função para auditoria de exportação de dados
def audit_data_export(user, export_type, data_subject_email, export_format, file_size=None):
    """Audita exportações de dados pessoais"""
    return log_audit_event(
        event_type=AuditEventType.LGPD_EXPORT,
        resource_type='DataExport',
        action='export_personal_data',
        user=user,
        metadata={
            'export_type': export_type,
            'data_subject_email': data_subject_email,
            'export_format': export_format,
            'file_size_bytes': file_size
        },
        is_sensitive_data=True
    )


# Função para auditoria de exclusão LGPD
def audit_lgpd_deletion(user, data_subject_email, deleted_records, deletion_reason):
    """Audita exclusões de dados por solicitação LGPD"""
    return log_audit_event(
        event_type=AuditEventType.LGPD_DELETION,
        resource_type='LGPDDeletion',
        action='delete_personal_data',
        user=user,
        metadata={
            'data_subject_email': data_subject_email,
            'deleted_records': deleted_records,
            'deletion_reason': deletion_reason,
            'total_records_deleted': len(deleted_records) if isinstance(deleted_records, list) else 0
        },
        is_sensitive_data=True
    )
"""
Modelos para sistema de auditoria e conformidade LGPD.
Separado do audit_system.py para evitar imports circulares.
"""

import json
import uuid
from datetime import datetime, timezone
from django.db import models
from django.utils import timezone as django_timezone


class AuditEventType(models.TextChoices):
    """Tipos de eventos de auditoria"""
    LOGIN = 'LOGIN', 'Login'
    LOGOUT = 'LOGOUT', 'Logout'
    CREATE = 'CREATE', 'Criação'
    READ = 'READ', 'Leitura'
    UPDATE = 'UPDATE', 'Atualização'
    DELETE = 'DELETE', 'Exclusão'
    EXPORT = 'EXPORT', 'Exportação'
    IMPORT = 'IMPORT', 'Importação'
    PERMISSION_CHANGE = 'PERMISSION_CHANGE', 'Alteração de Permissão'
    DATA_ACCESS = 'DATA_ACCESS', 'Acesso a Dados'
    LGPD_REQUEST = 'LGPD_REQUEST', 'Solicitação LGPD'
    LGPD_DELETION = 'LGPD_DELETION', 'Exclusão LGPD'
    LGPD_EXPORT = 'LGPD_EXPORT', 'Exportação LGPD'
    CONSENT_CHANGE = 'CONSENT_CHANGE', 'Alteração de Consentimento'
    SECURITY_EVENT = 'SECURITY_EVENT', 'Evento de Segurança'


class AuditLog(models.Model):
    """
    Modelo para logs de auditoria por tenant.
    Registra todas as operações realizadas no sistema.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, verbose_name="ID do Tenant")
    user_id = models.UUIDField(null=True, blank=True, db_index=True, verbose_name="ID do Usuário")
    user_email = models.EmailField(blank=True, verbose_name="Email do Usuário")
    
    # Detalhes do evento
    event_type = models.CharField(
        max_length=50,
        choices=AuditEventType.choices,
        verbose_name="Tipo de Evento"
    )
    resource_type = models.CharField(max_length=100, verbose_name="Tipo de Recurso")
    resource_id = models.CharField(max_length=100, blank=True, verbose_name="ID do Recurso")
    action = models.CharField(max_length=100, verbose_name="Ação")
    
    # Contexto da requisição
    ip_address = models.GenericIPAddressField(verbose_name="Endereço IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    request_method = models.CharField(max_length=10, blank=True, verbose_name="Método HTTP")
    request_path = models.CharField(max_length=500, blank=True, verbose_name="Caminho da Requisição")
    
    # Dados do evento
    old_values = models.JSONField(null=True, blank=True, verbose_name="Valores Anteriores")
    new_values = models.JSONField(null=True, blank=True, verbose_name="Novos Valores")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadados")
    
    # Status e resultado
    success = models.BooleanField(default=True, verbose_name="Sucesso")
    error_message = models.TextField(blank=True, verbose_name="Mensagem de Erro")
    
    # Timestamps
    timestamp = models.DateTimeField(default=django_timezone.now, db_index=True, verbose_name="Data/Hora")
    
    # Conformidade LGPD
    is_sensitive_data = models.BooleanField(default=False, verbose_name="Dados Sensíveis")
    retention_period = models.IntegerField(default=2555, verbose_name="Período de Retenção (dias)")  # 7 anos
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        indexes = [
            models.Index(fields=['tenant_id', 'timestamp']),
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} - {self.resource_type} - {self.timestamp}"


class LGPDRequest(models.Model):
    """
    Modelo para rastrear solicitações LGPD (direitos dos titulares).
    """
    
    class RequestType(models.TextChoices):
        ACCESS = 'ACCESS', 'Acesso aos Dados'
        RECTIFICATION = 'RECTIFICATION', 'Retificação'
        DELETION = 'DELETION', 'Exclusão'
        PORTABILITY = 'PORTABILITY', 'Portabilidade'
        OBJECTION = 'OBJECTION', 'Oposição'
        CONSENT_WITHDRAWAL = 'CONSENT_WITHDRAWAL', 'Retirada de Consentimento'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        IN_PROGRESS = 'IN_PROGRESS', 'Em Andamento'
        COMPLETED = 'COMPLETED', 'Concluída'
        REJECTED = 'REJECTED', 'Rejeitada'
        CANCELLED = 'CANCELLED', 'Cancelada'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, verbose_name="ID do Tenant")
    
    # Dados do solicitante
    requester_name = models.CharField(max_length=255, verbose_name="Nome do Solicitante")
    requester_email = models.EmailField(verbose_name="Email do Solicitante")
    requester_document = models.CharField(max_length=20, blank=True, verbose_name="Documento do Solicitante")
    
    # Detalhes da solicitação
    request_type = models.CharField(
        max_length=50,
        choices=RequestType.choices,
        verbose_name="Tipo de Solicitação"
    )
    description = models.TextField(verbose_name="Descrição da Solicitação")
    affected_data_types = models.JSONField(
        default=list,
        verbose_name="Tipos de Dados Afetados",
        help_text="Lista dos tipos de dados pessoais afetados"
    )
    
    # Status e processamento
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status"
    )
    assigned_to = models.UUIDField(null=True, blank=True, verbose_name="Atribuído Para")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    due_date = models.DateTimeField(verbose_name="Data Limite")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Concluído em")
    
    # Resultado
    response_data = models.JSONField(null=True, blank=True, verbose_name="Dados de Resposta")
    rejection_reason = models.TextField(blank=True, verbose_name="Motivo da Rejeição")
    
    # Auditoria
    processing_log = models.JSONField(default=list, verbose_name="Log de Processamento")
    
    class Meta:
        db_table = 'lgpd_requests'
        verbose_name = 'Solicitação LGPD'
        verbose_name_plural = 'Solicitações LGPD'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['requester_email']),
            models.Index(fields=['due_date']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.requester_email}"

    def add_processing_log(self, action: str, user_email: str, details: dict = None):
        """Adiciona entrada no log de processamento"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': action,
            'user_email': user_email,
            'details': details or {}
        }
        self.processing_log.append(log_entry)
        self.save(update_fields=['processing_log', 'updated_at'])


class DataChangeLog(models.Model):
    """
    Modelo para rastrear alterações em dados pessoais.
    Usado para conformidade LGPD e auditoria detalhada.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, verbose_name="ID do Tenant")
    
    # Identificação do registro alterado
    table_name = models.CharField(max_length=100, verbose_name="Nome da Tabela")
    record_id = models.CharField(max_length=100, verbose_name="ID do Registro")
    
    # Detalhes da alteração
    field_name = models.CharField(max_length=100, verbose_name="Nome do Campo")
    old_value = models.TextField(blank=True, verbose_name="Valor Anterior")
    new_value = models.TextField(blank=True, verbose_name="Novo Valor")
    
    # Contexto da alteração
    changed_by = models.UUIDField(verbose_name="Alterado Por")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Alterado em")
    change_reason = models.CharField(max_length=255, blank=True, verbose_name="Motivo da Alteração")
    
    # Classificação dos dados
    is_personal_data = models.BooleanField(default=False, verbose_name="Dados Pessoais")
    is_sensitive_data = models.BooleanField(default=False, verbose_name="Dados Sensíveis")
    data_category = models.CharField(max_length=100, blank=True, verbose_name="Categoria dos Dados")
    
    class Meta:
        db_table = 'data_change_logs'
        verbose_name = 'Log de Alteração de Dados'
        verbose_name_plural = 'Logs de Alteração de Dados'
        indexes = [
            models.Index(fields=['tenant_id', 'changed_at']),
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['changed_by']),
        ]
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.table_name}.{self.field_name} - {self.changed_at}"
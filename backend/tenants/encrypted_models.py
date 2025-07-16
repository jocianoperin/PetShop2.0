"""
Modelos com suporte a criptografia de dados sensíveis por tenant.
"""

from django.db import models
from django.core.exceptions import ValidationError
from .base_models import TenantAwareModel
from .encrypted_fields import (
    EncryptedTextField, EncryptedCharField, EncryptedEmailField,
    EncryptedModelMixin, ConsentTrackingMixin
)
from .encryption import LGPDComplianceManager
import uuid


class EncryptedClienteData(TenantAwareModel, EncryptedModelMixin, ConsentTrackingMixin):
    """
    Modelo para armazenar dados sensíveis criptografados de clientes.
    Separado do modelo principal para maior segurança.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente_id = models.IntegerField(help_text="ID do cliente no modelo principal")
    
    # Campos criptografados (armazenados como texto criptografado)
    cpf_encrypted = models.TextField(
        blank=True, null=True,
        help_text="CPF do cliente (criptografado)"
    )
    rg_encrypted = models.TextField(
        blank=True, null=True,
        help_text="RG do cliente (criptografado)"
    )
    endereco_completo_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Endereço completo do cliente (criptografado)"
    )
    observacoes_pessoais_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Observações pessoais sobre o cliente (criptografado)"
    )
    dados_bancarios_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Dados bancários do cliente (criptografado)"
    )
    
    # Metadados de consentimento
    consent_given_at = models.DateTimeField(null=True, blank=True)
    consent_given_by = models.CharField(max_length=255, blank=True)
    consent_type = models.CharField(
        max_length=20,
        choices=[
            ('explicit', 'Explícito'),
            ('implicit', 'Implícito'),
            ('legitimate', 'Interesse Legítimo')
        ],
        default='explicit'
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'encrypted_cliente_data'
        verbose_name = 'Dados Criptografados do Cliente'
        verbose_name_plural = 'Dados Criptografados dos Clientes'
        unique_together = ['tenant', 'cliente_id']
    
    def __str__(self):
        return f"Dados criptografados - Cliente {self.cliente_id} (Tenant: {self.tenant.name})"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Validar se há consentimento para campos que requerem
        required_consent_fields = ['cpf', 'rg', 'observacoes_pessoais', 'dados_bancarios']
        for field_name in required_consent_fields:
            field_value = getattr(self, field_name, None)
            if field_value and not self.has_consent(field_name):
                if not self.consent_given_at:
                    raise ValidationError(
                        f"Consentimento é obrigatório para o campo {field_name}"
                    )
    
    def save(self, *args, **kwargs):
        """Override save para validações LGPD"""
        # Validar conformidade LGPD antes de salvar
        if not LGPDComplianceManager.validate_data_processing(self, 'save', 'write'):
            raise ValidationError("Processamento de dados não autorizado")
        
        super().save(*args, **kwargs)
    
    def access_data(self, user_id=None):
        """
        Registra acesso aos dados para auditoria.
        
        Args:
            user_id: ID do usuário que está acessando os dados
        """
        from django.utils import timezone
        
        self.last_accessed_at = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed_at', 'access_count'])
        
        # Log de acesso para auditoria
        LGPDComplianceManager.log_data_access(
            tenant_id=str(self.tenant.id),
            user_id=user_id or 'anonymous',
            model_name=self.__class__.__name__,
            field_name='all_encrypted_fields',
            operation='access',
            success=True
        )
    
    # Propriedades para acesso transparente aos dados criptografados
    @property
    def cpf(self):
        """Retorna CPF descriptografado"""
        return self.decrypt_field('cpf')
    
    @cpf.setter
    def cpf(self, value):
        """Define CPF criptografado"""
        self.encrypt_field('cpf', value)
    
    @property
    def rg(self):
        """Retorna RG descriptografado"""
        return self.decrypt_field('rg')
    
    @rg.setter
    def rg(self, value):
        """Define RG criptografado"""
        self.encrypt_field('rg', value)
    
    @property
    def endereco_completo(self):
        """Retorna endereço completo descriptografado"""
        return self.decrypt_field('endereco_completo')
    
    @endereco_completo.setter
    def endereco_completo(self, value):
        """Define endereço completo criptografado"""
        self.encrypt_field('endereco_completo', value)
    
    @property
    def observacoes_pessoais(self):
        """Retorna observações pessoais descriptografadas"""
        return self.decrypt_field('observacoes_pessoais')
    
    @observacoes_pessoais.setter
    def observacoes_pessoais(self, value):
        """Define observações pessoais criptografadas"""
        self.encrypt_field('observacoes_pessoais', value)
    
    @property
    def dados_bancarios(self):
        """Retorna dados bancários descriptografados"""
        return self.decrypt_field('dados_bancarios')
    
    @dados_bancarios.setter
    def dados_bancarios(self, value):
        """Define dados bancários criptografados"""
        self.encrypt_field('dados_bancarios', value)


class EncryptedAnimalData(TenantAwareModel, EncryptedModelMixin, ConsentTrackingMixin):
    """
    Modelo para armazenar dados médicos sensíveis criptografados de animais.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    animal_id = models.IntegerField(help_text="ID do animal no modelo principal")
    
    # Campos criptografados (armazenados como texto criptografado)
    historico_medico_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Histórico médico completo do animal (criptografado)"
    )
    observacoes_veterinario_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Observações do veterinário (criptografado)"
    )
    medicamentos_atuais_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Lista de medicamentos atuais (criptografado)"
    )
    alergias_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Alergias conhecidas do animal (criptografado)"
    )
    condicoes_especiais_encrypted = models.TextField(
        blank=True, null=True,
        help_text="Condições especiais de saúde (criptografado)"
    )
    
    # Metadados de consentimento
    consent_given_at = models.DateTimeField(null=True, blank=True)
    consent_given_by = models.CharField(max_length=255, blank=True)
    veterinario_responsavel = models.CharField(max_length=255, blank=True)
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'encrypted_animal_data'
        verbose_name = 'Dados Médicos Criptografados do Animal'
        verbose_name_plural = 'Dados Médicos Criptografados dos Animais'
        unique_together = ['tenant', 'animal_id']
    
    def __str__(self):
        return f"Dados médicos criptografados - Animal {self.animal_id} (Tenant: {self.tenant.name})"
    
    # Propriedades para acesso transparente aos dados criptografados
    @property
    def historico_medico(self):
        """Retorna histórico médico descriptografado"""
        return self.decrypt_field('historico_medico')
    
    @historico_medico.setter
    def historico_medico(self, value):
        """Define histórico médico criptografado"""
        self.encrypt_field('historico_medico', value)
    
    @property
    def observacoes_veterinario(self):
        """Retorna observações do veterinário descriptografadas"""
        return self.decrypt_field('observacoes_veterinario')
    
    @observacoes_veterinario.setter
    def observacoes_veterinario(self, value):
        """Define observações do veterinário criptografadas"""
        self.encrypt_field('observacoes_veterinario', value)
    
    @property
    def medicamentos_atuais(self):
        """Retorna medicamentos atuais descriptografados"""
        return self.decrypt_field('medicamentos_atuais')
    
    @medicamentos_atuais.setter
    def medicamentos_atuais(self, value):
        """Define medicamentos atuais criptografados"""
        self.encrypt_field('medicamentos_atuais', value)
    
    @property
    def alergias(self):
        """Retorna alergias descriptografadas"""
        return self.decrypt_field('alergias')
    
    @alergias.setter
    def alergias(self, value):
        """Define alergias criptografadas"""
        self.encrypt_field('alergias', value)
    
    @property
    def condicoes_especiais(self):
        """Retorna condições especiais descriptografadas"""
        return self.decrypt_field('condicoes_especiais')
    
    @condicoes_especiais.setter
    def condicoes_especiais(self, value):
        """Define condições especiais criptografadas"""
        self.encrypt_field('condicoes_especiais', value)


class DataProcessingLog(TenantAwareModel):
    """
    Log de processamento de dados pessoais para conformidade LGPD.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identificação
    user_id = models.CharField(max_length=255, blank=True)
    model_name = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=255)
    
    # Operação
    operation = models.CharField(
        max_length=20,
        choices=[
            ('read', 'Leitura'),
            ('write', 'Escrita'),
            ('update', 'Atualização'),
            ('delete', 'Exclusão'),
            ('access', 'Acesso'),
            ('export', 'Exportação')
        ]
    )
    
    # Resultado
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Contexto
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Conformidade LGPD
    legal_basis = models.CharField(
        max_length=50,
        choices=[
            ('consent', 'Consentimento'),
            ('contract', 'Execução de Contrato'),
            ('legal_obligation', 'Obrigação Legal'),
            ('vital_interests', 'Interesses Vitais'),
            ('public_task', 'Tarefa Pública'),
            ('legitimate_interests', 'Interesses Legítimos')
        ],
        default='consent'
    )
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'data_processing_log'
        verbose_name = 'Log de Processamento de Dados'
        verbose_name_plural = 'Logs de Processamento de Dados'
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['tenant', 'user_id', 'timestamp']),
            models.Index(fields=['tenant', 'model_name', 'operation']),
        ]
    
    def __str__(self):
        return f"{self.operation} - {self.model_name}.{self.field_name} by {self.user_id} at {self.timestamp}"


class ConsentRecord(TenantAwareModel):
    """
    Registro de consentimento LGPD por tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identificação do titular dos dados
    data_subject_type = models.CharField(
        max_length=20,
        choices=[
            ('cliente', 'Cliente'),
            ('animal', 'Animal'),
            ('usuario', 'Usuário')
        ]
    )
    data_subject_id = models.CharField(max_length=255)
    
    # Detalhes do consentimento
    purpose = models.TextField(help_text="Finalidade do processamento")
    data_categories = models.JSONField(
        default=list,
        help_text="Categorias de dados pessoais"
    )
    processing_activities = models.JSONField(
        default=list,
        help_text="Atividades de processamento"
    )
    
    # Status do consentimento
    consent_given = models.BooleanField(default=False)
    consent_type = models.CharField(
        max_length=20,
        choices=[
            ('explicit', 'Explícito'),
            ('implicit', 'Implícito'),
            ('legitimate', 'Interesse Legítimo')
        ]
    )
    
    # Metadados
    given_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    given_by = models.CharField(max_length=255, blank=True)
    revoked_by = models.CharField(max_length=255, blank=True)
    
    # Contexto
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'consent_record'
        verbose_name = 'Registro de Consentimento'
        verbose_name_plural = 'Registros de Consentimento'
        unique_together = ['tenant', 'data_subject_type', 'data_subject_id', 'purpose']
    
    def __str__(self):
        status = "Dado" if self.consent_given else "Revogado"
        return f"Consentimento {status} - {self.data_subject_type} {self.data_subject_id}"
    
    def revoke_consent(self, revoked_by=None):
        """Revoga o consentimento"""
        from django.utils import timezone
        
        self.consent_given = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by or 'system'
        self.save()
        
        # Log da revogação
        LGPDComplianceManager.log_data_access(
            tenant_id=str(self.tenant.id),
            user_id=revoked_by or 'system',
            model_name=self.__class__.__name__,
            field_name='consent',
            operation='revoke',
            success=True
        )
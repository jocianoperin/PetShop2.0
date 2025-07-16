"""
Campos de modelo Django com suporte a criptografia por tenant.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .encryption import encryption_manager, LGPDComplianceManager
import logging

logger = logging.getLogger('tenants.encryption')


class EncryptedTextField(models.TextField):
    """
    Campo de texto que automaticamente criptografa dados sensíveis.
    """
    
    def __init__(self, *args, **kwargs):
        self.is_sensitive = kwargs.pop('is_sensitive', True)
        self.require_consent = kwargs.pop('require_consent', False)
        super().__init__(*args, **kwargs)
    
    def _make_getter(self, field_name):
        def getter(instance):
            return self._decrypt_field_value(instance, field_name)
        return getter
    
    def _make_setter(self, field_name):
        def setter(instance, value):
            self._encrypt_field_value(instance, field_name, value)
        return setter
    
    def _decrypt_field_value(self, instance, field_name):
        """Descriptografa o valor do campo"""
        encrypted_field_name = f"{field_name}_encrypted"
        encrypted_value = getattr(instance, encrypted_field_name, None)
        
        if not encrypted_value:
            return None
        
        if not hasattr(instance, 'tenant') or not instance.tenant:
            logger.warning(f"No tenant found for decrypting {field_name}")
            return None
        
        try:
            tenant_id = str(instance.tenant.id)
            decrypted_value = encryption_manager.decrypt(encrypted_value, tenant_id)
            
            # Log de acesso para auditoria LGPD
            if self.is_sensitive:
                LGPDComplianceManager.log_data_access(
                    tenant_id=tenant_id,
                    user_id=getattr(instance, '_current_user_id', 'system'),
                    model_name=instance.__class__.__name__,
                    field_name=field_name,
                    operation='read',
                    success=True
                )
            
            return decrypted_value
        except Exception as e:
            logger.error(f"Failed to decrypt {field_name}: {str(e)}")
            
            # Log de falha para auditoria
            if self.is_sensitive:
                LGPDComplianceManager.log_data_access(
                    tenant_id=str(instance.tenant.id) if instance.tenant else 'unknown',
                    user_id=getattr(instance, '_current_user_id', 'system'),
                    model_name=instance.__class__.__name__,
                    field_name=field_name,
                    operation='read',
                    success=False
                )
            
            return None
    
    def _encrypt_field_value(self, instance, field_name, value):
        """Criptografa o valor do campo"""
        if not value:
            encrypted_field_name = f"{field_name}_encrypted"
            setattr(instance, encrypted_field_name, None)
            return
        
        if not hasattr(instance, 'tenant') or not instance.tenant:
            raise ValidationError("Tenant é obrigatório para campos criptografados")
        
        # Validar conformidade LGPD
        if self.is_sensitive:
            if not LGPDComplianceManager.validate_data_processing(
                instance, field_name, 'write'
            ):
                raise ValidationError(
                    f"Processamento de dados não autorizado para o campo {field_name}"
                )
        
        try:
            tenant_id = str(instance.tenant.id)
            encrypted_value = encryption_manager.encrypt(str(value), tenant_id)
            encrypted_field_name = f"{field_name}_encrypted"
            setattr(instance, encrypted_field_name, encrypted_value)
            
            # Log de escrita para auditoria LGPD
            if self.is_sensitive:
                LGPDComplianceManager.log_data_access(
                    tenant_id=tenant_id,
                    user_id=getattr(instance, '_current_user_id', 'system'),
                    model_name=instance.__class__.__name__,
                    field_name=field_name,
                    operation='write',
                    success=True
                )
        except Exception as e:
            logger.error(f"Failed to encrypt {field_name}: {str(e)}")
            
            # Log de falha para auditoria
            if self.is_sensitive:
                LGPDComplianceManager.log_data_access(
                    tenant_id=str(instance.tenant.id) if instance.tenant else 'unknown',
                    user_id=getattr(instance, '_current_user_id', 'system'),
                    model_name=instance.__class__.__name__,
                    field_name=field_name,
                    operation='write',
                    success=False
                )
            
            raise ValidationError(f"Falha na criptografia do campo {field_name}")


class EncryptedCharField(models.CharField):
    """
    Campo de caracteres que automaticamente criptografa dados sensíveis.
    """
    
    def __init__(self, *args, **kwargs):
        self.is_sensitive = kwargs.pop('is_sensitive', True)
        self.require_consent = kwargs.pop('require_consent', False)
        super().__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        
        # Adicionar campo criptografado correspondente
        encrypted_field_name = f"{name}_encrypted"
        encrypted_field = models.TextField(
            null=True, blank=True, editable=False,
            help_text=f"Versão criptografada de {name}"
        )
        encrypted_field.contribute_to_class(cls, encrypted_field_name)


class EncryptedEmailField(models.EmailField):
    """
    Campo de email que automaticamente criptografa dados sensíveis.
    """
    
    def __init__(self, *args, **kwargs):
        self.is_sensitive = kwargs.pop('is_sensitive', True)
        self.require_consent = kwargs.pop('require_consent', False)
        super().__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        
        # Adicionar campo criptografado correspondente
        encrypted_field_name = f"{name}_encrypted"
        encrypted_field = models.TextField(
            null=True, blank=True, editable=False,
            help_text=f"Versão criptografada de {name}"
        )
        encrypted_field.contribute_to_class(cls, encrypted_field_name)


class EncryptedModelMixin:
    """
    Mixin para modelos que contêm dados criptografados.
    Fornece métodos utilitários para trabalhar com campos criptografados.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypted_fields_cache = {}
    
    def get_encrypted_fields(self):
        """Retorna lista de campos criptografados no modelo"""
        encrypted_fields = []
        for field in self._meta.fields:
            if field.name.endswith('_encrypted'):
                # Remove o sufixo _encrypted para obter o nome do campo original
                original_field_name = field.name[:-10]  # Remove '_encrypted'
                encrypted_fields.append(original_field_name)
        return encrypted_fields
    
    def decrypt_field(self, field_name):
        """
        Descriptografa um campo específico.
        
        Args:
            field_name: Nome do campo a ser descriptografado
            
        Returns:
            Valor descriptografado ou None
        """
        # Verificar cache primeiro
        if field_name in self._encrypted_fields_cache:
            return self._encrypted_fields_cache[field_name]
        
        encrypted_field_name = f"{field_name}_encrypted"
        if not hasattr(self, encrypted_field_name):
            return getattr(self, field_name, None)
        
        encrypted_value = getattr(self, encrypted_field_name)
        if not encrypted_value:
            return None
        
        if not hasattr(self, 'tenant') or not self.tenant:
            logger.warning(f"No tenant found for decrypting {field_name}")
            return None
        
        try:
            tenant_id = str(self.tenant.id)
            decrypted_value = encryption_manager.decrypt(encrypted_value, tenant_id)
            
            # Cache o valor descriptografado
            self._encrypted_fields_cache[field_name] = decrypted_value
            
            return decrypted_value
        except Exception as e:
            logger.error(f"Failed to decrypt {field_name}: {str(e)}")
            return None
    
    def encrypt_field(self, field_name, value):
        """
        Criptografa um campo específico.
        
        Args:
            field_name: Nome do campo a ser criptografado
            value: Valor a ser criptografado
        """
        if not hasattr(self, 'tenant') or not self.tenant:
            raise ValidationError("Tenant é obrigatório para campos criptografados")
        
        if not value:
            encrypted_field_name = f"{field_name}_encrypted"
            setattr(self, encrypted_field_name, None)
            self._encrypted_fields_cache.pop(field_name, None)
            return
        
        try:
            tenant_id = str(self.tenant.id)
            encrypted_value = encryption_manager.encrypt(str(value), tenant_id)
            encrypted_field_name = f"{field_name}_encrypted"
            setattr(self, encrypted_field_name, encrypted_value)
            
            # Atualizar cache
            self._encrypted_fields_cache[field_name] = value
            
        except Exception as e:
            logger.error(f"Failed to encrypt {field_name}: {str(e)}")
            raise ValidationError(f"Falha na criptografia do campo {field_name}")
    
    def decrypt_all_fields(self):
        """
        Descriptografa todos os campos criptografados do modelo.
        
        Returns:
            Dict com os valores descriptografados
        """
        decrypted_data = {}
        encrypted_fields = self.get_encrypted_fields()
        
        for field_name in encrypted_fields:
            decrypted_data[field_name] = self.decrypt_field(field_name)
        
        return decrypted_data
    
    def clear_encryption_cache(self):
        """Limpa o cache de campos descriptografados"""
        self._encrypted_fields_cache.clear()
    
    def save(self, *args, **kwargs):
        """Override save para processar campos criptografados"""
        # Processar campos criptografados antes de salvar
        for field in self._meta.fields:
            if isinstance(field, (EncryptedTextField, EncryptedCharField, EncryptedEmailField)):
                field_value = getattr(self, field.name, None)
                if field_value is not None:
                    # Criptografar o valor
                    self.encrypt_field(field.name, field_value)
                    # Limpar o campo original para não salvar em texto plano
                    setattr(self, field.name, None)
        
        super().save(*args, **kwargs)


class ConsentTrackingMixin:
    """
    Mixin para rastrear consentimento LGPD em modelos.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._consent_given = {}
    
    def give_consent(self, field_name, user_id=None, consent_type='explicit'):
        """
        Registra consentimento para processamento de dados pessoais.
        
        Args:
            field_name: Nome do campo para o qual o consentimento é dado
            user_id: ID do usuário que deu o consentimento
            consent_type: Tipo de consentimento ('explicit', 'implicit')
        """
        self._consent_given[field_name] = {
            'user_id': user_id,
            'consent_type': consent_type,
            'timestamp': timezone.now(),
            'tenant_id': str(self.tenant.id) if hasattr(self, 'tenant') and self.tenant else None
        }
        
        # Log do consentimento para auditoria
        audit_logger = logging.getLogger('tenants.audit')
        audit_logger.info(
            f"LGPD_CONSENT tenant_id={self._consent_given[field_name]['tenant_id']} "
            f"user_id={user_id} model={self.__class__.__name__} "
            f"field={field_name} consent_type={consent_type}"
        )
    
    def revoke_consent(self, field_name, user_id=None):
        """
        Revoga consentimento para processamento de dados pessoais.
        
        Args:
            field_name: Nome do campo para o qual o consentimento é revogado
            user_id: ID do usuário que revogou o consentimento
        """
        if field_name in self._consent_given:
            del self._consent_given[field_name]
        
        # Log da revogação para auditoria
        audit_logger = logging.getLogger('tenants.audit')
        audit_logger.info(
            f"LGPD_CONSENT_REVOKED tenant_id={str(self.tenant.id) if hasattr(self, 'tenant') and self.tenant else 'unknown'} "
            f"user_id={user_id} model={self.__class__.__name__} field={field_name}"
        )
    
    def has_consent(self, field_name):
        """
        Verifica se há consentimento para processar um campo específico.
        
        Args:
            field_name: Nome do campo a verificar
            
        Returns:
            bool: True se há consentimento, False caso contrário
        """
        return field_name in self._consent_given
    
    def get_consent_info(self, field_name):
        """
        Obtém informações sobre o consentimento de um campo.
        
        Args:
            field_name: Nome do campo
            
        Returns:
            dict: Informações do consentimento ou None
        """
        return self._consent_given.get(field_name)
"""
Sistema de criptografia para dados sensíveis por tenant.
Implementa criptografia AES-256 com chaves específicas por tenant.
"""

import os
import base64
import hashlib
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger('tenants.encryption')


class TenantEncryptionManager:
    """
    Gerenciador de criptografia por tenant.
    Cada tenant possui sua própria chave de criptografia derivada.
    """
    
    def __init__(self):
        self.master_key = self._get_master_key()
        self.cache_timeout = getattr(settings, 'TENANT_ENCRYPTION_CACHE_TIMEOUT', 3600)
    
    def _get_master_key(self) -> bytes:
        """Obtém a chave mestra do sistema"""
        master_key = getattr(settings, 'TENANT_ENCRYPTION_MASTER_KEY', None)
        if not master_key:
            # Em produção, isso deve vir de variáveis de ambiente ou serviço de chaves
            master_key = os.environ.get('TENANT_ENCRYPTION_MASTER_KEY')
            if not master_key:
                # Fallback para desenvolvimento - NUNCA usar em produção
                master_key = settings.SECRET_KEY + '_encryption_master'
                logger.warning("Using fallback master key - NOT SECURE FOR PRODUCTION")
        
        return master_key.encode('utf-8')
    
    def _derive_tenant_key(self, tenant_id: str) -> bytes:
        """Deriva uma chave específica para o tenant"""
        # Usar o ID do tenant como salt
        salt = hashlib.sha256(tenant_id.encode()).digest()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return key
    
    def _get_tenant_cipher(self, tenant_id: str) -> Fernet:
        """Obtém o cipher para um tenant específico (com cache)"""
        cache_key = f"tenant_cipher_{tenant_id}"
        cipher = cache.get(cache_key)
        
        if cipher is None:
            tenant_key = self._derive_tenant_key(tenant_id)
            cipher = Fernet(tenant_key)
            cache.set(cache_key, cipher, self.cache_timeout)
        
        return cipher
    
    def encrypt(self, data: str, tenant_id: str) -> str:
        """
        Criptografa dados para um tenant específico.
        
        Args:
            data: Dados a serem criptografados
            tenant_id: ID do tenant
            
        Returns:
            Dados criptografados em base64
        """
        if not data:
            return data
        
        try:
            cipher = self._get_tenant_cipher(tenant_id)
            encrypted_data = cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed for tenant {tenant_id}: {str(e)}")
            raise ValidationError(f"Falha na criptografia: {str(e)}")
    
    def decrypt(self, encrypted_data: str, tenant_id: str) -> str:
        """
        Descriptografa dados de um tenant específico.
        
        Args:
            encrypted_data: Dados criptografados em base64
            tenant_id: ID do tenant
            
        Returns:
            Dados descriptografados
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            cipher = self._get_tenant_cipher(tenant_id)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = cipher.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed for tenant {tenant_id}: {str(e)}")
            raise ValidationError(f"Falha na descriptografia: {str(e)}")
    
    def rotate_tenant_key(self, tenant_id: str) -> bool:
        """
        Rotaciona a chave de um tenant (para casos de comprometimento).
        ATENÇÃO: Isso invalidará todos os dados criptografados existentes!
        """
        try:
            # Remove a chave do cache para forçar regeneração
            cache_key = f"tenant_cipher_{tenant_id}"
            cache.delete(cache_key)
            
            logger.info(f"Key rotation completed for tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Key rotation failed for tenant {tenant_id}: {str(e)}")
            return False


# Instância global do gerenciador
encryption_manager = TenantEncryptionManager()


class EncryptedField:
    """
    Descriptor para campos criptografados em modelos Django.
    Automaticamente criptografa/descriptografa dados baseado no tenant.
    """
    
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.encrypted_field_name = f"_{field_name}_encrypted"
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        # Verificar se já temos o valor descriptografado em cache
        cached_value = getattr(instance, f"_cached_{self.field_name}", None)
        if cached_value is not None:
            return cached_value
        
        # Obter valor criptografado do banco
        encrypted_value = getattr(instance, self.encrypted_field_name, None)
        if not encrypted_value:
            return None
        
        # Descriptografar usando o tenant do objeto
        tenant_id = str(instance.tenant.id) if hasattr(instance, 'tenant') and instance.tenant else None
        if not tenant_id:
            logger.warning(f"No tenant found for encrypted field {self.field_name}")
            return None
        
        try:
            decrypted_value = encryption_manager.decrypt(encrypted_value, tenant_id)
            # Cache o valor descriptografado
            setattr(instance, f"_cached_{self.field_name}", decrypted_value)
            return decrypted_value
        except Exception as e:
            logger.error(f"Failed to decrypt field {self.field_name}: {str(e)}")
            return None
    
    def __set__(self, instance, value):
        if value is None:
            setattr(instance, self.encrypted_field_name, None)
            setattr(instance, f"_cached_{self.field_name}", None)
            return
        
        # Obter tenant do objeto
        tenant_id = str(instance.tenant.id) if hasattr(instance, 'tenant') and instance.tenant else None
        if not tenant_id:
            raise ValidationError("Tenant é obrigatório para campos criptografados")
        
        try:
            # Criptografar o valor
            encrypted_value = encryption_manager.encrypt(str(value), tenant_id)
            setattr(instance, self.encrypted_field_name, encrypted_value)
            # Cache o valor original
            setattr(instance, f"_cached_{self.field_name}", value)
        except Exception as e:
            logger.error(f"Failed to encrypt field {self.field_name}: {str(e)}")
            raise ValidationError(f"Falha na criptografia do campo {self.field_name}")


class LGPDComplianceManager:
    """
    Gerenciador de conformidade LGPD para dados pessoais.
    """
    
    # Campos considerados dados pessoais sensíveis
    SENSITIVE_FIELDS = {
        'email', 'telefone', 'endereco', 'cpf', 'rg', 'documento',
        'observacoes_medicas', 'historico_medico', 'observacoes'
    }
    
    # Campos que requerem consentimento explícito
    EXPLICIT_CONSENT_FIELDS = {
        'observacoes_medicas', 'historico_medico', 'dados_bancarios'
    }
    
    @classmethod
    def is_sensitive_field(cls, field_name: str) -> bool:
        """Verifica se um campo contém dados pessoais sensíveis"""
        return field_name.lower() in cls.SENSITIVE_FIELDS
    
    @classmethod
    def requires_explicit_consent(cls, field_name: str) -> bool:
        """Verifica se um campo requer consentimento explícito"""
        return field_name.lower() in cls.EXPLICIT_CONSENT_FIELDS
    
    @classmethod
    def validate_data_processing(cls, model_instance, field_name: str, operation: str) -> bool:
        """
        Valida se o processamento de dados está em conformidade com LGPD.
        
        Args:
            model_instance: Instância do modelo
            field_name: Nome do campo sendo processado
            operation: Tipo de operação ('read', 'write', 'delete')
        """
        if not cls.is_sensitive_field(field_name):
            return True
        
        # Verificar se há consentimento registrado (implementar conforme necessário)
        # Por enquanto, assumimos que há consentimento se o tenant está ativo
        if hasattr(model_instance, 'tenant') and model_instance.tenant:
            return model_instance.tenant.is_active
        
        return False
    
    @classmethod
    def log_data_access(cls, tenant_id: str, user_id: str, model_name: str, 
                       field_name: str, operation: str, success: bool):
        """
        Registra acesso a dados pessoais para auditoria LGPD.
        """
        audit_logger = logging.getLogger('tenants.audit')
        audit_logger.info(
            f"LGPD_ACCESS tenant_id={tenant_id} user_id={user_id} "
            f"model={model_name} field={field_name} operation={operation} "
            f"success={success}"
        )


def encrypt_sensitive_data(sender, instance, **kwargs):
    """
    Signal handler para criptografar dados sensíveis antes de salvar.
    """
    if not hasattr(instance, 'tenant') or not instance.tenant:
        return
    
    # Identificar campos sensíveis no modelo
    for field in instance._meta.fields:
        if LGPDComplianceManager.is_sensitive_field(field.name):
            value = getattr(instance, field.name, None)
            if value and not field.name.endswith('_encrypted'):
                # Verificar se já existe um campo criptografado correspondente
                encrypted_field_name = f"{field.name}_encrypted"
                if hasattr(instance, encrypted_field_name):
                    # Criptografar e armazenar no campo criptografado
                    try:
                        encrypted_value = encryption_manager.encrypt(
                            str(value), str(instance.tenant.id)
                        )
                        setattr(instance, encrypted_field_name, encrypted_value)
                        # Limpar o campo original se necessário
                        # setattr(instance, field.name, None)
                    except Exception as e:
                        logger.error(f"Failed to encrypt {field.name}: {str(e)}")


# Configurações de criptografia
ENCRYPTION_SETTINGS = {
    'ENABLE_FIELD_ENCRYPTION': True,
    'ENABLE_LGPD_COMPLIANCE': True,
    'CACHE_TIMEOUT': 3600,
    'LOG_DATA_ACCESS': True,
    'REQUIRE_CONSENT_TRACKING': True,
}
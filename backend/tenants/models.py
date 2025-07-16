import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class Tenant(models.Model):
    """
    Modelo para representar um tenant (petshop) no sistema multitenant.
    Cada tenant possui seu próprio schema no banco de dados.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nome do Petshop")
    subdomain = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9-]+$',
                message='Subdomínio deve conter apenas letras minúsculas, números e hífens.'
            )
        ],
        verbose_name="Subdomínio"
    )
    schema_name = models.CharField(
        max_length=63, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9_]+$',
                message='Nome do schema deve conter apenas letras minúsculas, números e underscores.'
            )
        ],
        verbose_name="Nome do Schema"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    plan_type = models.CharField(
        max_length=50, 
        default='basic',
        choices=[
            ('basic', 'Básico'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise')
        ],
        verbose_name="Tipo do Plano"
    )
    max_users = models.IntegerField(default=10, verbose_name="Máximo de Usuários")
    max_animals = models.IntegerField(default=1000, verbose_name="Máximo de Animais")

    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return f"{self.name} ({self.subdomain})"

    def save(self, *args, **kwargs):
        if not self.schema_name:
            # Gera um nome de schema único baseado no subdomain
            self.schema_name = f"tenant_{self.subdomain.replace('-', '_')}"
        super().save(*args, **kwargs)

    def clean(self):
        """Validações customizadas do modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar se subdomain não contém palavras reservadas
        reserved_words = ['admin', 'api', 'www', 'mail', 'ftp', 'localhost', 'test']
        if self.subdomain.lower() in reserved_words:
            raise ValidationError({'subdomain': 'Este subdomínio é reservado e não pode ser usado.'})
        
        # Validar se schema_name não existe
        if self.schema_name and Tenant.objects.filter(schema_name=self.schema_name).exclude(pk=self.pk).exists():
            raise ValidationError({'schema_name': 'Este nome de schema já está em uso.'})


# Import encrypted models to register them with Django
from .encrypted_models import (
    EncryptedClienteData, EncryptedAnimalData, 
    DataProcessingLog, ConsentRecord
)

# Import audit models to register them with Django
from .audit_models import AuditLog, LGPDRequest, DataChangeLog




class TenantUser(models.Model):
    """
    Modelo para usuários vinculados a tenants específicos.
    Estende o sistema de autenticação para suporte multitenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    email = models.EmailField(verbose_name="Email")
    password_hash = models.CharField(max_length=255, verbose_name="Hash da Senha")
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Primeiro Nome")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Último Nome")
    role = models.CharField(
        max_length=50,
        default='user',
        choices=[
            ('admin', 'Administrador'),
            ('manager', 'Gerente'),
            ('user', 'Usuário'),
            ('viewer', 'Visualizador')
        ],
        verbose_name="Função"
    )
    permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Permissões Específicas",
        help_text="Permissões específicas do usuário em formato JSON"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Último Login")

    class Meta:
        db_table = 'tenant_users'
        verbose_name = 'Usuário do Tenant'
        verbose_name_plural = 'Usuários do Tenant'
        unique_together = ['tenant', 'email']

    def __str__(self):
        return f"{self.email} ({self.tenant.name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def has_permission(self, permission_key):
        """Verifica se o usuário tem uma permissão específica"""
        # Verificar permissões baseadas no role
        role_permissions = {
            'admin': ['*'],  # Admin tem todas as permissões
            'manager': ['read', 'write', 'delete'],
            'user': ['read', 'write'],
            'viewer': ['read']
        }
        
        if self.role in role_permissions:
            if '*' in role_permissions[self.role] or permission_key in role_permissions[self.role]:
                return True
        
        # Verificar permissões específicas
        return self.permissions.get(permission_key, False)

    def clean(self):
        """Validações customizadas do modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar se o tenant está ativo
        if self.tenant and not self.tenant.is_active:
            raise ValidationError({'tenant': 'Não é possível criar usuários para tenants inativos.'})


class TenantConfiguration(models.Model):
    """
    Modelo para configurações específicas por tenant.
    Permite personalização individual de cada petshop.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='configurations')
    config_key = models.CharField(max_length=100, verbose_name="Chave de Configuração")
    config_value = models.TextField(blank=True, verbose_name="Valor da Configuração")
    config_type = models.CharField(
        max_length=20,
        default='string',
        choices=[
            ('string', 'Texto'),
            ('integer', 'Número Inteiro'),
            ('float', 'Número Decimal'),
            ('boolean', 'Verdadeiro/Falso'),
            ('json', 'JSON'),
            ('email', 'Email'),
            ('url', 'URL')
        ],
        verbose_name="Tipo da Configuração"
    )
    is_sensitive = models.BooleanField(
        default=False,
        verbose_name="Informação Sensível",
        help_text="Marque se esta configuração contém informações sensíveis (será criptografada)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        db_table = 'tenant_configurations'
        verbose_name = 'Configuração do Tenant'
        verbose_name_plural = 'Configurações do Tenant'
        unique_together = ['tenant', 'config_key']

    def __str__(self):
        return f"{self.tenant.name} - {self.config_key}"

    @classmethod
    def get_config(cls, tenant, key, default=None):
        """Método utilitário para obter configuração de um tenant"""
        try:
            config = cls.objects.get(tenant=tenant, config_key=key)
            return cls._parse_value(config.config_value, config.config_type)
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, tenant, key, value, config_type='string', is_sensitive=False):
        """Método utilitário para definir configuração de um tenant"""
        config_value = cls._serialize_value(value, config_type)
        
        config, created = cls.objects.get_or_create(
            tenant=tenant,
            config_key=key,
            defaults={
                'config_value': config_value,
                'config_type': config_type,
                'is_sensitive': is_sensitive
            }
        )
        if not created:
            config.config_value = config_value
            config.config_type = config_type
            config.is_sensitive = is_sensitive
            config.save()
        return config

    @staticmethod
    def _parse_value(value, config_type):
        """Converte o valor string para o tipo apropriado"""
        if not value:
            return None
            
        if config_type == 'integer':
            return int(value)
        elif config_type == 'float':
            return float(value)
        elif config_type == 'boolean':
            return value.lower() in ('true', '1', 'yes', 'on')
        elif config_type == 'json':
            import json
            return json.loads(value)
        else:
            return value

    @staticmethod
    def _serialize_value(value, config_type):
        """Converte o valor para string para armazenamento"""
        if value is None:
            return ''
            
        if config_type == 'json':
            import json
            return json.dumps(value)
        elif config_type == 'boolean':
            return str(bool(value)).lower()
        else:
            return str(value)

    def clean(self):
        """Validações customizadas do modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar chaves de configuração reservadas
        reserved_keys = ['password', 'secret_key', 'api_key']
        if any(reserved in self.config_key.lower() for reserved in reserved_keys):
            if not self.is_sensitive:
                raise ValidationError({
                    'is_sensitive': 'Configurações com chaves sensíveis devem ser marcadas como sensíveis.'
                })
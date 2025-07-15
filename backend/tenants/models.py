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


class TenantUser(models.Model):
    """
    Modelo para usuários vinculados a tenants específicos.
    Estende o sistema de autenticação para suporte multitenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    email = models.EmailField(unique=True, verbose_name="Email")
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


class TenantConfiguration(models.Model):
    """
    Modelo para configurações específicas por tenant.
    Permite personalização individual de cada petshop.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='configurations')
    config_key = models.CharField(max_length=100, verbose_name="Chave de Configuração")
    config_value = models.TextField(blank=True, verbose_name="Valor da Configuração")
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
            return config.config_value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, tenant, key, value):
        """Método utilitário para definir configuração de um tenant"""
        config, created = cls.objects.get_or_create(
            tenant=tenant,
            config_key=key,
            defaults={'config_value': value}
        )
        if not created:
            config.config_value = value
            config.save()
        return config
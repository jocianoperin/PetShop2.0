"""
Serializers para APIs de tenant e autenticação multitenant.
"""

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator
from .models import Tenant, TenantUser, TenantConfiguration


class TenantRegistrationSerializer(serializers.Serializer):
    """
    Serializer para registro de novos tenants.
    Valida dados de entrada e prepara para provisionamento.
    """
    
    # Dados do petshop/tenant
    name = serializers.CharField(
        max_length=255,
        help_text="Nome do petshop"
    )
    subdomain = serializers.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9-]+$',
                message='Subdomínio deve conter apenas letras minúsculas, números e hífens.'
            )
        ],
        help_text="Subdomínio desejado (ex: meupetshop)"
    )
    
    # Dados do administrador
    admin_email = serializers.EmailField(
        help_text="Email do administrador do petshop"
    )
    admin_password = serializers.CharField(
        min_length=8,
        write_only=True,
        help_text="Senha do administrador (mínimo 8 caracteres)"
    )
    admin_first_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Primeiro nome do administrador"
    )
    admin_last_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Último nome do administrador"
    )
    
    # Configurações opcionais
    plan_type = serializers.ChoiceField(
        choices=[
            ('basic', 'Básico'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise')
        ],
        default='basic',
        required=False,
        help_text="Tipo do plano"
    )
    
    def validate_subdomain(self, value):
        """Validação customizada para subdomínio"""
        value = value.lower().strip()
        
        # Verificar palavras reservadas
        reserved_words = ['admin', 'api', 'www', 'mail', 'ftp', 'localhost', 'test', 'app']
        if value in reserved_words:
            raise serializers.ValidationError(
                "Este subdomínio é reservado e não pode ser usado."
            )
        
        # Verificar se já existe
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError(
                "Este subdomínio já está em uso."
            )
        
        return value
    
    def validate_admin_email(self, value):
        """Validação customizada para email do administrador"""
        value = value.lower().strip()
        
        # Verificar se email já está em uso
        if TenantUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este email já está em uso."
            )
        
        return value
    
    def validate_admin_password(self, value):
        """Validação customizada para senha"""
        if len(value) < 8:
            raise serializers.ValidationError(
                "A senha deve ter pelo menos 8 caracteres."
            )
        
        # Verificar se tem pelo menos uma letra e um número
        has_letter = any(c.isalpha() for c in value)
        has_number = any(c.isdigit() for c in value)
        
        if not (has_letter and has_number):
            raise serializers.ValidationError(
                "A senha deve conter pelo menos uma letra e um número."
            )
        
        return value


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer para modelo Tenant.
    Usado para retornar informações do tenant após criação.
    """
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'created_at', 
            'is_active', 'plan_type', 'max_users', 'max_animals'
        ]
        read_only_fields = ['id', 'created_at']


class TenantUserSerializer(serializers.ModelSerializer):
    """
    Serializer para modelo TenantUser.
    Usado para retornar informações do usuário após criação.
    """
    
    full_name = serializers.ReadOnlyField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_subdomain = serializers.CharField(source='tenant.subdomain', read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'created_at', 'last_login',
            'tenant_name', 'tenant_subdomain'
        ]
        read_only_fields = ['id', 'created_at', 'last_login']


class TenantLoginSerializer(serializers.Serializer):
    """
    Serializer para login multitenant.
    Inclui identificação do tenant além das credenciais.
    """
    
    email = serializers.EmailField(
        help_text="Email do usuário"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Senha do usuário"
    )
    tenant_subdomain = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Subdomínio do tenant (opcional se detectado automaticamente)"
    )
    
    def validate(self, attrs):
        """Validação customizada para login multitenant"""
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password', '')
        tenant_subdomain = attrs.get('tenant_subdomain', '').lower().strip()
        
        if not email or not password:
            raise serializers.ValidationError(
                "Email e senha são obrigatórios."
            )
        
        # Se tenant_subdomain não foi fornecido, será resolvido pelo middleware
        attrs['email'] = email
        if tenant_subdomain:
            attrs['tenant_subdomain'] = tenant_subdomain
        
        return attrs


class TenantJWTTokenSerializer(serializers.Serializer):
    """
    Serializer para tokens JWT com informações de tenant.
    """
    
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    token_type = serializers.CharField(default='Bearer', read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    
    # Informações do usuário
    user = TenantUserSerializer(read_only=True)
    
    # Informações do tenant
    tenant = TenantSerializer(read_only=True)


class TenantConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer para configurações do tenant.
    """
    
    class Meta:
        model = TenantConfiguration
        fields = [
            'id', 'config_key', 'config_value', 'config_type',
            'is_sensitive', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customizar representação para ocultar valores sensíveis"""
        data = super().to_representation(instance)
        
        if instance.is_sensitive:
            data['config_value'] = '***HIDDEN***'
        
        return data


class TenantRegistrationResponseSerializer(serializers.Serializer):
    """
    Serializer para resposta de registro de tenant.
    """
    
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    tenant = TenantSerializer()
    admin_user = TenantUserSerializer()
    login_url = serializers.URLField()
    
    # Informações adicionais
    provisioning_status = serializers.CharField()
    next_steps = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class TenantStatusSerializer(serializers.Serializer):
    """
    Serializer para status de provisionamento do tenant.
    """
    
    tenant = TenantSerializer()
    provisioning_status = serializers.CharField()
    validation = serializers.DictField()
    
    class Meta:
        fields = ['tenant', 'provisioning_status', 'validation']
"""
Autenticação JWT customizada para sistema multitenant.
"""

import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from .models import Tenant, TenantUser
from .utils import set_current_tenant


class TenantJWTAuthentication(JWTAuthentication):
    """
    Autenticação JWT customizada que inclui informações de tenant.
    Estende a autenticação padrão do SimpleJWT para suporte multitenant.
    """
    
    def authenticate(self, request):
        """
        Autentica o usuário e define o tenant no contexto.
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        # Definir tenant no contexto se disponível no token
        tenant = self.get_tenant_from_token(validated_token)
        if tenant:
            set_current_tenant(tenant)
            # Adicionar tenant ao request para acesso fácil
            request.tenant = tenant

        return user, validated_token

    def get_user(self, validated_token):
        """
        Obtém o usuário do tenant a partir do token validado.
        """
        try:
            user_id = validated_token.get('user_id')
            tenant_id = validated_token.get('tenant_id')
            
            if not user_id or not tenant_id:
                # Fallback para autenticação padrão se não houver dados de tenant
                return super().get_user(validated_token)
            
            # Buscar usuário do tenant
            tenant_user = TenantUser.objects.select_related('tenant').get(
                id=user_id,
                tenant_id=tenant_id,
                is_active=True
            )
            
            # Verificar se o tenant está ativo
            if not tenant_user.tenant.is_active:
                raise InvalidToken('Tenant inativo')
            
            # Criar um objeto user-like para compatibilidade com Django
            user = TenantUserProxy(tenant_user)
            return user
            
        except TenantUser.DoesNotExist:
            raise InvalidToken('Usuário não encontrado no tenant')
        except Exception as e:
            raise InvalidToken(f'Erro na autenticação: {str(e)}')

    def get_tenant_from_token(self, validated_token):
        """
        Extrai informações do tenant do token JWT.
        """
        try:
            tenant_id = validated_token.get('tenant_id')
            if tenant_id:
                return Tenant.objects.get(id=tenant_id, is_active=True)
        except Tenant.DoesNotExist:
            pass
        return None


class TenantUserProxy:
    """
    Proxy para TenantUser que implementa a interface esperada pelo Django.
    Permite usar TenantUser com o sistema de autenticação do Django.
    """
    
    def __init__(self, tenant_user):
        self.tenant_user = tenant_user
        self._tenant = tenant_user.tenant
    
    @property
    def id(self):
        return self.tenant_user.id
    
    @property
    def pk(self):
        return self.tenant_user.id
    
    @property
    def username(self):
        return self.tenant_user.email
    
    @property
    def email(self):
        return self.tenant_user.email
    
    @property
    def first_name(self):
        return self.tenant_user.first_name
    
    @property
    def last_name(self):
        return self.tenant_user.last_name
    
    @property
    def is_active(self):
        return self.tenant_user.is_active
    
    @property
    def is_staff(self):
        return self.tenant_user.role in ['admin', 'manager']
    
    @property
    def is_superuser(self):
        return self.tenant_user.role == 'admin'
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    @property
    def tenant(self):
        return self._tenant
    
    @property
    def role(self):
        return self.tenant_user.role
    
    @property
    def permissions(self):
        return self.tenant_user.permissions
    
    def get_full_name(self):
        return self.tenant_user.full_name
    
    def get_short_name(self):
        return self.tenant_user.first_name or self.tenant_user.email
    
    def has_perm(self, perm, obj=None):
        """Verifica se o usuário tem uma permissão específica"""
        if self.tenant_user.role == 'admin':
            return True
        return self.tenant_user.has_permission(perm)
    
    def has_perms(self, perm_list, obj=None):
        """Verifica se o usuário tem todas as permissões da lista"""
        return all(self.has_perm(perm, obj) for perm in perm_list)
    
    def has_module_perms(self, app_label):
        """Verifica se o usuário tem permissões para um módulo"""
        if self.tenant_user.role == 'admin':
            return True
        return self.tenant_user.has_permission(f'{app_label}.*')
    
    def __str__(self):
        return f"{self.tenant_user.email} ({self.tenant_user.tenant.name})"
    
    def __repr__(self):
        return f"<TenantUserProxy: {self.tenant_user.email}>"


class TenantAPIKeyAuthentication:
    """
    Autenticação via API Key específica do tenant.
    Útil para integrações e webhooks.
    """
    
    keyword = 'TenantAPIKey'
    
    def authenticate(self, request):
        """
        Autentica usando API Key do tenant.
        Header: Authorization: TenantAPIKey <tenant_id>:<api_key>
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith(self.keyword):
            return None
        
        try:
            # Extrair token
            token = auth_header.split(' ')[1]
            tenant_id, api_key = token.split(':', 1)
            
            # Buscar tenant
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            
            # Verificar API key (implementar lógica de verificação)
            if self._verify_api_key(tenant, api_key):
                # Criar usuário de sistema para o tenant
                system_user = TenantSystemUser(tenant)
                set_current_tenant(tenant)
                request.tenant = tenant
                return system_user, None
            
        except (ValueError, Tenant.DoesNotExist, IndexError):
            pass
        
        return None
    
    def _verify_api_key(self, tenant, api_key):
        """
        Verifica se a API key é válida para o tenant.
        Implementar lógica de verificação baseada em configurações do tenant.
        """
        from .models import TenantConfiguration
        
        stored_api_key = TenantConfiguration.get_config(tenant, 'api_key')
        return stored_api_key and stored_api_key == api_key


class TenantSystemUser:
    """
    Usuário de sistema para autenticação via API Key.
    Representa operações automatizadas do tenant.
    """
    
    def __init__(self, tenant):
        self._tenant = tenant
        self.id = f"system_{tenant.id}"
        self.pk = self.id
        self.username = f"system@{tenant.subdomain}"
        self.email = f"system@{tenant.subdomain}"
        self.first_name = "System"
        self.last_name = "User"
        self.is_active = True
        self.is_staff = True
        self.is_superuser = True
        self.is_authenticated = True
        self.is_anonymous = False
    
    @property
    def tenant(self):
        return self._tenant
    
    def has_perm(self, perm, obj=None):
        return True
    
    def has_perms(self, perm_list, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True
    
    def get_full_name(self):
        return f"System User ({self._tenant.name})"
    
    def get_short_name(self):
        return "System"
    
    def __str__(self):
        return f"System User ({self._tenant.name})"


def create_tenant_jwt_token(tenant_user):
    """
    Cria um token JWT customizado com informações de tenant.
    
    Args:
        tenant_user: Instância de TenantUser
    
    Returns:
        dict: Tokens de acesso e refresh
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken()
    
    # Claims customizados
    refresh['user_id'] = str(tenant_user.id)
    refresh['email'] = tenant_user.email
    refresh['tenant_id'] = str(tenant_user.tenant.id)
    refresh['tenant_subdomain'] = tenant_user.tenant.subdomain
    refresh['tenant_schema'] = tenant_user.tenant.schema_name
    refresh['user_role'] = tenant_user.role
    refresh['user_permissions'] = tenant_user.permissions
    refresh['tenant_name'] = tenant_user.tenant.name
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def decode_tenant_jwt_token(token):
    """
    Decodifica um token JWT e extrai informações de tenant.
    
    Args:
        token: Token JWT string
    
    Returns:
        dict: Informações decodificadas do token
    """
    try:
        # Decodificar sem verificar assinatura (apenas para extrair claims)
        decoded = jwt.decode(
            token, 
            options={"verify_signature": False}
        )
        
        return {
            'user_id': decoded.get('user_id'),
            'email': decoded.get('email'),
            'tenant_id': decoded.get('tenant_id'),
            'tenant_subdomain': decoded.get('tenant_subdomain'),
            'tenant_schema': decoded.get('tenant_schema'),
            'user_role': decoded.get('user_role'),
            'user_permissions': decoded.get('user_permissions', {}),
            'tenant_name': decoded.get('tenant_name'),
            'exp': decoded.get('exp'),
            'iat': decoded.get('iat'),
        }
    except jwt.DecodeError:
        return None


def validate_tenant_access(user, tenant):
    """
    Valida se um usuário tem acesso a um tenant específico.
    
    Args:
        user: Usuário (TenantUserProxy ou similar)
        tenant: Instância de Tenant
    
    Returns:
        bool: True se o usuário tem acesso ao tenant
    """
    if hasattr(user, 'tenant_user'):
        return user.tenant_user.tenant.id == tenant.id
    elif hasattr(user, 'tenant'):
        return user.tenant.id == tenant.id
    return False
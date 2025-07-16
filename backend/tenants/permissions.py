"""
Permissões customizadas para sistema multitenant.
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .utils import get_current_tenant
from .models import TenantUser


class TenantPermission(BasePermission):
    """
    Permissão base que requer um tenant válido.
    """
    
    def has_permission(self, request, view):
        """
        Verifica se o request tem um tenant válido.
        """
        tenant = get_current_tenant()
        if not tenant:
            return False
        
        # Verificar se o tenant está ativo
        if not tenant.is_active:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica permissões específicas do objeto.
        """
        return self.has_permission(request, view)


class TenantUserPermission(TenantPermission):
    """
    Permissão que requer um usuário autenticado do tenant.
    """
    
    def has_permission(self, request, view):
        """
        Verifica se o usuário está autenticado e pertence ao tenant.
        """
        if not super().has_permission(request, view):
            return False
        
        # Verificar se o usuário está autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar se é um TenantUserProxy
        if hasattr(request.user, 'tenant_user'):
            tenant = get_current_tenant()
            return request.user.tenant_user.tenant.id == tenant.id
        
        return False


class TenantAdminPermission(TenantUserPermission):
    """
    Permissão que requer um usuário administrador do tenant.
    """
    
    def has_permission(self, request, view):
        """
        Verifica se o usuário é administrador do tenant.
        """
        if not super().has_permission(request, view):
            return False
        
        # Verificar se o usuário é admin ou manager
        if hasattr(request.user, 'tenant_user'):
            return request.user.tenant_user.role in ['admin', 'manager']
        
        return False


class TenantOwnerPermission(TenantUserPermission):
    """
    Permissão que requer que o usuário seja o proprietário do tenant.
    """
    
    def has_permission(self, request, view):
        """
        Verifica se o usuário é o proprietário (admin) do tenant.
        """
        if not super().has_permission(request, view):
            return False
        
        # Verificar se o usuário é admin
        if hasattr(request.user, 'tenant_user'):
            return request.user.tenant_user.role == 'admin'
        
        return False


class TenantResourcePermission(TenantUserPermission):
    """
    Permissão para recursos específicos do tenant.
    Verifica se o usuário tem permissão para acessar um recurso específico.
    """
    
    # Mapeamento de ações para permissões
    action_permissions = {
        'list': 'read',
        'retrieve': 'read',
        'create': 'write',
        'update': 'write',
        'partial_update': 'write',
        'destroy': 'delete',
    }
    
    def has_permission(self, request, view):
        """
        Verifica permissões baseadas na ação da view.
        """
        if not super().has_permission(request, view):
            return False
        
        # Obter a ação da view
        action = getattr(view, 'action', None)
        if not action:
            return True  # Permitir se não há ação específica
        
        # Mapear ação para permissão
        required_permission = self.action_permissions.get(action, 'read')
        
        # Verificar se o usuário tem a permissão
        if hasattr(request.user, 'tenant_user'):
            return request.user.tenant_user.has_permission(required_permission)
        
        return False


class TenantDataIsolationPermission(TenantUserPermission):
    """
    Permissão que garante isolamento de dados por tenant.
    Verifica se o objeto pertence ao tenant atual.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica se o objeto pertence ao tenant atual.
        """
        if not super().has_permission(request, view):
            return False
        
        tenant = get_current_tenant()
        
        # Verificar se o objeto tem um campo tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant.id == tenant.id
        
        # Verificar se o objeto é tenant-aware através de relacionamentos
        if hasattr(obj, 'cliente') and hasattr(obj.cliente, 'tenant'):
            return obj.cliente.tenant.id == tenant.id
        
        # Para objetos que não têm tenant direto, assumir que pertencem ao tenant atual
        # (isso deve ser validado pelo TenantAwareManager)
        return True


class TenantAPIKeyPermission(BasePermission):
    """
    Permissão para autenticação via API Key do tenant.
    """
    
    def has_permission(self, request, view):
        """
        Verifica se a requisição tem uma API Key válida do tenant.
        """
        # Verificar se há um tenant no contexto
        tenant = get_current_tenant()
        if not tenant:
            return False
        
        # Verificar se o usuário é um TenantSystemUser (autenticado via API Key)
        if hasattr(request.user, 'tenant') and request.user.username.startswith('system@'):
            return request.user.tenant.id == tenant.id
        
        return False


class TenantPlanPermission(TenantUserPermission):
    """
    Permissão baseada no plano do tenant.
    """
    
    # Limites por plano
    plan_limits = {
        'basic': {
            'max_users': 5,
            'max_animals': 100,
            'max_products': 50,
            'features': ['basic_reports', 'customer_management']
        },
        'premium': {
            'max_users': 20,
            'max_animals': 1000,
            'max_products': 500,
            'features': ['advanced_reports', 'inventory_management', 'scheduling']
        },
        'enterprise': {
            'max_users': -1,  # Ilimitado
            'max_animals': -1,
            'max_products': -1,
            'features': ['all_features', 'api_access', 'custom_integrations']
        }
    }
    
    def has_permission(self, request, view):
        """
        Verifica se o tenant tem permissão baseada no plano.
        """
        if not super().has_permission(request, view):
            return False
        
        tenant = get_current_tenant()
        plan_type = tenant.plan_type
        
        # Verificar se o plano existe
        if plan_type not in self.plan_limits:
            return False
        
        # Verificar limites específicos baseados na view
        return self._check_plan_limits(request, view, tenant, plan_type)
    
    def _check_plan_limits(self, request, view, tenant, plan_type):
        """
        Verifica limites específicos do plano.
        """
        limits = self.plan_limits[plan_type]
        
        # Verificar limite de usuários
        if hasattr(view, 'model') and view.model == TenantUser:
            if request.method == 'POST':  # Criação de usuário
                current_users = TenantUser.objects.filter(tenant=tenant, is_active=True).count()
                max_users = limits['max_users']
                if max_users > 0 and current_users >= max_users:
                    raise PermissionDenied(f"Limite de usuários atingido para o plano {plan_type}")
        
        # Verificar recursos específicos
        required_feature = getattr(view, 'required_feature', None)
        if required_feature:
            if required_feature not in limits['features'] and 'all_features' not in limits['features']:
                raise PermissionDenied(f"Recurso '{required_feature}' não disponível no plano {plan_type}")
        
        return True


class TenantReadOnlyPermission(TenantUserPermission):
    """
    Permissão somente leitura para usuários do tenant.
    """
    
    def has_permission(self, request, view):
        """
        Permite apenas operações de leitura.
        """
        if not super().has_permission(request, view):
            return False
        
        # Permitir apenas métodos de leitura
        return request.method in ['GET', 'HEAD', 'OPTIONS']


class TenantCustomPermission(TenantUserPermission):
    """
    Permissão customizável baseada em configurações do tenant.
    """
    
    def has_permission(self, request, view):
        """
        Verifica permissões customizadas do tenant.
        """
        if not super().has_permission(request, view):
            return False
        
        tenant = get_current_tenant()
        
        # Obter configurações de permissão do tenant
        from .models import TenantConfiguration
        
        permission_config = TenantConfiguration.get_config(
            tenant, 
            'custom_permissions', 
            default={}
        )
        
        # Verificar permissões específicas da view
        view_name = getattr(view, '__class__.__name__', '')
        view_permissions = permission_config.get(view_name, {})
        
        # Verificar se o usuário tem as permissões necessárias
        user_role = request.user.tenant_user.role
        allowed_roles = view_permissions.get('allowed_roles', ['admin', 'manager', 'user'])
        
        return user_role in allowed_roles


# Decorators para views baseadas em função
def tenant_required(view_func):
    """
    Decorator que requer um tenant válido.
    """
    def wrapper(request, *args, **kwargs):
        permission = TenantPermission()
        if not permission.has_permission(request, None):
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Tenant requerido',
                'code': 'TENANT_REQUIRED'
            }, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_user_required(view_func):
    """
    Decorator que requer um usuário autenticado do tenant.
    """
    def wrapper(request, *args, **kwargs):
        permission = TenantUserPermission()
        if not permission.has_permission(request, None):
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Usuário do tenant requerido',
                'code': 'TENANT_USER_REQUIRED'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_admin_required(view_func):
    """
    Decorator que requer um administrador do tenant.
    """
    def wrapper(request, *args, **kwargs):
        permission = TenantAdminPermission()
        if not permission.has_permission(request, None):
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Permissões de administrador requeridas',
                'code': 'TENANT_ADMIN_REQUIRED'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_plan_required(required_plan):
    """
    Decorator que requer um plano específico do tenant.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            tenant = get_current_tenant()
            if not tenant or tenant.plan_type != required_plan:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': f'Plano {required_plan} requerido',
                    'code': 'TENANT_PLAN_REQUIRED'
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def tenant_feature_required(feature_name):
    """
    Decorator que requer um recurso específico do plano do tenant.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            permission = TenantPlanPermission()
            # Simular uma view com required_feature
            class MockView:
                required_feature = feature_name
            
            mock_view = MockView()
            if not permission._check_plan_limits(request, mock_view, get_current_tenant(), get_current_tenant().plan_type):
                from django.http import JsonResponse
                return JsonResponse({
                    'error': f'Recurso {feature_name} não disponível no seu plano',
                    'code': 'FEATURE_NOT_AVAILABLE'
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
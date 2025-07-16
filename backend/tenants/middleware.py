import threading
import jwt
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Tenant
from .utils import get_current_tenant, set_current_tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware para resolução automática de tenant baseado em:
    1. Subdomínio (tenant.exemplo.com)
    2. Header X-Tenant-ID
    3. Token JWT (tenant_id ou tenant_subdomain no payload)
    4. Parâmetro de query (apenas desenvolvimento)
    """

    def process_request(self, request):
        tenant = None
        
        try:
            # Método 1: Resolução via subdomínio
            tenant = self._resolve_by_subdomain(request)
            
            # Método 2: Fallback para header X-Tenant-ID
            if not tenant:
                tenant = self._resolve_by_header(request)
            
            # Método 3: Fallback para JWT token
            if not tenant:
                tenant = self._resolve_by_jwt_token(request)
            
            # Método 4: Fallback para parâmetro de query (desenvolvimento)
            if not tenant:
                tenant = self._resolve_by_query_param(request)
            
            if tenant:
                # Define o tenant atual no contexto da thread
                set_current_tenant(tenant)
                request.tenant = tenant
                
                # Configura a conexão do banco para o schema do tenant
                self._set_tenant_schema(tenant)
            else:
                # Para endpoints que não requerem tenant (registro, etc.)
                if self._is_tenant_required(request):
                    return JsonResponse({
                        'error': 'Tenant não identificado',
                        'code': 'TENANT_NOT_FOUND'
                    }, status=400)
                    
        except Tenant.DoesNotExist:
            # Log do erro para debugging
            import logging
            logger = logging.getLogger('tenants')
            logger.warning(f'Tenant não encontrado para request: {request.get_host()}{request.path}')
            
            return JsonResponse({
                'error': 'Tenant não encontrado',
                'code': 'TENANT_NOT_FOUND',
                'details': 'O tenant especificado não existe ou está inativo'
            }, status=404)
        except Exception as e:
            # Log do erro para debugging
            import logging
            logger = logging.getLogger('tenants')
            logger.error(f'Erro na resolução do tenant: {str(e)}', exc_info=True)
            
            return JsonResponse({
                'error': 'Erro na resolução do tenant',
                'code': 'TENANT_RESOLUTION_ERROR',
                'details': 'Erro interno do servidor ao identificar o tenant'
            }, status=500)

    def process_response(self, request, response):
        # Limpa o contexto do tenant após o processamento
        set_current_tenant(None)
        return response

    def _resolve_by_subdomain(self, request):
        """Resolve tenant pelo subdomínio"""
        host = request.get_host()
        
        # Remove porta se presente
        if ':' in host:
            host = host.split(':')[0]
        
        # Extrai subdomínio (assume formato: subdomain.domain.com)
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.domain.com
            subdomain = parts[0]
            if subdomain != 'www':  # Ignora www
                try:
                    return Tenant.objects.get(subdomain=subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    pass
        
        return None

    def _resolve_by_header(self, request):
        """Resolve tenant pelo header X-Tenant-ID"""
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                pass
        
        return None

    def _resolve_by_jwt_token(self, request):
        """Resolve tenant pelo JWT token"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Valida o token JWT usando django-rest-framework-simplejwt
            UntypedToken(token)
            
            # Decodifica o token para extrair o tenant_id
            decoded_token = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256'],
                options={"verify_signature": False}  # Já validado pelo UntypedToken
            )
            
            # Procura por tenant_id no payload do token
            tenant_id = decoded_token.get('tenant_id')
            if tenant_id:
                try:
                    return Tenant.objects.get(id=tenant_id, is_active=True)
                except (Tenant.DoesNotExist, ValueError):
                    pass
            
            # Fallback: procura por tenant_subdomain no payload
            tenant_subdomain = decoded_token.get('tenant_subdomain')
            if tenant_subdomain:
                try:
                    return Tenant.objects.get(subdomain=tenant_subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    pass
                    
        except (InvalidToken, TokenError, jwt.DecodeError, jwt.InvalidTokenError):
            # Token inválido ou expirado - não retorna erro, apenas None
            pass
        except Exception:
            # Outros erros - não retorna erro, apenas None
            pass
        
        return None

    def _resolve_by_query_param(self, request):
        """Resolve tenant pelo parâmetro de query (apenas para desenvolvimento)"""
        tenant_param = request.GET.get('tenant')
        if tenant_param:
            try:
                # Pode ser ID ou subdomínio
                if len(tenant_param) == 36:  # UUID
                    return Tenant.objects.get(id=tenant_param, is_active=True)
                else:  # Subdomínio
                    return Tenant.objects.get(subdomain=tenant_param, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                pass
        
        return None

    def _set_tenant_schema(self, tenant):
        """Configura o schema do banco para o tenant atual"""
        # Para PostgreSQL, define o search_path para o schema do tenant
        from .utils import _is_postgresql
        if _is_postgresql():
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant.schema_name}, public")

    def _is_tenant_required(self, request):
        """Verifica se o endpoint atual requer identificação de tenant"""
        # Endpoints que não requerem tenant
        exempt_paths = [
            '/api/tenants/register/',
            '/api/auth/login/',
            '/api/health/',
            '/admin/',
            '/api/docs/',
        ]
        
        path = request.path
        return not any(path.startswith(exempt_path) for exempt_path in exempt_paths)


class TenantSchemaMiddleware(MiddlewareMixin):
    """
    Middleware adicional para garantir que todas as queries
    sejam executadas no schema correto do tenant.
    """
    
    def process_request(self, request):
        tenant = getattr(request, 'tenant', None)
        if tenant:
            # Força o uso do schema correto para todas as operações de banco
            self._ensure_tenant_schema(tenant)

    def _ensure_tenant_schema(self, tenant):
        """Garante que o schema correto está sendo usado"""
        from .utils import _is_postgresql
        
        # Apenas para PostgreSQL
        if not _is_postgresql():
            return
            
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_schema()")
                current_schema = cursor.fetchone()[0]
                
                if current_schema != tenant.schema_name:
                    cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
        except Exception:
            # Em caso de erro, define o schema novamente
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
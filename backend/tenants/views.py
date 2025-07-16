"""
Views para APIs de tenant e autenticação multitenant.
"""

import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Tenant, TenantUser
from .serializers import (
    TenantRegistrationSerializer,
    TenantRegistrationResponseSerializer,
    TenantLoginSerializer,
    TenantJWTTokenSerializer,
    TenantStatusSerializer
)
from .services import tenant_provisioning_service, TenantProvisioningError
from .utils import get_current_tenant, resolve_tenant_from_request
from .authentication import create_tenant_jwt_token


logger = logging.getLogger('tenants.views')


class TenantRegistrationView(APIView):
    """
    API para registro de novos tenants.
    
    POST /api/tenants/register
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Registra um novo tenant com provisionamento automático.
        """
        serializer = TenantRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Dados de registro inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extrair dados validados
            tenant_data = serializer.validated_data
            
            logger.info(f"Starting tenant registration for: {tenant_data['name']}")
            
            # Criar tenant usando o serviço de provisionamento
            tenant = tenant_provisioning_service.create_tenant(tenant_data)
            
            # Buscar usuário administrador criado
            admin_user = TenantUser.objects.get(
                tenant=tenant,
                email=tenant_data['admin_email'],
                role='admin'
            )
            
            # Construir URL de login
            base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
            login_url = f"{base_url.rstrip('/')}/login?tenant={tenant.subdomain}"
            
            # Preparar resposta
            response_data = {
                'success': True,
                'message': f'Petshop "{tenant.name}" registrado com sucesso!',
                'tenant': tenant,
                'admin_user': admin_user,
                'login_url': login_url,
                'provisioning_status': 'complete',
                'next_steps': [
                    'Acesse o link de login fornecido',
                    'Faça login com suas credenciais',
                    'Complete a configuração do seu petshop',
                    'Comece a cadastrar seus clientes e serviços'
                ]
            }
            
            response_serializer = TenantRegistrationResponseSerializer(response_data)
            
            logger.info(f"Tenant registration completed successfully: {tenant.name} ({tenant.id})")
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except TenantProvisioningError as e:
            logger.error(f"Tenant provisioning failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro no provisionamento do tenant',
                'error': str(e),
                'error_type': 'provisioning_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Unexpected error during tenant registration: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': 'Ocorreu um erro inesperado durante o registro',
                'error_type': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TenantLoginView(APIView):
    """
    API para login multitenant.
    
    POST /api/tenants/login
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Autentica usuário em um tenant específico.
        """
        serializer = TenantLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Dados de login inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validated_data = serializer.validated_data
            email = validated_data['email']
            password = validated_data['password']
            tenant_subdomain = validated_data.get('tenant_subdomain')
            
            # Resolver tenant
            tenant = None
            if tenant_subdomain:
                try:
                    tenant = Tenant.objects.get(subdomain=tenant_subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Tenant não encontrado ou inativo',
                        'error_type': 'tenant_not_found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Tentar resolver tenant do request (middleware)
                tenant = resolve_tenant_from_request(request)
                if not tenant:
                    return Response({
                        'success': False,
                        'message': 'Não foi possível identificar o tenant',
                        'error_type': 'tenant_resolution_failed'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Buscar usuário no tenant
            try:
                user = TenantUser.objects.get(
                    tenant=tenant,
                    email=email,
                    is_active=True
                )
            except TenantUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Credenciais inválidas',
                    'error_type': 'invalid_credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verificar senha
            if not check_password(password, user.password_hash):
                return Response({
                    'success': False,
                    'message': 'Credenciais inválidas',
                    'error_type': 'invalid_credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Gerar tokens JWT usando função centralizada
            tokens = create_tenant_jwt_token(user)
            
            # Atualizar último login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Preparar resposta
            response_data = {
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'token_type': 'Bearer',
                'expires_in': int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                'user': user,
                'tenant': tenant
            }
            
            response_serializer = TenantJWTTokenSerializer(response_data)
            
            logger.info(f"Successful login for user {email} in tenant {tenant.name}")
            
            return Response({
                'success': True,
                'message': 'Login realizado com sucesso',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error during tenant login: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error_type': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class TenantStatusView(APIView):
    """
    API para verificar status de provisionamento do tenant.
    
    GET /api/tenants/status/{tenant_id_or_subdomain}
    """
    
    permission_classes = [AllowAny]  # Pode ser chamado durante o processo de registro
    
    def get(self, request, tenant_identifier):
        """
        Retorna status de provisionamento do tenant.
        """
        try:
            status_data = tenant_provisioning_service.get_provisioning_status(tenant_identifier)
            
            if 'error' in status_data:
                return Response({
                    'success': False,
                    'message': status_data['error']
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = TenantStatusSerializer(status_data)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting tenant status: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Erro ao obter status do tenant'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_subdomain_availability(request):
    """
    Verifica disponibilidade de subdomínio.
    
    POST /api/tenants/check-subdomain
    Body: {"subdomain": "meusubdominio"}
    """
    subdomain = request.data.get('subdomain', '').lower().strip()
    
    if not subdomain:
        return Response({
            'success': False,
            'message': 'Subdomínio é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar formato
    import re
    if not re.match(r'^[a-z0-9-]+$', subdomain):
        return Response({
            'available': False,
            'message': 'Subdomínio deve conter apenas letras minúsculas, números e hífens'
        }, status=status.HTTP_200_OK)
    
    # Verificar palavras reservadas
    reserved_words = ['admin', 'api', 'www', 'mail', 'ftp', 'localhost', 'test', 'app']
    if subdomain in reserved_words:
        return Response({
            'available': False,
            'message': 'Este subdomínio é reservado e não pode ser usado'
        }, status=status.HTTP_200_OK)
    
    # Verificar se já existe
    exists = Tenant.objects.filter(subdomain=subdomain).exists()
    
    return Response({
        'available': not exists,
        'subdomain': subdomain,
        'message': 'Subdomínio disponível' if not exists else 'Subdomínio já está em uso'
    }, status=status.HTTP_200_OK)


class TenantRefreshTokenView(TokenObtainPairView):
    """
    View customizada para refresh de tokens com informações de tenant.
    
    POST /api/tenants/token/refresh
    """
    
    def post(self, request, *args, **kwargs):
        """
        Refresh token com validação de tenant.
        """
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Adicionar informações de tenant na resposta se disponível
                tenant = get_current_tenant()
                if tenant:
                    response.data['tenant'] = {
                        'id': str(tenant.id),
                        'name': tenant.name,
                        'subdomain': tenant.subdomain
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"Error refreshing tenant token: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Erro ao renovar token'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tenant_logout(request):
    """
    Logout do usuário com invalidação de token.
    
    POST /api/tenants/logout
    """
    try:
        # Obter refresh token do request
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                logger.warning(f"Failed to blacklist token: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Logout realizado com sucesso'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Erro durante logout'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
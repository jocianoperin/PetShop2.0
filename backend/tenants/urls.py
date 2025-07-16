"""
URLs para APIs de tenant e autenticação multitenant.
"""

from django.urls import path
from .views import (
    TenantRegistrationView,
    TenantLoginView,
    TenantStatusView,
    TenantRefreshTokenView,
    check_subdomain_availability,
    tenant_logout
)

app_name = 'tenants'

urlpatterns = [
    # Registro de tenant
    path('register/', TenantRegistrationView.as_view(), name='tenant-register'),
    
    # Verificação de disponibilidade de subdomínio
    path('check-subdomain/', check_subdomain_availability, name='check-subdomain'),
    
    # Status de provisionamento
    path('status/<str:tenant_identifier>/', TenantStatusView.as_view(), name='tenant-status'),
    
    # Autenticação multitenant
    path('login/', TenantLoginView.as_view(), name='tenant-login'),
    path('logout/', tenant_logout, name='tenant-logout'),
    path('token/refresh/', TenantRefreshTokenView.as_view(), name='tenant-token-refresh'),
]
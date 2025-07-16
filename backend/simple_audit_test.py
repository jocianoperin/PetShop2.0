#!/usr/bin/env python
"""
Teste simples do sistema de auditoria sem usar signals de login.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from django.contrib.auth.models import User
from tenants.models import Tenant
from tenants.audit_models import AuditLog, AuditEventType
from tenants.audit_signals import log_audit_event
from tenants.utils import set_current_tenant


def test_audit_system():
    """Testar sistema de auditoria básico"""
    print("=== Teste Simples do Sistema de Auditoria ===")
    
    # Criar ou obter tenant de teste
    tenant, created = Tenant.objects.get_or_create(
        subdomain="simpletest",
        defaults={
            'name': "Simple Test Petshop",
            'schema_name': "simpletest_schema"
        }
    )
    print(f"Tenant: {tenant.name} ({'criado' if created else 'existente'})")
    
    # Criar ou obter usuário de teste
    user, created = User.objects.get_or_create(
        username='simpletest',
        defaults={
            'email': 'simpletest@example.com'
        }
    )
    print(f"Usuário: {user.username} ({'criado' if created else 'existente'})")
    
    # Configurar tenant atual
    set_current_tenant(tenant)
    
    # Testar log de auditoria básico
    print("\nTestando log de auditoria...")
    
    try:
        audit_log = log_audit_event(
            event_type=AuditEventType.READ,
            resource_type='Cliente',
            action='read',
            user=user,
            resource_id='123',
            metadata={'test': 'simple_test'},
            is_sensitive_data=True
        )
        
        if audit_log:
            print(f"✓ Log de auditoria criado: {audit_log.id}")
            print(f"  - Tenant: {audit_log.tenant_id}")
            print(f"  - Usuário: {audit_log.user_email}")
            print(f"  - Evento: {audit_log.event_type}")
            print(f"  - Recurso: {audit_log.resource_type}")
            print(f"  - Método HTTP: {audit_log.request_method}")
        else:
            print("✗ Falha ao criar log de auditoria")
            
    except Exception as e:
        print(f"✗ Erro ao criar log de auditoria: {e}")
    
    # Verificar logs existentes
    print(f"\nTotal de logs de auditoria para o tenant: {AuditLog.objects.filter(tenant_id=tenant.id).count()}")
    
    # Testar API de auditoria sem login
    print("\nTestando API de auditoria...")
    
    from django.test import Client
    from django.urls import reverse
    
    client = Client()
    
    # Testar endpoint sem autenticação (deve falhar)
    try:
        response = client.get('/api/tenants/audit/logs/')
        print(f"GET /api/tenants/audit/logs/ (sem auth) - Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✓ Autenticação necessária (esperado)")
        elif response.status_code == 403:
            print("✓ Acesso negado (esperado)")
        else:
            print(f"? Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Erro ao testar API: {e}")
    
    print("\n=== Teste Concluído ===")


if __name__ == '__main__':
    test_audit_system()
#!/usr/bin/env python
"""
Script para testar as APIs de auditoria e conformidade LGPD.
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from tenants.models import Tenant, TenantUser
from tenants.audit_models import AuditLog, LGPDRequest, AuditEventType
from tenants.audit_signals import log_audit_event
from tenants.utils import set_current_tenant


def setup_test_data():
    """Configurar dados de teste"""
    print("Configurando dados de teste...")
    
    # Criar ou obter tenant de teste
    tenant, created = Tenant.objects.get_or_create(
        subdomain="testapi",
        defaults={
            'name': "Test Petshop API",
            'schema_name': "testapi_schema"
        }
    )
    
    # Criar ou obter usuário de teste
    user, created = User.objects.get_or_create(
        username='testapi',
        defaults={
            'email': 'testapi@example.com',
            'password': 'testpass123'
        }
    )
    
    # Configurar tenant atual
    set_current_tenant(tenant)
    
    # Criar alguns logs de auditoria
    for i in range(5):
        log_audit_event(
            event_type=AuditEventType.READ,
            resource_type='Cliente',
            action='read',
            user=user,
            resource_id=str(i),
            is_sensitive_data=True
        )
    
    # Criar solicitação LGPD
    lgpd_request = LGPDRequest.objects.create(
        tenant_id=tenant.id,
        requester_name="João Silva",
        requester_email="joao@example.com",
        request_type=LGPDRequest.RequestType.ACCESS,
        description="Solicito acesso aos meus dados pessoais",
        due_date=timezone.now() + timedelta(days=15)
    )
    
    print(f"Tenant criado: {tenant.id}")
    print(f"Usuário criado: {user.username}")
    print(f"Logs de auditoria criados: {AuditLog.objects.filter(tenant_id=tenant.id).count()}")
    print(f"Solicitação LGPD criada: {lgpd_request.id}")
    
    return tenant, user


def test_audit_logs_api(client, user):
    """Testar API de logs de auditoria"""
    print("\n=== Testando API de Logs de Auditoria ===")
    
    # Login
    client.force_login(user)
    
    # Testar listagem de logs
    response = client.get('/api/tenants/audit/logs/')
    print(f"GET /api/tenants/audit/logs/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total de logs: {data.get('count', 0)}")
        print(f"Logs retornados: {len(data.get('results', []))}")
    else:
        print(f"Erro: {response.content.decode()}")
    
    # Testar estatísticas
    response = client.get('/api/tenants/audit/logs/statistics/')
    print(f"GET /api/tenants/audit/logs/statistics/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total de eventos: {data.get('total_events', 0)}")
        print(f"Eventos recentes: {data.get('recent_events', 0)}")
    else:
        print(f"Erro: {response.content.decode()}")


def test_lgpd_requests_api(client, user):
    """Testar API de solicitações LGPD"""
    print("\n=== Testando API de Solicitações LGPD ===")
    
    # Testar listagem de solicitações
    response = client.get('/api/tenants/audit/lgpd-requests/')
    print(f"GET /api/tenants/audit/lgpd-requests/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total de solicitações: {data.get('count', 0)}")
        print(f"Solicitações retornadas: {len(data.get('results', []))}")
    else:
        print(f"Erro: {response.content.decode()}")
    
    # Testar criação de nova solicitação
    new_request_data = {
        'requester_name': 'Maria Silva',
        'requester_email': 'maria@example.com',
        'request_type': 'DELETION',
        'description': 'Solicito exclusão dos meus dados',
        'affected_data_types': ['nome', 'email', 'telefone']
    }
    
    response = client.post(
        '/api/tenants/audit/lgpd-requests/',
        data=json.dumps(new_request_data),
        content_type='application/json'
    )
    print(f"POST /api/tenants/audit/lgpd-requests/ - Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"Nova solicitação criada: {data.get('id')}")
        print(f"Status: {data.get('status')}")
    else:
        print(f"Erro: {response.content.decode()}")


def test_compliance_reports_api(client, user):
    """Testar API de relatórios de conformidade"""
    print("\n=== Testando API de Relatórios de Conformidade ===")
    
    # Testar verificação rápida de conformidade
    response = client.get('/api/tenants/audit/compliance/quick-check/')
    print(f"GET /api/tenants/audit/compliance/quick-check/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Pontuação de conformidade: {data.get('compliance_score')}")
        print(f"Nível de conformidade: {data.get('compliance_level')}")
        print(f"Solicitações LGPD em atraso: {data.get('overdue_lgpd_requests')}")
    else:
        print(f"Erro: {response.content.decode()}")
    
    # Testar relatório completo
    response = client.get('/api/tenants/audit/compliance/full-report/')
    print(f"GET /api/tenants/audit/compliance/full-report/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Relatório gerado com sucesso")
        print(f"Período: {data.get('report_metadata', {}).get('period_start')} a {data.get('report_metadata', {}).get('period_end')}")
        print(f"Direitos dos titulares - Total de solicitações: {data.get('data_subject_rights', {}).get('total_requests')}")
        print(f"Atividades de processamento: {data.get('data_processing_activities', {}).get('total_processing_activities')}")
    else:
        print(f"Erro: {response.content.decode()}")
    
    # Testar resumo LGPD (endpoint legado)
    response = client.get('/api/tenants/audit/compliance/lgpd-summary/')
    print(f"GET /api/tenants/audit/compliance/lgpd-summary/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Resumo LGPD gerado com sucesso")
    else:
        print(f"Erro: {response.content.decode()}")


def test_export_functionality(client, user):
    """Testar funcionalidades de exportação"""
    print("\n=== Testando Funcionalidades de Exportação ===")
    
    # Testar exportação CSV de logs
    response = client.get('/api/tenants/audit/logs/export/')
    print(f"GET /api/tenants/audit/logs/export/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Exportação CSV - Content-Type: {response.get('Content-Type')}")
        print(f"Tamanho do arquivo: {len(response.content)} bytes")
    else:
        print(f"Erro: {response.content.decode()}")
    
    # Testar exportação CSV de conformidade
    response = client.get('/api/tenants/audit/compliance/export-csv/')
    print(f"GET /api/tenants/audit/compliance/export-csv/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Exportação CSV de conformidade - Content-Type: {response.get('Content-Type')}")
        print(f"Tamanho do arquivo: {len(response.content)} bytes")
    else:
        print(f"Erro: {response.content.decode()}")
    
    # Testar exportação JSON de conformidade
    response = client.get('/api/tenants/audit/compliance/export-json/')
    print(f"GET /api/tenants/audit/compliance/export-json/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Exportação JSON de conformidade - Content-Type: {response.get('Content-Type')}")
        print(f"Tamanho do arquivo: {len(response.content)} bytes")
    else:
        print(f"Erro: {response.content.decode()}")


def main():
    """Função principal"""
    print("=== Teste das APIs de Auditoria e Conformidade LGPD ===")
    
    # Configurar dados de teste
    tenant, user = setup_test_data()
    
    # Criar cliente de teste
    client = Client()
    
    # Executar testes
    test_audit_logs_api(client, user)
    test_lgpd_requests_api(client, user)
    test_compliance_reports_api(client, user)
    test_export_functionality(client, user)
    
    print("\n=== Teste Concluído ===")
    print("Verifique os logs acima para identificar possíveis problemas.")


if __name__ == '__main__':
    main()
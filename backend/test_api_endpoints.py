#!/usr/bin/env python
"""
Teste direto dos endpoints da API usando Django test client.
"""

import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from tenants.models import Tenant, TenantUser


def test_check_subdomain_endpoint():
    """Testa o endpoint de verificação de subdomínio"""
    
    print("=== Teste: Verificação de Subdomínio ===")
    
    client = Client()
    
    # Testar subdomínio disponível
    response = client.post(
        '/api/tenants/check-subdomain/',
        data=json.dumps({"subdomain": "novopetshop"}),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('available'):
            print("✅ Subdomínio disponível corretamente identificado")
        else:
            print("❌ Subdomínio deveria estar disponível")
    else:
        print("❌ Erro na verificação de subdomínio")
    
    print()


def test_tenant_registration_endpoint():
    """Testa o endpoint de registro de tenant"""
    
    print("=== Teste: Registro de Tenant ===")
    
    client = Client()
    
    # Dados de teste
    test_data = {
        "name": "Pet Shop Teste API",
        "subdomain": "testapi",
        "admin_email": "admin@testapi.com",
        "admin_password": "senha123456",
        "admin_first_name": "Admin",
        "admin_last_name": "Teste",
        "plan_type": "basic"
    }
    
    print(f"Dados de teste: {json.dumps(test_data, indent=2)}")
    
    response = client.post(
        '/api/tenants/register/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 201:
            print("✅ Registro de tenant realizado com sucesso!")
            return response_data
        else:
            print("❌ Falha no registro de tenant")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao processar resposta: {str(e)}")
        print(f"Response content: {response.content}")
        return None


def test_tenant_login_endpoint():
    """Testa o endpoint de login do tenant"""
    
    print("\n=== Teste: Login do Tenant ===")
    
    client = Client()
    
    # Primeiro, criar um tenant para testar login
    try:
        # Verificar se já existe
        tenant = Tenant.objects.filter(subdomain="logintest").first()
        if not tenant:
            from tenants.services import tenant_provisioning_service
            
            tenant_data = {
                "name": "Pet Shop Login Test",
                "subdomain": "logintest",
                "admin_email": "admin@logintest.com",
                "admin_password": "senha123456",
                "admin_first_name": "Admin",
                "admin_last_name": "Login"
            }
            
            tenant = tenant_provisioning_service.create_tenant(tenant_data)
            print(f"Tenant criado para teste: {tenant.name}")
        
        # Testar login
        login_data = {
            "email": "admin@logintest.com",
            "password": "senha123456",
            "tenant_subdomain": "logintest"
        }
        
        response = client.post(
            '/api/tenants/login/',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                print("✅ Login realizado com sucesso!")
            else:
                print("❌ Falha no login")
                
        except Exception as e:
            print(f"❌ Erro ao processar resposta de login: {str(e)}")
            print(f"Response content: {response.content}")
        
    except Exception as e:
        print(f"❌ Erro no teste de login: {str(e)}")


def test_tenant_status_endpoint():
    """Testa o endpoint de status do tenant"""
    
    print("\n=== Teste: Status do Tenant ===")
    
    client = Client()
    
    # Usar um tenant existente ou criar um
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ Nenhum tenant encontrado para testar status")
        return
    
    response = client.get(f'/api/tenants/status/{tenant.subdomain}/')
    
    print(f"Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ Status do tenant obtido com sucesso!")
        else:
            print("❌ Falha ao obter status do tenant")
            
    except Exception as e:
        print(f"❌ Erro ao processar resposta de status: {str(e)}")
        print(f"Response content: {response.content}")


def cleanup_test_data():
    """Remove dados de teste criados"""
    
    print("\n=== Limpeza dos Dados de Teste ===")
    
    try:
        # Remover tenants de teste
        test_subdomains = ["testapi", "logintest", "novopetshop"]
        
        for subdomain in test_subdomains:
            tenant = Tenant.objects.filter(subdomain=subdomain).first()
            if tenant:
                print(f"Removendo tenant: {tenant.name}")
                
                # Remover usuários do tenant
                TenantUser.objects.filter(tenant=tenant).delete()
                
                # Remover tenant
                tenant.delete()
                
                print(f"✅ Tenant {subdomain} removido")
        
        print("✅ Limpeza concluída")
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {str(e)}")


def main():
    """Executa todos os testes"""
    
    print(f"Iniciando testes de API em {datetime.now()}")
    print("=" * 60)
    
    try:
        # Executar testes
        test_check_subdomain_endpoint()
        test_tenant_registration_endpoint()
        test_tenant_login_endpoint()
        test_tenant_status_endpoint()
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
    
    finally:
        # Perguntar sobre limpeza
        print("\n" + "=" * 60)
        cleanup = input("Deseja remover os dados de teste criados? (s/N): ").lower()
        if cleanup in ['s', 'sim', 'y', 'yes']:
            cleanup_test_data()
    
    print(f"\nTestes concluídos em {datetime.now()}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Script de teste para API de registro de tenant.
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

def test_tenant_registration_api():
    """Testa a API de registro de tenant"""
    
    # URL da API (assumindo servidor local)
    base_url = "http://localhost:8000"
    register_url = f"{base_url}/api/tenants/register/"
    
    # Dados de teste para registro
    test_data = {
        "name": "Pet Shop Teste",
        "subdomain": "petshopteste",
        "admin_email": "admin@petshopteste.com",
        "admin_password": "senha123456",
        "admin_first_name": "João",
        "admin_last_name": "Silva",
        "plan_type": "basic"
    }
    
    print("=== Teste de Registro de Tenant ===")
    print(f"URL: {register_url}")
    print(f"Dados: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        # Fazer requisição POST
        response = requests.post(
            register_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        # Tentar decodificar JSON
        try:
            response_data = response.json()
            print("Resposta JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("Resposta não é JSON válido:")
            print(response.text)
        
        print()
        
        if response.status_code == 201:
            print("✅ Registro de tenant realizado com sucesso!")
            
            # Testar login se o registro foi bem-sucedido
            if 'data' in response_data:
                test_tenant_login(response_data['data'])
        else:
            print("❌ Falha no registro de tenant")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - certifique-se de que o servidor Django está rodando")
        print("Execute: python manage.py runserver")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")


def test_tenant_login(registration_data):
    """Testa o login do tenant recém-criado"""
    
    print("\n=== Teste de Login do Tenant ===")
    
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/tenants/login/"
    
    # Dados de login baseados no registro
    login_data = {
        "email": "admin@petshopteste.com",
        "password": "senha123456",
        "tenant_subdomain": "petshopteste"
    }
    
    print(f"URL: {login_url}")
    print(f"Dados: {json.dumps(login_data, indent=2)}")
    print()
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print("Resposta JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("Resposta não é JSON válido:")
            print(response.text)
        
        if response.status_code == 200:
            print("✅ Login realizado com sucesso!")
        else:
            print("❌ Falha no login")
            
    except Exception as e:
        print(f"❌ Erro no teste de login: {str(e)}")


def test_subdomain_availability():
    """Testa a verificação de disponibilidade de subdomínio"""
    
    print("\n=== Teste de Disponibilidade de Subdomínio ===")
    
    base_url = "http://localhost:8000"
    check_url = f"{base_url}/api/tenants/check-subdomain/"
    
    # Testar subdomínio disponível
    test_data = {"subdomain": "novopetshop"}
    
    print(f"URL: {check_url}")
    print(f"Testando subdomínio: {test_data['subdomain']}")
    
    try:
        response = requests.post(
            check_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print("Resposta JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("Resposta não é JSON válido:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erro no teste de disponibilidade: {str(e)}")


def cleanup_test_tenant():
    """Remove o tenant de teste criado"""
    
    print("\n=== Limpeza do Tenant de Teste ===")
    
    try:
        from tenants.models import Tenant, TenantUser
        
        # Remover tenant de teste
        test_tenant = Tenant.objects.filter(subdomain="petshopteste").first()
        if test_tenant:
            print(f"Removendo tenant: {test_tenant.name}")
            
            # Remover usuários do tenant
            TenantUser.objects.filter(tenant=test_tenant).delete()
            
            # Remover tenant
            test_tenant.delete()
            
            print("✅ Tenant de teste removido com sucesso")
        else:
            print("ℹ️ Nenhum tenant de teste encontrado para remover")
            
    except Exception as e:
        print(f"❌ Erro na limpeza: {str(e)}")


if __name__ == "__main__":
    print(f"Iniciando testes em {datetime.now()}")
    print("=" * 50)
    
    # Executar testes
    test_subdomain_availability()
    test_tenant_registration_api()
    
    # Perguntar se deve limpar
    print("\n" + "=" * 50)
    cleanup = input("Deseja remover o tenant de teste criado? (s/N): ").lower()
    if cleanup in ['s', 'sim', 'y', 'yes']:
        cleanup_test_tenant()
    
    print(f"\nTestes concluídos em {datetime.now()}")
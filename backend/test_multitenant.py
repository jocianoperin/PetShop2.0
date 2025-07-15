#!/usr/bin/env python
"""
Script de teste para verificar a infraestrutura multitenant.
"""

import os
import sys
import django

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant, TenantUser, TenantConfiguration
from tenants.utils import tenant_context, create_tenant_schema
from django.db import connection


def test_tenant_creation():
    """Testa criação de tenant"""
    print("=== Teste de Criação de Tenant ===")
    
    # Cria um tenant de teste
    tenant = Tenant.objects.create(
        name="Petshop Teste",
        subdomain="teste",
        plan_type="basic"
    )
    
    print(f"Tenant criado: {tenant.name} ({tenant.subdomain})")
    print(f"Schema: {tenant.schema_name}")
    
    return tenant


def test_tenant_user_creation(tenant):
    """Testa criação de usuário do tenant"""
    print("\n=== Teste de Criação de Usuário ===")
    
    user = TenantUser.objects.create(
        tenant=tenant,
        email="admin@teste.com",
        password_hash="hash_teste",
        first_name="Admin",
        last_name="Teste",
        role="admin"
    )
    
    print(f"Usuário criado: {user.email} ({user.full_name})")
    print(f"Tenant: {user.tenant.name}")
    
    return user


def test_tenant_configuration(tenant):
    """Testa configurações do tenant"""
    print("\n=== Teste de Configurações ===")
    
    # Cria algumas configurações
    configs = [
        ("theme_color", "#007bff"),
        ("company_logo", "/media/logos/teste.png"),
        ("max_appointments_per_day", "50"),
    ]
    
    for key, value in configs:
        config = TenantConfiguration.objects.create(
            tenant=tenant,
            config_key=key,
            config_value=value
        )
        print(f"Configuração criada: {key} = {value}")
    
    # Testa métodos utilitários
    theme = TenantConfiguration.get_config(tenant, "theme_color")
    print(f"Tema obtido: {theme}")
    
    # Atualiza configuração
    TenantConfiguration.set_config(tenant, "theme_color", "#28a745")
    new_theme = TenantConfiguration.get_config(tenant, "theme_color")
    print(f"Tema atualizado: {new_theme}")


def test_database_schema_operations(tenant):
    """Testa operações de schema de banco"""
    print("\n=== Teste de Operações de Schema ===")
    
    # Para SQLite, não temos schemas reais, mas podemos testar a lógica
    print(f"Schema do tenant: {tenant.schema_name}")
    
    # Testa contexto de tenant
    with tenant_context(tenant):
        print("Executando no contexto do tenant")
        current_tenant = tenant
        print(f"Tenant atual: {current_tenant.name}")


def test_middleware_simulation():
    """Simula funcionamento do middleware"""
    print("\n=== Teste de Simulação de Middleware ===")
    
    from tenants.utils import set_current_tenant, get_current_tenant
    
    # Simula definição de tenant atual
    tenant = Tenant.objects.first()
    set_current_tenant(tenant)
    
    current = get_current_tenant()
    print(f"Tenant atual definido: {current.name if current else 'Nenhum'}")
    
    # Limpa contexto
    set_current_tenant(None)
    current = get_current_tenant()
    print(f"Tenant após limpeza: {current}")


def test_database_router():
    """Testa o roteador de banco de dados"""
    print("\n=== Teste de Roteador de Banco ===")
    
    from tenants.db_router import TenantDatabaseRouter
    
    router = TenantDatabaseRouter()
    
    # Testa roteamento para modelo compartilhado
    db = router.db_for_read(Tenant)
    print(f"Banco para modelo Tenant: {db}")
    
    # Testa roteamento para modelo tenant-aware (simulado)
    from api.models import Cliente
    db = router.db_for_read(Cliente)
    print(f"Banco para modelo Cliente: {db}")


def cleanup_test_data():
    """Limpa dados de teste"""
    print("\n=== Limpeza de Dados de Teste ===")
    
    # Remove configurações
    TenantConfiguration.objects.filter(tenant__subdomain="teste").delete()
    print("Configurações removidas")
    
    # Remove usuários
    TenantUser.objects.filter(tenant__subdomain="teste").delete()
    print("Usuários removidos")
    
    # Remove tenant
    Tenant.objects.filter(subdomain="teste").delete()
    print("Tenant removido")


def main():
    """Função principal do teste"""
    print("Iniciando testes da infraestrutura multitenant...\n")
    
    try:
        # Executa testes
        tenant = test_tenant_creation()
        user = test_tenant_user_creation(tenant)
        test_tenant_configuration(tenant)
        test_database_schema_operations(tenant)
        test_middleware_simulation()
        test_database_router()
        
        print("\n=== Todos os testes executados com sucesso! ===")
        
    except Exception as e:
        print(f"\nErro durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpa dados de teste
        cleanup_test_data()
        print("\nTestes concluídos.")


if __name__ == "__main__":
    main()
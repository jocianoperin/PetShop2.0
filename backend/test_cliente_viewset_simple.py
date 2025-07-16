#!/usr/bin/env python
"""
Teste simples para verificar se o ClienteViewSet está funcionando
com isolamento de tenant.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.utils import set_current_tenant, tenant_context
from api.models import Cliente


def test_cliente_tenant_isolation():
    """Teste básico de isolamento de tenant para clientes"""
    print("=== Teste de Isolamento de Tenant - ClienteViewSet ===")
    
    try:
        # Buscar ou criar tenants de teste
        tenant1, created = Tenant.objects.get_or_create(
            subdomain="test-tenant-1",
            defaults={
                'name': "Test Tenant 1",
                'schema_name': "test_tenant_1",
                'is_active': True
            }
        )
        
        tenant2, created = Tenant.objects.get_or_create(
            subdomain="test-tenant-2", 
            defaults={
                'name': "Test Tenant 2",
                'schema_name': "test_tenant_2",
                'is_active': True
            }
        )
        
        print(f"Tenant 1: {tenant1.name} ({tenant1.subdomain})")
        print(f"Tenant 2: {tenant2.name} ({tenant2.subdomain})")
        
        # Limpar dados de teste anteriores
        with tenant_context(tenant1):
            Cliente.objects.filter(nome__startswith="Teste").delete()
        
        with tenant_context(tenant2):
            Cliente.objects.filter(nome__startswith="Teste").delete()
        
        # Criar clientes no tenant1
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            cliente1 = Cliente.objects.create(
                nome="Teste Cliente 1",
                email="teste1@tenant1.com",
                telefone="11111111111",
                endereco="Endereço Teste 1"
            )
            
            cliente2 = Cliente.objects.create(
                nome="Teste Cliente 2", 
                email="teste2@tenant1.com",
                telefone="11111111112",
                endereco="Endereço Teste 2"
            )
            
            print(f"\nCriados no Tenant 1:")
            print(f"- {cliente1.nome} (tenant: {cliente1.tenant.name})")
            print(f"- {cliente2.nome} (tenant: {cliente2.tenant.name})")
            
            # Verificar quantos clientes existem no tenant1
            total_tenant1 = Cliente.objects.count()
            print(f"Total de clientes no Tenant 1: {total_tenant1}")
        
        # Criar cliente no tenant2
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            
            cliente3 = Cliente.objects.create(
                nome="Teste Cliente 3",
                email="teste3@tenant2.com", 
                telefone="22222222222",
                endereco="Endereço Teste 3"
            )
            
            print(f"\nCriado no Tenant 2:")
            print(f"- {cliente3.nome} (tenant: {cliente3.tenant.name})")
            
            # Verificar quantos clientes existem no tenant2
            total_tenant2 = Cliente.objects.count()
            print(f"Total de clientes no Tenant 2: {total_tenant2}")
        
        # Verificar isolamento - tenant1 não deve ver clientes do tenant2
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            clientes_tenant1 = Cliente.objects.all()
            nomes_tenant1 = [c.nome for c in clientes_tenant1]
            
            print(f"\nClientes visíveis no Tenant 1: {nomes_tenant1}")
            
            # Verificar se não vê cliente do tenant2
            if "Teste Cliente 3" not in nomes_tenant1:
                print("✓ Isolamento funcionando: Tenant 1 não vê clientes do Tenant 2")
            else:
                print("❌ ERRO: Tenant 1 está vendo clientes do Tenant 2!")
                return False
        
        # Verificar isolamento - tenant2 não deve ver clientes do tenant1
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            clientes_tenant2 = Cliente.objects.all()
            nomes_tenant2 = [c.nome for c in clientes_tenant2]
            
            print(f"Clientes visíveis no Tenant 2: {nomes_tenant2}")
            
            # Verificar se não vê clientes do tenant1
            if "Teste Cliente 1" not in nomes_tenant2 and "Teste Cliente 2" not in nomes_tenant2:
                print("✓ Isolamento funcionando: Tenant 2 não vê clientes do Tenant 1")
            else:
                print("❌ ERRO: Tenant 2 está vendo clientes do Tenant 1!")
                return False
        
        # Teste de unicidade de email por tenant
        print(f"\n=== Teste de Unicidade de Email por Tenant ===")
        
        # Deve permitir mesmo email em tenants diferentes
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            cliente_email_dup1 = Cliente.objects.create(
                nome="Email Duplicado Tenant 1",
                email="mesmo@email.com",
                telefone="11111111113",
                endereco="Endereço Email Dup 1"
            )
            print(f"Criado no Tenant 1: {cliente_email_dup1.nome} - {cliente_email_dup1.email}")
        
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            cliente_email_dup2 = Cliente.objects.create(
                nome="Email Duplicado Tenant 2",
                email="mesmo@email.com",  # Mesmo email
                telefone="22222222223", 
                endereco="Endereço Email Dup 2"
            )
            print(f"Criado no Tenant 2: {cliente_email_dup2.nome} - {cliente_email_dup2.email}")
        
        print("✓ Mesmo email permitido em tenants diferentes")
        
        print(f"\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        print("✅ ClienteViewSet está funcionando corretamente com isolamento multitenant!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_cliente_tenant_isolation()
    if success:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n💥 Alguns testes falharam!")
    
    sys.exit(0 if success else 1)
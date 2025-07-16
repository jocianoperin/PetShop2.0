#!/usr/bin/env python
"""
Teste simples para verificar se os modelos tenant-aware estão funcionando.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.utils import tenant_context
from api.models import Cliente, Animal, Servico, Agendamento, Produto, Venda, ItemVenda

def test_tenant_aware_models():
    """Testa os modelos tenant-aware"""
    print("=== Teste dos Modelos Tenant-Aware ===")
    
    # Criar tenants de teste
    print("\n1. Criando tenants de teste...")
    tenant1, created1 = Tenant.objects.get_or_create(
        subdomain='teste1',
        defaults={
            'name': 'Petshop Teste 1',
            'schema_name': 'tenant_teste1'
        }
    )
    print(f"Tenant 1: {tenant1.name} ({'criado' if created1 else 'existente'})")
    
    tenant2, created2 = Tenant.objects.get_or_create(
        subdomain='teste2',
        defaults={
            'name': 'Petshop Teste 2',
            'schema_name': 'tenant_teste2'
        }
    )
    print(f"Tenant 2: {tenant2.name} ({'criado' if created2 else 'existente'})")
    
    # Testar isolamento de dados
    print("\n2. Testando isolamento de dados...")
    
    # Criar cliente no tenant1
    with tenant_context(tenant1):
        try:
            cliente1 = Cliente.objects.create(
                nome="João Silva",
                email="joao@teste.com",
                telefone="11999999999",
                endereco="Rua A, 123"
            )
            print(f"Cliente criado no tenant1: {cliente1.nome}")
        except Exception as e:
            print(f"Erro ao criar cliente no tenant1: {e}")
    
    # Criar cliente no tenant2
    with tenant_context(tenant2):
        try:
            cliente2 = Cliente.objects.create(
                nome="Maria Santos",
                email="maria@teste.com",
                telefone="11888888888",
                endereco="Rua B, 456"
            )
            print(f"Cliente criado no tenant2: {cliente2.nome}")
        except Exception as e:
            print(f"Erro ao criar cliente no tenant2: {e}")
    
    # Verificar isolamento
    print("\n3. Verificando isolamento...")
    
    with tenant_context(tenant1):
        clientes_tenant1 = Cliente.objects.all()
        print(f"Clientes no tenant1: {clientes_tenant1.count()}")
        for cliente in clientes_tenant1:
            print(f"  - {cliente.nome} ({cliente.tenant.name})")
    
    with tenant_context(tenant2):
        clientes_tenant2 = Cliente.objects.all()
        print(f"Clientes no tenant2: {clientes_tenant2.count()}")
        for cliente in clientes_tenant2:
            print(f"  - {cliente.nome} ({cliente.tenant.name})")
    
    # Testar manager all_tenants
    print("\n4. Testando manager all_tenants...")
    todos_clientes = Cliente.objects.all_tenants()
    print(f"Total de clientes (todos os tenants): {todos_clientes.count()}")
    for cliente in todos_clientes:
        print(f"  - {cliente.nome} ({cliente.tenant.name})")
    
    # Testar criação de outros modelos
    print("\n5. Testando outros modelos...")
    
    with tenant_context(tenant1):
        try:
            # Criar serviço
            from datetime import timedelta
            servico = Servico.objects.create(
                nome="Banho e Tosa",
                descricao="Banho completo com tosa",
                preco=50.00,
                duracao_estimada=timedelta(hours=1, minutes=30)
            )
            print(f"Serviço criado: {servico.nome}")
            
            # Criar produto
            produto = Produto.objects.create(
                nome="Ração Premium",
                descricao="Ração premium para cães",
                categoria="racao",
                preco=89.90,
                estoque=100
            )
            print(f"Produto criado: {produto.nome}")
            
        except Exception as e:
            print(f"Erro ao criar outros modelos: {e}")
    
    print("\n=== Teste Concluído ===")

if __name__ == '__main__':
    test_tenant_aware_models()
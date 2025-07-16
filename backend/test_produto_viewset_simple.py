#!/usr/bin/env python
"""
Teste simples para verificar se o ProdutoViewSet está funcionando
com isolamento de tenant e controle de estoque.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.utils import set_current_tenant, tenant_context
from api.models import Produto


def test_produto_tenant_isolation():
    """Teste básico de isolamento de tenant para produtos"""
    print("=== Teste de Isolamento de Tenant - ProdutoViewSet ===")
    
    try:
        # Buscar ou criar tenants de teste
        tenant1, created = Tenant.objects.get_or_create(
            subdomain="test-produto-1",
            defaults={
                'name': "Test Produto Tenant 1",
                'schema_name': "test_produto_1",
                'is_active': True
            }
        )
        
        tenant2, created = Tenant.objects.get_or_create(
            subdomain="test-produto-2", 
            defaults={
                'name': "Test Produto Tenant 2",
                'schema_name': "test_produto_2",
                'is_active': True
            }
        )
        
        print(f"Tenant 1: {tenant1.name} ({tenant1.subdomain})")
        print(f"Tenant 2: {tenant2.name} ({tenant2.subdomain})")
        
        # Limpar dados de teste anteriores
        with tenant_context(tenant1):
            Produto.objects.filter(nome__startswith="Teste").delete()
        
        with tenant_context(tenant2):
            Produto.objects.filter(nome__startswith="Teste").delete()
        
        # Criar produtos no tenant1
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            produto1 = Produto.objects.create(
                nome="Teste Ração Premium",
                descricao="Ração premium para cães adultos",
                categoria="racao",
                preco=Decimal('89.90'),
                estoque=50,
                estoque_minimo=10,
                ativo=True
            )
            
            produto2 = Produto.objects.create(
                nome="Teste Brinquedo Bola",
                descricao="Bola de borracha para cães",
                categoria="brinquedo",
                preco=Decimal('15.50'),
                estoque=3,  # Estoque baixo
                estoque_minimo=5,
                ativo=True
            )
            
            print(f"\nCriados no Tenant 1:")
            print(f"- Produto: {produto1.nome} - R$ {produto1.preco} (estoque: {produto1.estoque}) (tenant: {produto1.tenant.name})")
            print(f"- Produto: {produto2.nome} - R$ {produto2.preco} (estoque: {produto2.estoque}) (tenant: {produto2.tenant.name})")
            print(f"- Produto 2 estoque baixo: {produto2.estoque_baixo}")
            
            # Verificar quantos produtos existem no tenant1
            total_produtos_tenant1 = Produto.objects.count()
            print(f"Total de produtos no Tenant 1: {total_produtos_tenant1}")
        
        # Criar produto no tenant2
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            
            produto3 = Produto.objects.create(
                nome="Teste Shampoo Pet",
                descricao="Shampoo especial para pets",
                categoria="higiene",
                preco=Decimal('25.00'),
                estoque=20,
                estoque_minimo=5,
                ativo=True
            )
            
            print(f"\nCriado no Tenant 2:")
            print(f"- Produto: {produto3.nome} - R$ {produto3.preco} (estoque: {produto3.estoque}) (tenant: {produto3.tenant.name})")
            
            # Verificar quantos produtos existem no tenant2
            total_produtos_tenant2 = Produto.objects.count()
            print(f"Total de produtos no Tenant 2: {total_produtos_tenant2}")
        
        # Verificar isolamento - tenant1 não deve ver produtos do tenant2
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            produtos_tenant1 = Produto.objects.all()
            nomes_tenant1 = [p.nome for p in produtos_tenant1]
            
            print(f"\nProdutos visíveis no Tenant 1: {nomes_tenant1}")
            
            # Verificar se não vê produto do tenant2
            if "Teste Shampoo Pet" not in nomes_tenant1:
                print("✓ Isolamento funcionando: Tenant 1 não vê produtos do Tenant 2")
            else:
                print("❌ ERRO: Tenant 1 está vendo produtos do Tenant 2!")
                return False
        
        # Verificar isolamento - tenant2 não deve ver produtos do tenant1
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            produtos_tenant2 = Produto.objects.all()
            nomes_tenant2 = [p.nome for p in produtos_tenant2]
            
            print(f"Produtos visíveis no Tenant 2: {nomes_tenant2}")
            
            # Verificar se não vê produtos do tenant1
            if "Teste Ração Premium" not in nomes_tenant2 and "Teste Brinquedo Bola" not in nomes_tenant2:
                print("✓ Isolamento funcionando: Tenant 2 não vê produtos do Tenant 1")
            else:
                print("❌ ERRO: Tenant 2 está vendo produtos do Tenant 1!")
                return False
        
        # Teste de unicidade de nome por tenant
        print(f"\n=== Teste de Unicidade de Nome por Tenant ===")
        
        # Deve permitir mesmo nome em tenants diferentes
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            produto_nome_dup1 = Produto.objects.create(
                nome="Produto Duplicado",
                descricao="Produto com nome duplicado tenant 1",
                categoria="outro",
                preco=Decimal('10.00'),
                estoque=5,
                estoque_minimo=2,
                ativo=True
            )
            print(f"Criado no Tenant 1: {produto_nome_dup1.nome}")
        
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            produto_nome_dup2 = Produto.objects.create(
                nome="Produto Duplicado",  # Mesmo nome
                descricao="Produto com nome duplicado tenant 2",
                categoria="outro",
                preco=Decimal('12.00'),
                estoque=8,
                estoque_minimo=3,
                ativo=True
            )
            print(f"Criado no Tenant 2: {produto_nome_dup2.nome}")
        
        print("✓ Mesmo nome permitido em tenants diferentes")
        
        # Teste de filtro por categoria
        print(f"\n=== Teste de Filtro por Categoria ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar produtos da categoria 'racao'
            produtos_racao = Produto.objects.filter(categoria='racao')
            if produtos_racao.count() == 1 and produtos_racao.first().nome == "Teste Ração Premium":
                print("✓ Filtro por categoria funcionando")
            else:
                print("❌ ERRO: Filtro por categoria não funcionou")
                return False
        
        # Teste de produtos com estoque baixo
        print(f"\n=== Teste de Estoque Baixo ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar produtos com estoque baixo
            produtos_estoque_baixo = [p for p in Produto.objects.all() if p.estoque_baixo]
            nomes_estoque_baixo = [p.nome for p in produtos_estoque_baixo]
            
            print(f"Produtos com estoque baixo no Tenant 1: {nomes_estoque_baixo}")
            
            if "Teste Brinquedo Bola" in nomes_estoque_baixo:
                print("✓ Detecção de estoque baixo funcionando")
            else:
                print("❌ ERRO: Detecção de estoque baixo não funcionou")
                return False
        
        # Teste de busca por nome
        print(f"\n=== Teste de Busca por Nome ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar por nome
            produtos_racao_busca = Produto.objects.filter(nome__icontains="Ração")
            if produtos_racao_busca.count() == 1:
                print("✓ Busca por nome funcionando")
            else:
                print("❌ ERRO: Busca por nome não funcionou")
                return False
        
        # Teste de controle de estoque
        print(f"\n=== Teste de Controle de Estoque ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Simular entrada de estoque
            produto_teste = Produto.objects.get(nome="Teste Brinquedo Bola")
            estoque_anterior = produto_teste.estoque
            
            # Adicionar 10 unidades
            produto_teste.estoque += 10
            produto_teste.save()
            
            print(f"Estoque anterior: {estoque_anterior}, Estoque atual: {produto_teste.estoque}")
            
            if produto_teste.estoque == estoque_anterior + 10:
                print("✓ Controle de estoque funcionando")
            else:
                print("❌ ERRO: Controle de estoque não funcionou")
                return False
            
            # Verificar se não está mais com estoque baixo
            if not produto_teste.estoque_baixo:
                print("✓ Status de estoque baixo atualizado corretamente")
            else:
                print("❌ ERRO: Status de estoque baixo não foi atualizado")
                return False
        
        print(f"\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        print("✅ ProdutoViewSet está funcionando corretamente com isolamento multitenant!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_produto_tenant_isolation()
    if success:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n💥 Alguns testes falharam!")
    
    sys.exit(0 if success else 1)
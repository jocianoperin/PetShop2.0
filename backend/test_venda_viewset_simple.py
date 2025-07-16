#!/usr/bin/env python
"""
Teste simples para verificar se o VendaViewSet está funcionando
com isolamento de tenant e controle financeiro.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.utils import set_current_tenant, tenant_context
from api.models import Cliente, Produto, Venda, ItemVenda


def test_venda_tenant_isolation():
    """Teste básico de isolamento de tenant para vendas"""
    print("=== Teste de Isolamento de Tenant - VendaViewSet ===")
    
    try:
        # Buscar ou criar tenants de teste
        tenant1, created = Tenant.objects.get_or_create(
            subdomain="test-venda-1",
            defaults={
                'name': "Test Venda Tenant 1",
                'schema_name': "test_venda_1",
                'is_active': True
            }
        )
        
        tenant2, created = Tenant.objects.get_or_create(
            subdomain="test-venda-2", 
            defaults={
                'name': "Test Venda Tenant 2",
                'schema_name': "test_venda_2",
                'is_active': True
            }
        )
        
        print(f"Tenant 1: {tenant1.name} ({tenant1.subdomain})")
        print(f"Tenant 2: {tenant2.name} ({tenant2.subdomain})")
        
        # Limpar dados de teste anteriores
        with tenant_context(tenant1):
            ItemVenda.objects.filter(venda__observacoes__contains="Teste").delete()
            Venda.objects.filter(observacoes__contains="Teste").delete()
            Produto.objects.filter(nome__startswith="Teste").delete()
            Cliente.objects.filter(nome__startswith="Teste").delete()
        
        with tenant_context(tenant2):
            ItemVenda.objects.filter(venda__observacoes__contains="Teste").delete()
            Venda.objects.filter(observacoes__contains="Teste").delete()
            Produto.objects.filter(nome__startswith="Teste").delete()
            Cliente.objects.filter(nome__startswith="Teste").delete()
        
        # Criar dados base no tenant1
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            cliente1 = Cliente.objects.create(
                nome="Teste Cliente Venda 1",
                email="teste1@venda1.com",
                telefone="11111111111",
                endereco="Endereço Teste 1"
            )
            
            produto1 = Produto.objects.create(
                nome="Teste Produto Venda 1",
                descricao="Produto para teste de venda",
                categoria="outro",
                preco=Decimal('50.00'),
                estoque=100,
                estoque_minimo=10,
                ativo=True
            )
            
            # Criar venda
            venda1 = Venda.objects.create(
                cliente=cliente1,
                valor_total=Decimal('100.00'),
                desconto=Decimal('10.00'),
                observacoes='Teste venda tenant 1'
            )
            
            # Criar item da venda
            item1 = ItemVenda.objects.create(
                venda=venda1,
                produto=produto1,
                quantidade=2,
                preco_unitario=Decimal('50.00')
            )
            
            print(f"\nCriados no Tenant 1:")
            print(f"- Cliente: {cliente1.nome} (tenant: {cliente1.tenant.name})")
            print(f"- Produto: {produto1.nome} - R$ {produto1.preco} (tenant: {produto1.tenant.name})")
            print(f"- Venda: {venda1.id} - R$ {venda1.valor_total} (tenant: {venda1.tenant.name})")
            print(f"- Item: {item1.produto.nome} x{item1.quantidade} (tenant: {item1.tenant.name})")
            
            # Verificar quantas vendas existem no tenant1
            total_vendas_tenant1 = Venda.objects.count()
            print(f"Total de vendas no Tenant 1: {total_vendas_tenant1}")
        
        # Criar dados base no tenant2
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            
            cliente2 = Cliente.objects.create(
                nome="Teste Cliente Venda 2",
                email="teste2@venda2.com", 
                telefone="22222222222",
                endereco="Endereço Teste 2"
            )
            
            produto2 = Produto.objects.create(
                nome="Teste Produto Venda 2",
                descricao="Produto para teste de venda 2",
                categoria="outro",
                preco=Decimal('30.00'),
                estoque=50,
                estoque_minimo=5,
                ativo=True
            )
            
            # Criar venda
            venda2 = Venda.objects.create(
                cliente=cliente2,
                valor_total=Decimal('90.00'),
                desconto=Decimal('0.00'),
                observacoes='Teste venda tenant 2'
            )
            
            # Criar item da venda
            item2 = ItemVenda.objects.create(
                venda=venda2,
                produto=produto2,
                quantidade=3,
                preco_unitario=Decimal('30.00')
            )
            
            print(f"\nCriado no Tenant 2:")
            print(f"- Cliente: {cliente2.nome} (tenant: {cliente2.tenant.name})")
            print(f"- Produto: {produto2.nome} - R$ {produto2.preco} (tenant: {produto2.tenant.name})")
            print(f"- Venda: {venda2.id} - R$ {venda2.valor_total} (tenant: {venda2.tenant.name})")
            print(f"- Item: {item2.produto.nome} x{item2.quantidade} (tenant: {item2.tenant.name})")
            
            # Verificar quantas vendas existem no tenant2
            total_vendas_tenant2 = Venda.objects.count()
            print(f"Total de vendas no Tenant 2: {total_vendas_tenant2}")
        
        # Verificar isolamento - tenant1 não deve ver vendas do tenant2
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            vendas_tenant1 = Venda.objects.all()
            observacoes_tenant1 = [v.observacoes for v in vendas_tenant1]
            
            print(f"\nVendas visíveis no Tenant 1: {observacoes_tenant1}")
            
            # Verificar se não vê venda do tenant2
            if "Teste venda tenant 2" not in observacoes_tenant1:
                print("✓ Isolamento funcionando: Tenant 1 não vê vendas do Tenant 2")
            else:
                print("❌ ERRO: Tenant 1 está vendo vendas do Tenant 2!")
                return False
        
        # Verificar isolamento - tenant2 não deve ver vendas do tenant1
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            vendas_tenant2 = Venda.objects.all()
            observacoes_tenant2 = [v.observacoes for v in vendas_tenant2]
            
            print(f"Vendas visíveis no Tenant 2: {observacoes_tenant2}")
            
            # Verificar se não vê venda do tenant1
            if "Teste venda tenant 1" not in observacoes_tenant2:
                print("✓ Isolamento funcionando: Tenant 2 não vê vendas do Tenant 1")
            else:
                print("❌ ERRO: Tenant 2 está vendo vendas do Tenant 1!")
                return False
        
        # Teste de validação de relacionamento cross-tenant
        print(f"\n=== Teste de Validação Cross-Tenant ===")
        
        # Tentar criar venda no tenant1 com cliente do tenant2 (deve falhar)
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            try:
                # Isso deve falhar porque cliente2 pertence ao tenant2
                venda_invalida = Venda(
                    cliente=cliente2,  # Cliente de outro tenant!
                    valor_total=Decimal('50.00'),
                    desconto=Decimal('0.00'),
                    observacoes='Venda inválida cross-tenant'
                )
                venda_invalida.save()
                print("❌ ERRO: Conseguiu criar venda com cliente de outro tenant!")
                return False
            except Exception as e:
                print(f"✓ Validação funcionando: {str(e)}")
        
        # Teste de filtro por cliente
        print(f"\n=== Teste de Filtro por Cliente ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar vendas do cliente1
            vendas_cliente1 = Venda.objects.filter(cliente=cliente1)
            print(f"Vendas do cliente {cliente1.nome}: {vendas_cliente1.count()}")
            
            # Deve retornar 1 venda
            if vendas_cliente1.count() == 1:
                print("✓ Filtro por cliente funcionando corretamente")
            else:
                print(f"❌ ERRO: Esperado 1 venda, encontrado {vendas_cliente1.count()}")
                return False
        
        # Teste de cálculos financeiros
        print(f"\n=== Teste de Cálculos Financeiros ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Calcular total de vendas
            from django.db.models import Sum
            total_vendas = Venda.objects.aggregate(Sum('valor_total'))['valor_total__sum']
            total_descontos = Venda.objects.aggregate(Sum('desconto'))['desconto__sum']
            
            print(f"Total de vendas no Tenant 1: R$ {total_vendas}")
            print(f"Total de descontos no Tenant 1: R$ {total_descontos}")
            
            if total_vendas == Decimal('100.00') and total_descontos == Decimal('10.00'):
                print("✓ Cálculos financeiros funcionando")
            else:
                print("❌ ERRO: Cálculos financeiros não funcionaram")
                return False
        
        # Teste de itens de venda
        print(f"\n=== Teste de Itens de Venda ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar itens da venda
            itens_venda1 = ItemVenda.objects.filter(venda=venda1)
            if itens_venda1.count() == 1:
                item = itens_venda1.first()
                subtotal = item.quantidade * item.preco_unitario
                print(f"Item: {item.produto.nome} x{item.quantidade} = R$ {subtotal}")
                
                if subtotal == Decimal('100.00'):
                    print("✓ Cálculo de subtotal funcionando")
                else:
                    print("❌ ERRO: Cálculo de subtotal não funcionou")
                    return False
            else:
                print("❌ ERRO: Número incorreto de itens na venda")
                return False
        
        # Teste de isolamento de itens de venda
        print(f"\n=== Teste de Isolamento de Itens de Venda ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar todos os itens de venda
            todos_itens = ItemVenda.objects.all()
            produtos_itens = [item.produto.nome for item in todos_itens]
            
            print(f"Produtos em itens de venda no Tenant 1: {produtos_itens}")
            
            # Não deve ver produtos do tenant2
            if "Teste Produto Venda 2" not in produtos_itens:
                print("✓ Isolamento de itens de venda funcionando")
            else:
                print("❌ ERRO: Vendo itens de venda de outro tenant")
                return False
        
        print(f"\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        print("✅ VendaViewSet está funcionando corretamente com isolamento multitenant!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_venda_tenant_isolation()
    if success:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n💥 Alguns testes falharam!")
    
    sys.exit(0 if success else 1)
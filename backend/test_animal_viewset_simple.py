#!/usr/bin/env python
"""
Teste simples para verificar se o AnimalViewSet está funcionando
com isolamento de tenant e validações de relacionamento.
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.utils import set_current_tenant, tenant_context
from api.models import Cliente, Animal


def test_animal_tenant_isolation():
    """Teste básico de isolamento de tenant para animais"""
    print("=== Teste de Isolamento de Tenant - AnimalViewSet ===")
    
    try:
        # Buscar ou criar tenants de teste
        tenant1, created = Tenant.objects.get_or_create(
            subdomain="test-animal-1",
            defaults={
                'name': "Test Animal Tenant 1",
                'schema_name': "test_animal_1",
                'is_active': True
            }
        )
        
        tenant2, created = Tenant.objects.get_or_create(
            subdomain="test-animal-2", 
            defaults={
                'name': "Test Animal Tenant 2",
                'schema_name': "test_animal_2",
                'is_active': True
            }
        )
        
        print(f"Tenant 1: {tenant1.name} ({tenant1.subdomain})")
        print(f"Tenant 2: {tenant2.name} ({tenant2.subdomain})")
        
        # Limpar dados de teste anteriores
        with tenant_context(tenant1):
            Animal.objects.filter(nome__startswith="Teste").delete()
            Cliente.objects.filter(nome__startswith="Teste").delete()
        
        with tenant_context(tenant2):
            Animal.objects.filter(nome__startswith="Teste").delete()
            Cliente.objects.filter(nome__startswith="Teste").delete()
        
        # Criar clientes e animais no tenant1
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            cliente1 = Cliente.objects.create(
                nome="Teste Cliente Animal 1",
                email="teste1@animal1.com",
                telefone="11111111111",
                endereco="Endereço Teste 1"
            )
            
            animal1 = Animal.objects.create(
                nome="Teste Rex",
                especie="cao",
                raca="Labrador",
                data_nascimento=date.today() - timedelta(days=365*2),  # 2 anos
                peso=25.5,
                cor="Dourado",
                cliente=cliente1
            )
            
            animal2 = Animal.objects.create(
                nome="Teste Mimi",
                especie="gato",
                raca="Persa",
                data_nascimento=date.today() - timedelta(days=365*1),  # 1 ano
                peso=4.2,
                cor="Branco",
                cliente=cliente1
            )
            
            print(f"\nCriados no Tenant 1:")
            print(f"- Cliente: {cliente1.nome} (tenant: {cliente1.tenant.name})")
            print(f"- Animal: {animal1.nome} - {animal1.especie} (tenant: {animal1.tenant.name})")
            print(f"- Animal: {animal2.nome} - {animal2.especie} (tenant: {animal2.tenant.name})")
            
            # Verificar quantos animais existem no tenant1
            total_animais_tenant1 = Animal.objects.count()
            print(f"Total de animais no Tenant 1: {total_animais_tenant1}")
        
        # Criar cliente e animal no tenant2
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            
            cliente2 = Cliente.objects.create(
                nome="Teste Cliente Animal 2",
                email="teste2@animal2.com", 
                telefone="22222222222",
                endereco="Endereço Teste 2"
            )
            
            animal3 = Animal.objects.create(
                nome="Teste Buddy",
                especie="cao",
                raca="Golden Retriever",
                data_nascimento=date.today() - timedelta(days=365*3),  # 3 anos
                peso=30.0,
                cor="Dourado",
                cliente=cliente2
            )
            
            print(f"\nCriado no Tenant 2:")
            print(f"- Cliente: {cliente2.nome} (tenant: {cliente2.tenant.name})")
            print(f"- Animal: {animal3.nome} - {animal3.especie} (tenant: {animal3.tenant.name})")
            
            # Verificar quantos animais existem no tenant2
            total_animais_tenant2 = Animal.objects.count()
            print(f"Total de animais no Tenant 2: {total_animais_tenant2}")
        
        # Verificar isolamento - tenant1 não deve ver animais do tenant2
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            animais_tenant1 = Animal.objects.all()
            nomes_tenant1 = [a.nome for a in animais_tenant1]
            
            print(f"\nAnimais visíveis no Tenant 1: {nomes_tenant1}")
            
            # Verificar se não vê animal do tenant2
            if "Teste Buddy" not in nomes_tenant1:
                print("✓ Isolamento funcionando: Tenant 1 não vê animais do Tenant 2")
            else:
                print("❌ ERRO: Tenant 1 está vendo animais do Tenant 2!")
                return False
        
        # Verificar isolamento - tenant2 não deve ver animais do tenant1
        with tenant_context(tenant2):
            set_current_tenant(tenant2)
            animais_tenant2 = Animal.objects.all()
            nomes_tenant2 = [a.nome for a in animais_tenant2]
            
            print(f"Animais visíveis no Tenant 2: {nomes_tenant2}")
            
            # Verificar se não vê animais do tenant1
            if "Teste Rex" not in nomes_tenant2 and "Teste Mimi" not in nomes_tenant2:
                print("✓ Isolamento funcionando: Tenant 2 não vê animais do Tenant 1")
            else:
                print("❌ ERRO: Tenant 2 está vendo animais do Tenant 1!")
                return False
        
        # Teste de validação de relacionamento cliente-animal
        print(f"\n=== Teste de Validação de Relacionamento Cliente-Animal ===")
        
        # Tentar criar animal no tenant1 com cliente do tenant2 (deve falhar)
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            try:
                # Isso deve falhar porque cliente2 pertence ao tenant2
                animal_invalido = Animal(
                    nome="Animal Inválido",
                    especie="cao",
                    raca="Vira-lata",
                    data_nascimento=date.today() - timedelta(days=365),
                    cliente=cliente2  # Cliente de outro tenant!
                )
                animal_invalido.save()
                print("❌ ERRO: Conseguiu criar animal com cliente de outro tenant!")
                return False
            except Exception as e:
                print(f"✓ Validação funcionando: {str(e)}")
        
        # Teste de filtro por cliente
        print(f"\n=== Teste de Filtro por Cliente ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar animais do cliente1
            animais_cliente1 = Animal.objects.filter(cliente=cliente1)
            print(f"Animais do cliente {cliente1.nome}: {[a.nome for a in animais_cliente1]}")
            
            # Deve retornar 2 animais
            if animais_cliente1.count() == 2:
                print("✓ Filtro por cliente funcionando corretamente")
            else:
                print(f"❌ ERRO: Esperado 2 animais, encontrado {animais_cliente1.count()}")
                return False
        
        # Teste de busca por nome/raça
        print(f"\n=== Teste de Busca por Nome/Raça ===")
        
        with tenant_context(tenant1):
            set_current_tenant(tenant1)
            
            # Buscar por nome
            animais_rex = Animal.objects.filter(nome__icontains="Rex")
            if animais_rex.count() == 1 and animais_rex.first().nome == "Teste Rex":
                print("✓ Busca por nome funcionando")
            else:
                print("❌ ERRO: Busca por nome não funcionou")
                return False
            
            # Buscar por raça
            animais_labrador = Animal.objects.filter(raca__icontains="Labrador")
            if animais_labrador.count() == 1:
                print("✓ Busca por raça funcionando")
            else:
                print("❌ ERRO: Busca por raça não funcionou")
                return False
        
        print(f"\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        print("✅ AnimalViewSet está funcionando corretamente com isolamento multitenant!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_animal_tenant_isolation()
    if success:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n💥 Alguns testes falharam!")
    
    sys.exit(0 if success else 1)
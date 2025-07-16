#!/usr/bin/env python
"""
Teste para verificar validações cross-tenant.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.utils import tenant_context
from api.models import Cliente, Animal
from django.core.exceptions import ValidationError

def test_cross_tenant_validation():
    """Testa validações cross-tenant"""
    print("=== Teste de Validações Cross-Tenant ===")
    
    # Obter tenants existentes
    tenant1 = Tenant.objects.get(subdomain='teste1')
    tenant2 = Tenant.objects.get(subdomain='teste2')
    
    # Criar cliente no tenant1
    with tenant_context(tenant1):
        cliente1 = Cliente.objects.first()
        if not cliente1:
            cliente1 = Cliente.objects.create(
                nome="Cliente Teste 1",
                email="cliente1@teste.com",
                telefone="11111111111",
                endereco="Endereço 1"
            )
    
    print(f"Cliente criado no tenant1: {cliente1.nome}")
    
    # Tentar criar animal no tenant2 com cliente do tenant1
    print("\nTestando validação cross-tenant...")
    
    with tenant_context(tenant2):
        try:
            animal = Animal(
                nome="Rex",
                especie="cao",
                data_nascimento="2020-01-01",
                cliente=cliente1  # Cliente de outro tenant!
            )
            animal.clean()  # Deve falhar na validação
            animal.save()
            print("ERRO: Validação cross-tenant falhou!")
        except ValidationError as e:
            print(f"✅ Validação funcionou: {e}")
        except Exception as e:
            print(f"✅ Erro esperado: {e}")
    
    # Testar salvamento no contexto errado
    print("\nTestando salvamento no contexto errado...")
    
    with tenant_context(tenant2):
        try:
            cliente1.nome = "Nome Modificado"
            cliente1.save()  # Deve falhar
            print("ERRO: Validação de contexto falhou!")
        except ValidationError as e:
            print(f"✅ Validação de contexto funcionou: {e}")
        except Exception as e:
            print(f"✅ Erro esperado: {e}")
    
    print("\n=== Teste Concluído ===")

if __name__ == '__main__':
    test_cross_tenant_validation()
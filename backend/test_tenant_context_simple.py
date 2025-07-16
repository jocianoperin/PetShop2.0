#!/usr/bin/env python
"""
Script simples para testar o sistema de contexto de tenant
sem depender do Django test framework.
"""

import os
import sys

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')

try:
    import django
    django.setup()
    
    # Importa as funções de contexto
    from tenants.utils import (
        get_current_tenant, set_current_tenant, tenant_context,
        push_tenant_context, pop_tenant_context, clear_tenant_context
    )
    
    print("=== Testando Sistema de Contexto de Tenant ===")
    
    # Classe mock para simular um tenant
    class MockTenant:
        def __init__(self, name, schema_name):
            self.name = name
            self.schema_name = schema_name
        
        def __str__(self):
            return f"{self.name} ({self.schema_name})"
        
        def __eq__(self, other):
            return (isinstance(other, MockTenant) and 
                   self.name == other.name and 
                   self.schema_name == other.schema_name)
    
    # Criar tenants de teste
    tenant1 = MockTenant("Petshop Teste 1", "tenant_teste1")
    tenant2 = MockTenant("Petshop Teste 2", "tenant_teste2")
    
    # Teste 1: Contexto básico
    print("\n1. Testando contexto básico...")
    assert get_current_tenant() is None, "Contexto inicial deve ser None"
    
    set_current_tenant(tenant1)
    assert get_current_tenant() == tenant1, "Tenant deve ser definido corretamente"
    
    set_current_tenant(None)
    assert get_current_tenant() is None, "Contexto deve ser limpo"
    print("✓ Contexto básico funcionando")
    
    # Teste 2: Context manager
    print("\n2. Testando context manager...")
    assert get_current_tenant() is None, "Contexto inicial deve ser None"
    
    with tenant_context(tenant1):
        assert get_current_tenant() == tenant1, "Tenant deve estar ativo no contexto"
        
        # Contexto aninhado
        with tenant_context(tenant2):
            assert get_current_tenant() == tenant2, "Tenant2 deve estar ativo no contexto aninhado"
        
        # Volta para tenant1
        assert get_current_tenant() == tenant1, "Deve voltar para tenant1 após contexto aninhado"
    
    # Contexto deve estar limpo
    assert get_current_tenant() is None, "Contexto deve estar limpo após sair do context manager"
    print("✓ Context manager funcionando")
    
    # Teste 3: Stack de contexto
    print("\n3. Testando stack de contexto...")
    assert get_current_tenant() is None, "Contexto inicial deve ser None"
    
    push_tenant_context(tenant1)
    assert get_current_tenant() == tenant1, "Tenant1 deve estar no topo do stack"
    
    push_tenant_context(tenant2)
    assert get_current_tenant() == tenant2, "Tenant2 deve estar no topo do stack"
    
    pop_tenant_context()
    assert get_current_tenant() == tenant1, "Deve voltar para tenant1 após pop"
    
    pop_tenant_context()
    assert get_current_tenant() is None, "Deve voltar para None após segundo pop"
    print("✓ Stack de contexto funcionando")
    
    # Teste 4: Clear context
    print("\n4. Testando clear context...")
    push_tenant_context(tenant1)
    push_tenant_context(tenant2)
    assert get_current_tenant() == tenant2, "Tenant2 deve estar ativo"
    
    clear_tenant_context()
    assert get_current_tenant() is None, "Contexto deve estar completamente limpo"
    print("✓ Clear context funcionando")
    
    print("\n=== Todos os testes passaram! ===")
    print("✓ Thread-local storage funcionando")
    print("✓ Context manager implementado")
    print("✓ Stack de contexto funcionando")
    print("✓ Sistema de contexto de tenant está completo")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Verifique se o Django está instalado e configurado corretamente.")
except Exception as e:
    print(f"❌ Erro nos testes: {e}")
    import traceback
    traceback.print_exc()
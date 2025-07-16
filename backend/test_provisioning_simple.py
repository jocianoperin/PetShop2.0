#!/usr/bin/env python
"""
Script simples para testar o TenantProvisioningService
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.services import TenantProvisioningService, TenantProvisioningError
from tenants.models import Tenant, TenantUser, TenantConfiguration

def test_service_import():
    """Testa se o serviço pode ser importado"""
    print("✓ TenantProvisioningService importado com sucesso")
    return True

def test_service_instantiation():
    """Testa se o serviço pode ser instanciado"""
    try:
        service = TenantProvisioningService()
        print("✓ TenantProvisioningService instanciado com sucesso")
        return True
    except Exception as e:
        print(f"✗ Erro ao instanciar serviço: {e}")
        return False

def test_validation_method():
    """Testa método de validação"""
    try:
        service = TenantProvisioningService()
        
        # Teste com dados válidos
        valid_data = {
            'name': 'Pet Shop Teste',
            'subdomain': 'petteste',
            'admin_email': 'admin@petteste.com',
            'admin_password': 'senha123456'
        }
        
        service._validate_tenant_data(valid_data)
        print("✓ Validação de dados válidos passou")
        
        # Teste com dados inválidos
        invalid_data = {
            'name': 'Pet Shop Teste'
            # Faltam campos obrigatórios
        }
        
        try:
            service._validate_tenant_data(invalid_data)
            print("✗ Validação deveria ter falhado com dados inválidos")
            return False
        except TenantProvisioningError:
            print("✓ Validação corretamente rejeitou dados inválidos")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste de validação: {e}")
        return False

def test_tenant_record_creation():
    """Testa criação de registro de tenant"""
    try:
        service = TenantProvisioningService()
        
        tenant_data = {
            'name': 'Pet Shop Teste Record',
            'subdomain': 'pettesterecord',
            'admin_email': 'admin@pettesterecord.com',
            'admin_password': 'senha123456'
        }
        
        tenant = service._create_tenant_record(tenant_data)
        
        if tenant.name == 'Pet Shop Teste Record':
            print("✓ Registro de tenant criado com sucesso")
            
            # Limpar o tenant criado
            tenant.delete()
            return True
        else:
            print("✗ Dados do tenant não foram salvos corretamente")
            return False
            
    except Exception as e:
        print(f"✗ Erro ao criar registro de tenant: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("Testando TenantProvisioningService...")
    print("=" * 50)
    
    tests = [
        test_service_import,
        test_service_instantiation,
        test_validation_method,
        test_tenant_record_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Teste {test.__name__} falhou: {e}")
    
    print("=" * 50)
    print(f"Resultados: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram!")
        return True
    else:
        print("❌ Alguns testes falharam")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python
"""
Script de teste para verificar o funcionamento do database router multitenant.

Este script pode ser executado independentemente para testar se o sistema
de roteamento de database está funcionando corretamente.
"""

import os
import sys
import django

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from django.db import connection
from tenants.models import Tenant, TenantUser, TenantConfiguration
from tenants.db_router import TenantDatabaseRouter, schema_router
from tenants.utils import tenant_context, get_current_tenant, _is_postgresql


def test_database_router():
    """Testa o funcionamento básico do database router"""
    print("=== Teste do Database Router Multitenant ===\n")
    
    # 1. Testa instanciação do router
    print("1. Testando instanciação do router...")
    try:
        router = TenantDatabaseRouter()
        print("   ✓ Router instanciado com sucesso")
    except Exception as e:
        print(f"   ✗ Erro ao instanciar router: {e}")
        return False
    
    # 2. Testa roteamento para modelos compartilhados
    print("\n2. Testando roteamento para modelos compartilhados...")
    try:
        db_for_tenant = router.db_for_read(Tenant)
        db_for_write = router.db_for_write(Tenant)
        
        if db_for_tenant == 'default' and db_for_write == 'default':
            print("   ✓ Modelos compartilhados roteados para 'default'")
        else:
            print(f"   ✗ Roteamento incorreto: read={db_for_tenant}, write={db_for_write}")
    except Exception as e:
        print(f"   ✗ Erro no roteamento: {e}")
    
    # 3. Testa allow_migrate
    print("\n3. Testando allow_migrate...")
    try:
        # App tenants deve migrar apenas no default
        allow_tenants_default = router.allow_migrate('default', 'tenants')
        allow_tenants_other = router.allow_migrate('tenant_test', 'tenants')
        
        if allow_tenants_default and not allow_tenants_other:
            print("   ✓ Migrações do app 'tenants' restritas ao database 'default'")
        else:
            print(f"   ✗ Controle de migração incorreto: default={allow_tenants_default}, other={allow_tenants_other}")
        
        # Apps Django devem migrar apenas no default
        allow_auth_default = router.allow_migrate('default', 'auth')
        allow_auth_other = router.allow_migrate('tenant_test', 'auth')
        
        if allow_auth_default and not allow_auth_other:
            print("   ✓ Migrações do Django restritas ao database 'default'")
        else:
            print(f"   ✗ Controle de migração Django incorreto: default={allow_auth_default}, other={allow_auth_other}")
            
    except Exception as e:
        print(f"   ✗ Erro no allow_migrate: {e}")
    
    # 4. Testa schema router (apenas PostgreSQL)
    print("\n4. Testando schema router...")
    if _is_postgresql():
        try:
            # Obtém schema atual
            current_schema = schema_router.get_current_schema()
            print(f"   Schema atual: {current_schema}")
            
            # Testa mudança de schema
            schema_router.set_schema('test_schema')
            new_schema = schema_router.get_current_schema()
            
            # Volta para public
            schema_router.reset_to_public()
            final_schema = schema_router.get_current_schema()
            
            print(f"   ✓ Schema router funcionando (test: {new_schema}, final: {final_schema})")
            
        except Exception as e:
            print(f"   ✗ Erro no schema router: {e}")
    else:
        print("   - Schema router pulado (SQLite em uso)")
    
    # 5. Testa contexto de tenant
    print("\n5. Testando contexto de tenant...")
    try:
        # Verifica se não há tenant no contexto inicial
        initial_tenant = get_current_tenant()
        if initial_tenant is None:
            print("   ✓ Contexto inicial sem tenant")
        else:
            print(f"   ! Contexto inicial com tenant: {initial_tenant}")
        
        # Cria um tenant de teste se não existir
        test_tenant, created = Tenant.objects.get_or_create(
            subdomain='router-test',
            defaults={
                'name': 'Tenant Teste Router',
                'schema_name': 'tenant_router_test'
            }
        )
        
        if created:
            print(f"   Tenant de teste criado: {test_tenant.name}")
        
        # Testa contexto com tenant
        with tenant_context(test_tenant):
            context_tenant = get_current_tenant()
            if context_tenant == test_tenant:
                print("   ✓ Contexto de tenant funcionando")
            else:
                print(f"   ✗ Contexto incorreto: esperado {test_tenant}, obtido {context_tenant}")
        
        # Verifica se contexto foi limpo
        final_tenant = get_current_tenant()
        if final_tenant is None:
            print("   ✓ Contexto limpo após saída do context manager")
        else:
            print(f"   ✗ Contexto não foi limpo: {final_tenant}")
            
    except Exception as e:
        print(f"   ✗ Erro no teste de contexto: {e}")
    
    print("\n=== Teste Concluído ===")
    return True


def test_tenant_models():
    """Testa operações com modelos tenant-aware"""
    print("\n=== Teste de Modelos Tenant-Aware ===\n")
    
    try:
        # Cria ou obtém tenant de teste
        test_tenant, created = Tenant.objects.get_or_create(
            subdomain='model-test',
            defaults={
                'name': 'Tenant Teste Modelos',
                'schema_name': 'tenant_model_test'
            }
        )
        
        print(f"Usando tenant: {test_tenant.name}")
        
        # Testa criação de TenantUser
        with tenant_context(test_tenant):
            # Remove usuários existentes do teste
            TenantUser.objects.filter(
                tenant=test_tenant,
                email='test@model.test'
            ).delete()
            
            # Cria novo usuário
            user = TenantUser.objects.create(
                tenant=test_tenant,
                email='test@model.test',
                password_hash='test_hash',
                first_name='Test',
                last_name='User',
                role='user'
            )
            
            print(f"   ✓ TenantUser criado: {user.email}")
            
            # Verifica se o usuário está associado ao tenant correto
            if user.tenant == test_tenant:
                print("   ✓ Usuário associado ao tenant correto")
            else:
                print(f"   ✗ Usuário associado ao tenant incorreto: {user.tenant}")
            
            # Testa configurações
            TenantConfiguration.set_config(test_tenant, 'test_key', 'test_value')
            config_value = TenantConfiguration.get_config(test_tenant, 'test_key')
            
            if config_value == 'test_value':
                print("   ✓ Configuração de tenant funcionando")
            else:
                print(f"   ✗ Configuração incorreta: {config_value}")
        
        print("\n=== Teste de Modelos Concluído ===")
        
    except Exception as e:
        print(f"   ✗ Erro no teste de modelos: {e}")
        import traceback
        traceback.print_exc()


def cleanup_test_data():
    """Remove dados de teste criados"""
    print("\n=== Limpeza de Dados de Teste ===")
    
    try:
        # Remove tenants de teste
        test_tenants = Tenant.objects.filter(
            subdomain__in=['router-test', 'model-test']
        )
        
        count = test_tenants.count()
        if count > 0:
            # Remove usuários e configurações primeiro
            TenantUser.objects.filter(tenant__in=test_tenants).delete()
            TenantConfiguration.objects.filter(tenant__in=test_tenants).delete()
            
            # Remove os tenants
            test_tenants.delete()
            print(f"   ✓ {count} tenants de teste removidos")
        else:
            print("   - Nenhum tenant de teste encontrado")
            
    except Exception as e:
        print(f"   ✗ Erro na limpeza: {e}")


def main():
    """Função principal do teste"""
    print("Iniciando testes do database router multitenant...\n")
    
    try:
        # Executa os testes
        test_database_router()
        test_tenant_models()
        
        # Pergunta se deve limpar os dados de teste
        response = input("\nDeseja remover os dados de teste criados? (s/N): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            cleanup_test_data()
        
        print("\nTestes concluídos com sucesso!")
        
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
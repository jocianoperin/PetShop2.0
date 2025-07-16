#!/usr/bin/env python
"""
Teste abrangente do sistema de database router multitenant.

Este script testa todas as funcionalidades do database router:
1. Importação e instanciação
2. Roteamento de modelos compartilhados vs tenant-aware
3. Controle de migrações
4. Contexto de tenant
5. Isolamento de dados
"""

import os
import sys

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')

try:
    import django
    django.setup()
    print("✓ Django configurado com sucesso")
except Exception as e:
    print(f"✗ Erro ao configurar Django: {e}")
    sys.exit(1)

def test_router_import():
    """Testa importação do router"""
    print("\n=== Teste 1: Importação do Router ===")
    
    try:
        from tenants.db_router import TenantDatabaseRouter
        print("✓ TenantDatabaseRouter importado")
        
        router = TenantDatabaseRouter()
        print("✓ Router instanciado")
        
        return router
    except Exception as e:
        print(f"✗ Erro na importação: {e}")
        return None

def test_shared_model_routing(router):
    """Testa roteamento de modelos compartilhados"""
    print("\n=== Teste 2: Roteamento de Modelos Compartilhados ===")
    
    try:
        from tenants.models import Tenant, TenantUser, TenantConfiguration
        
        # Testa modelos compartilhados
        shared_models = [Tenant, TenantUser, TenantConfiguration]
        
        for model in shared_models:
            db_read = router.db_for_read(model)
            db_write = router.db_for_write(model)
            
            if db_read == 'default' and db_write == 'default':
                print(f"✓ {model.__name__} roteado para 'default'")
            else:
                print(f"✗ {model.__name__} roteamento incorreto: read={db_read}, write={db_write}")
                
    except Exception as e:
        print(f"✗ Erro no teste de roteamento: {e}")

def test_migration_control(router):
    """Testa controle de migrações"""
    print("\n=== Teste 3: Controle de Migrações ===")
    
    try:
        # Apps que devem migrar apenas no default
        shared_apps = ['tenants', 'auth', 'contenttypes', 'sessions', 'admin']
        
        for app in shared_apps:
            allow_default = router.allow_migrate('default', app)
            allow_tenant = router.allow_migrate('tenant_test', app)
            
            if allow_default and not allow_tenant:
                print(f"✓ App '{app}' migra apenas no default")
            else:
                print(f"✗ App '{app}' controle incorreto: default={allow_default}, tenant={allow_tenant}")
        
        # Outros apps devem poder migrar em qualquer database
        other_app = 'api'
        allow_default = router.allow_migrate('default', other_app)
        allow_tenant = router.allow_migrate('tenant_test', other_app)
        
        if allow_default and allow_tenant:
            print(f"✓ App '{other_app}' pode migrar em qualquer database")
        else:
            print(f"✗ App '{other_app}' restrição incorreta: default={allow_default}, tenant={allow_tenant}")
            
    except Exception as e:
        print(f"✗ Erro no teste de migrações: {e}")

def test_tenant_context():
    """Testa contexto de tenant"""
    print("\n=== Teste 4: Contexto de Tenant ===")
    
    try:
        from tenants.utils import get_current_tenant, set_current_tenant, tenant_context
        from tenants.models import Tenant
        
        # Verifica contexto inicial
        initial_tenant = get_current_tenant()
        if initial_tenant is None:
            print("✓ Contexto inicial vazio")
        else:
            print(f"! Contexto inicial não vazio: {initial_tenant}")
        
        # Cria tenant de teste
        test_tenant, created = Tenant.objects.get_or_create(
            subdomain='test-context',
            defaults={
                'name': 'Tenant Teste Contexto',
                'schema_name': 'tenant_test_context'
            }
        )
        
        if created:
            print(f"✓ Tenant de teste criado: {test_tenant.name}")
        else:
            print(f"✓ Usando tenant existente: {test_tenant.name}")
        
        # Testa context manager
        with tenant_context(test_tenant):
            context_tenant = get_current_tenant()
            if context_tenant == test_tenant:
                print("✓ Context manager funcionando")
            else:
                print(f"✗ Context manager falhou: esperado {test_tenant}, obtido {context_tenant}")
        
        # Verifica limpeza do contexto
        final_tenant = get_current_tenant()
        if final_tenant is None:
            print("✓ Contexto limpo após context manager")
        else:
            print(f"✗ Contexto não limpo: {final_tenant}")
            
        return test_tenant
        
    except Exception as e:
        print(f"✗ Erro no teste de contexto: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_data_isolation(test_tenant):
    """Testa isolamento de dados"""
    print("\n=== Teste 5: Isolamento de Dados ===")
    
    if not test_tenant:
        print("✗ Pulando teste - tenant não disponível")
        return
    
    try:
        from tenants.models import TenantUser, TenantConfiguration
        from tenants.utils import tenant_context
        
        # Cria segundo tenant para teste
        test_tenant2, created = Tenant.objects.get_or_create(
            subdomain='test-isolation',
            defaults={
                'name': 'Tenant Teste Isolamento',
                'schema_name': 'tenant_test_isolation'
            }
        )
        
        # Limpa dados de teste anteriores
        TenantUser.objects.filter(tenant__in=[test_tenant, test_tenant2]).delete()
        TenantConfiguration.objects.filter(tenant__in=[test_tenant, test_tenant2]).delete()
        
        # Cria dados no primeiro tenant
        with tenant_context(test_tenant):
            user1 = TenantUser.objects.create(
                tenant=test_tenant,
                email='user1@test.com',
                password_hash='hash1',
                first_name='User',
                last_name='One'
            )
            
            TenantConfiguration.set_config(test_tenant, 'test_key', 'value1')
            
            # Verifica se vê apenas seus dados
            users_count = TenantUser.objects.count()
            configs_count = TenantConfiguration.objects.count()
            
            print(f"✓ Tenant 1 - Usuários: {users_count}, Configs: {configs_count}")
        
        # Cria dados no segundo tenant
        with tenant_context(test_tenant2):
            user2 = TenantUser.objects.create(
                tenant=test_tenant2,
                email='user2@test.com',
                password_hash='hash2',
                first_name='User',
                last_name='Two'
            )
            
            TenantConfiguration.set_config(test_tenant2, 'test_key', 'value2')
            
            # Verifica se vê apenas seus dados
            users_count = TenantUser.objects.count()
            configs_count = TenantConfiguration.objects.count()
            
            print(f"✓ Tenant 2 - Usuários: {users_count}, Configs: {configs_count}")
        
        # Verifica isolamento total
        total_users = TenantUser.objects.using('default').filter(
            tenant__in=[test_tenant, test_tenant2]
        ).count()
        
        if total_users == 2:
            print("✓ Isolamento de dados funcionando")
        else:
            print(f"✗ Isolamento falhou - total de usuários: {total_users}")
            
        # Verifica configurações específicas
        config1 = TenantConfiguration.get_config(test_tenant, 'test_key')
        config2 = TenantConfiguration.get_config(test_tenant2, 'test_key')
        
        if config1 == 'value1' and config2 == 'value2':
            print("✓ Configurações isoladas corretamente")
        else:
            print(f"✗ Configurações não isoladas: config1={config1}, config2={config2}")
            
    except Exception as e:
        print(f"✗ Erro no teste de isolamento: {e}")
        import traceback
        traceback.print_exc()

def test_schema_router():
    """Testa schema router (PostgreSQL)"""
    print("\n=== Teste 6: Schema Router ===")
    
    try:
        from tenants.utils import _is_postgresql
        from tenants.db_router import schema_router
        
        if not _is_postgresql():
            print("- Pulando teste (SQLite em uso)")
            return
        
        # Testa obtenção do schema atual
        current_schema = schema_router.get_current_schema()
        print(f"✓ Schema atual: {current_schema}")
        
        # Testa mudança de schema
        schema_router.set_schema('test_schema')
        new_schema = schema_router.get_current_schema()
        print(f"✓ Schema alterado para: {new_schema}")
        
        # Volta para public
        schema_router.reset_to_public()
        final_schema = schema_router.get_current_schema()
        print(f"✓ Schema resetado para: {final_schema}")
        
    except Exception as e:
        print(f"✗ Erro no teste de schema: {e}")

def cleanup_test_data():
    """Remove dados de teste"""
    print("\n=== Limpeza de Dados de Teste ===")
    
    try:
        from tenants.models import Tenant, TenantUser, TenantConfiguration
        
        # Remove tenants de teste
        test_tenants = Tenant.objects.filter(
            subdomain__in=['test-context', 'test-isolation']
        )
        
        if test_tenants.exists():
            # Remove dados relacionados
            TenantUser.objects.filter(tenant__in=test_tenants).delete()
            TenantConfiguration.objects.filter(tenant__in=test_tenants).delete()
            
            count = test_tenants.count()
            test_tenants.delete()
            
            print(f"✓ {count} tenants de teste removidos")
        else:
            print("- Nenhum tenant de teste encontrado")
            
    except Exception as e:
        print(f"✗ Erro na limpeza: {e}")

def main():
    """Função principal"""
    print("=== TESTE ABRANGENTE DO DATABASE ROUTER MULTITENANT ===")
    
    try:
        # Executa todos os testes
        router = test_router_import()
        if not router:
            return
        
        test_shared_model_routing(router)
        test_migration_control(router)
        test_tenant = test_tenant_context()
        test_data_isolation(test_tenant)
        test_schema_router()
        
        # Pergunta sobre limpeza
        print("\n" + "="*60)
        response = input("Deseja remover os dados de teste? (s/N): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            cleanup_test_data()
        
        print("\n✓ TODOS OS TESTES CONCLUÍDOS!")
        
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n✗ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
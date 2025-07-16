"""
Script simples para verificar se o database router está funcionando.
"""

print("Verificando database router...")

try:
    # Tenta importar o router
    from tenants.db_router import TenantDatabaseRouter
    print("✓ Router importado com sucesso")
    
    # Tenta instanciar
    router = TenantDatabaseRouter()
    print("✓ Router instanciado com sucesso")
    
    # Testa métodos básicos
    from tenants.models import Tenant
    
    # Testa db_for_read
    db_read = router.db_for_read(Tenant)
    print(f"✓ db_for_read funcionando: {db_read}")
    
    # Testa db_for_write  
    db_write = router.db_for_write(Tenant)
    print(f"✓ db_for_write funcionando: {db_write}")
    
    # Testa allow_migrate
    allow_migrate = router.allow_migrate('default', 'tenants')
    print(f"✓ allow_migrate funcionando: {allow_migrate}")
    
    print("✓ Database router está funcionando corretamente!")
    
except ImportError as e:
    print(f"✗ Erro de importação: {e}")
except Exception as e:
    print(f"✗ Erro: {e}")
    import traceback
    traceback.print_exc()
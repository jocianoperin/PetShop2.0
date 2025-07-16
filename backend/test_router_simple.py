#!/usr/bin/env python
"""
Teste simples para verificar se o database router pode ser importado e instanciado.
"""

import os
import sys
import django

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')

try:
    django.setup()
    print("✓ Django configurado com sucesso")
except Exception as e:
    print(f"✗ Erro ao configurar Django: {e}")
    sys.exit(1)

try:
    from tenants.db_router import TenantDatabaseRouter
    print("✓ TenantDatabaseRouter importado com sucesso")
except Exception as e:
    print(f"✗ Erro ao importar TenantDatabaseRouter: {e}")
    sys.exit(1)

try:
    router = TenantDatabaseRouter()
    print("✓ TenantDatabaseRouter instanciado com sucesso")
except Exception as e:
    print(f"✗ Erro ao instanciar TenantDatabaseRouter: {e}")
    sys.exit(1)

try:
    from tenants.models import Tenant
    db_for_read = router.db_for_read(Tenant)
    db_for_write = router.db_for_write(Tenant)
    print(f"✓ Roteamento funcionando - Read: {db_for_read}, Write: {db_for_write}")
except Exception as e:
    print(f"✗ Erro no roteamento: {e}")
    sys.exit(1)

print("✓ Todos os testes básicos passaram!")
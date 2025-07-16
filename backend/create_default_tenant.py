#!/usr/bin/env python
"""
Script para criar um tenant padrão para migração.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant

def create_default_tenant():
    """Cria um tenant padrão se não existir"""
    tenant, created = Tenant.objects.get_or_create(
        subdomain='default',
        defaults={
            'name': 'Default Tenant',
            'schema_name': 'tenant_default'
        }
    )
    
    if created:
        print(f"Tenant padrão criado: {tenant.id}")
    else:
        print(f"Tenant padrão já existe: {tenant.id}")
    
    return tenant

if __name__ == '__main__':
    tenant = create_default_tenant()
    print(f"Tenant ID: {tenant.id}")
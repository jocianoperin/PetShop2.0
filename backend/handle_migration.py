#!/usr/bin/env python
"""
Script para lidar com a migração dos modelos tenant-aware.
"""
import os
import sys
import django
import subprocess

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant

def create_default_tenant():
    """Cria um tenant padrão"""
    tenant, created = Tenant.objects.get_or_create(
        subdomain='default',
        defaults={
            'name': 'Default Tenant',
            'schema_name': 'tenant_default'
        }
    )
    print(f"Default tenant: {tenant.id} ({'created' if created else 'exists'})")
    return tenant

def run_makemigrations():
    """Executa makemigrations com input automático"""
    try:
        # Primeiro, criar o tenant padrão
        default_tenant = create_default_tenant()
        
        # Executar makemigrations
        result = subprocess.run([
            sys.executable, 'manage.py', 'makemigrations', 'api'
        ], input=f"1\n{default_tenant.id}\n", text=True, capture_output=True)
        
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    run_makemigrations()
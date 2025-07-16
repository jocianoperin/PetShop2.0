#!/usr/bin/env python
"""
Simple test for tenant registration functionality.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant, TenantUser
from tenants.services import tenant_provisioning_service

def test_tenant_creation():
    """Test tenant creation service directly"""
    print("Testing tenant creation service...")
    
    # Test data
    tenant_data = {
        'name': 'Pet Shop Teste Direto',
        'subdomain': 'testdireto123',
        'admin_email': 'admin@testdireto.com',
        'admin_password': 'senha123456',
        'admin_first_name': 'Admin',
        'admin_last_name': 'Teste',
        'plan_type': 'basic'
    }
    
    # Clean up existing data
    try:
        existing_tenant = Tenant.objects.get(subdomain=tenant_data['subdomain'])
        print(f"Cleaning up existing tenant: {existing_tenant.name}")
        existing_tenant.delete()
    except Tenant.DoesNotExist:
        pass
    
    try:
        existing_user = TenantUser.objects.get(email=tenant_data['admin_email'])
        print(f"Cleaning up existing user: {existing_user.email}")
        existing_user.delete()
    except TenantUser.DoesNotExist:
        pass
    
    try:
        # Create tenant
        print("Creating tenant...")
        tenant = tenant_provisioning_service.create_tenant(tenant_data)
        
        print(f"✅ Tenant created successfully:")
        print(f"   - ID: {tenant.id}")
        print(f"   - Name: {tenant.name}")
        print(f"   - Subdomain: {tenant.subdomain}")
        print(f"   - Schema: {tenant.schema_name}")
        print(f"   - Active: {tenant.is_active}")
        
        # Verify admin user
        admin_user = TenantUser.objects.get(
            tenant=tenant,
            email=tenant_data['admin_email'],
            role='admin'
        )
        
        print(f"✅ Admin user created:")
        print(f"   - Email: {admin_user.email}")
        print(f"   - Name: {admin_user.full_name}")
        print(f"   - Role: {admin_user.role}")
        print(f"   - Active: {admin_user.is_active}")
        
        # Validate provisioning
        print("\nValidating provisioning...")
        validation = tenant_provisioning_service.validate_tenant_provisioning(tenant)
        
        if validation['valid']:
            print("✅ Tenant provisioning validation passed")
        else:
            print("❌ Tenant provisioning validation failed:")
            for error in validation['errors']:
                print(f"   - {error}")
        
        print(f"\nValidation details: {validation['checks']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tenant: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Starting simple tenant registration test...")
    success = test_tenant_creation()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
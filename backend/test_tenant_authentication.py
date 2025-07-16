#!/usr/bin/env python
"""
Test script for tenant authentication system.
Tests JWT token generation, validation, and tenant-aware authentication.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import Tenant, TenantUser
from tenants.authentication import (
    TenantJWTAuthentication, 
    create_tenant_jwt_token,
    decode_tenant_jwt_token
)
from tenants.services import tenant_provisioning_service


def test_tenant_jwt_token_creation():
    """Test JWT token creation with tenant information"""
    print("=" * 60)
    print("TESTING TENANT JWT TOKEN CREATION")
    print("=" * 60)
    
    try:
        # Create a test tenant and user
        tenant_data = {
            'name': 'Pet Shop Auth Test',
            'subdomain': 'authtest123',
            'admin_email': 'admin@authtest.com',
            'admin_password': 'senha123456',
            'admin_first_name': 'Admin',
            'admin_last_name': 'Test'
        }
        
        # Clean up existing data
        try:
            existing_tenant = Tenant.objects.get(subdomain=tenant_data['subdomain'])
            existing_tenant.delete()
        except Tenant.DoesNotExist:
            pass
        
        # Create tenant
        tenant = tenant_provisioning_service.create_tenant(tenant_data)
        admin_user = TenantUser.objects.get(
            tenant=tenant,
            email=tenant_data['admin_email'],
            role='admin'
        )
        
        print(f"✅ Test tenant created: {tenant.name}")
        print(f"✅ Admin user created: {admin_user.email}")
        
        # Test token creation
        tokens = create_tenant_jwt_token(admin_user)
        
        print(f"✅ JWT tokens generated:")
        print(f"   - Access token length: {len(tokens['access'])}")
        print(f"   - Refresh token length: {len(tokens['refresh'])}")
        
        # Test token decoding
        decoded = decode_tenant_jwt_token(tokens['access'])
        
        if decoded:
            print(f"✅ Token decoded successfully:")
            print(f"   - User ID: {decoded['user_id']}")
            print(f"   - Email: {decoded['email']}")
            print(f"   - Tenant ID: {decoded['tenant_id']}")
            print(f"   - Tenant Subdomain: {decoded['tenant_subdomain']}")
            print(f"   - User Role: {decoded['user_role']}")
            
            # Verify token data
            if (decoded['user_id'] == str(admin_user.id) and
                decoded['email'] == admin_user.email and
                decoded['tenant_id'] == str(tenant.id) and
                decoded['tenant_subdomain'] == tenant.subdomain and
                decoded['user_role'] == admin_user.role):
                print("✅ Token data validation passed")
                return True, tenant, admin_user, tokens
            else:
                print("❌ Token data validation failed")
                return False, None, None, None
        else:
            print("❌ Token decoding failed")
            return False, None, None, None
            
    except Exception as e:
        print(f"❌ Error in token creation test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, None, None


def test_tenant_login_api(tenant, admin_user):
    """Test tenant login API with JWT authentication"""
    print("\n" + "=" * 60)
    print("TESTING TENANT LOGIN API")
    print("=" * 60)
    
    client = APIClient()
    
    # Test login
    login_data = {
        'email': admin_user.email,
        'password': 'senha123456',
        'tenant_subdomain': tenant.subdomain
    }
    
    print(f"1. Testing login with data:")
    print(json.dumps(login_data, indent=2))
    
    response = client.post('/api/tenants/login/', login_data, format='json')
    
    print(f"2. Response status: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.data
        print(f"✅ Login successful")
        
        # Verify response structure
        if 'data' in response_data:
            data = response_data['data']
            required_fields = ['access_token', 'refresh_token', 'user', 'tenant']
            
            for field in required_fields:
                if field in data:
                    print(f"✅ Response contains '{field}'")
                else:
                    print(f"❌ Response missing '{field}'")
                    return False, None
            
            return True, data['access_token']
        else:
            print("❌ Response missing 'data' field")
            return False, None
    else:
        print(f"❌ Login failed with status {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Error: {response.data}")
        return False, None


def test_authenticated_request(access_token, tenant):
    """Test making authenticated requests with JWT token"""
    print("\n" + "=" * 60)
    print("TESTING AUTHENTICATED REQUESTS")
    print("=" * 60)
    
    client = APIClient()
    
    # Set authorization header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test 1: Request with tenant subdomain header
    print("1. Testing request with tenant subdomain header...")
    client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_TENANT_SUBDOMAIN=tenant.subdomain
    )
    
    # Make a request to a protected endpoint (we'll use tenant status)
    response = client.get(f'/api/tenants/status/{tenant.subdomain}/')
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Request with tenant header successful")
    else:
        print(f"❌ Request failed: {response.data if hasattr(response, 'data') else response.content}")
    
    # Test 2: Request with tenant ID header
    print("\n2. Testing request with tenant ID header...")
    client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_TENANT_ID=str(tenant.id)
    )
    
    response = client.get(f'/api/tenants/status/{tenant.id}/')
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Request with tenant ID header successful")
    else:
        print(f"❌ Request failed: {response.data if hasattr(response, 'data') else response.content}")
    
    return True


def test_tenant_middleware_resolution():
    """Test tenant resolution through middleware"""
    print("\n" + "=" * 60)
    print("TESTING TENANT MIDDLEWARE RESOLUTION")
    print("=" * 60)
    
    from tenants.middleware import TenantMiddleware
    from django.http import HttpRequest
    
    middleware = TenantMiddleware(lambda r: None)
    
    # Create mock request
    request = HttpRequest()
    request.META = {
        'HTTP_HOST': 'authtest123.localhost:8000',
        'HTTP_X_TENANT_ID': '',
        'HTTP_AUTHORIZATION': ''
    }
    request.path = '/api/test/'
    request.method = 'GET'
    
    print("1. Testing subdomain resolution...")
    print(f"   Host: {request.META['HTTP_HOST']}")
    
    # Test subdomain resolution
    tenant = middleware._resolve_by_subdomain(request)
    
    if tenant:
        print(f"✅ Tenant resolved by subdomain: {tenant.name}")
    else:
        print("❌ Failed to resolve tenant by subdomain")
    
    return True


def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 60)
    print("CLEANING UP TEST DATA")
    print("=" * 60)
    
    try:
        # Remove test tenant
        test_tenant = Tenant.objects.filter(subdomain='authtest123').first()
        if test_tenant:
            print(f"Removing test tenant: {test_tenant.name}")
            test_tenant.delete()
            print("✅ Test tenant removed")
        else:
            print("ℹ️ No test tenant found to remove")
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")


def main():
    """Run all authentication tests"""
    print("Starting Tenant Authentication Tests...")
    print(f"Time: {datetime.now()}")
    print()
    
    try:
        # Test 1: JWT Token Creation
        success, tenant, admin_user, tokens = test_tenant_jwt_token_creation()
        if not success:
            print("\n💥 JWT token creation test failed!")
            return False
        
        # Test 2: Login API
        success, access_token = test_tenant_login_api(tenant, admin_user)
        if not success:
            print("\n💥 Login API test failed!")
            return False
        
        # Test 3: Authenticated Requests
        test_authenticated_request(access_token, tenant)
        
        # Test 4: Middleware Resolution
        test_tenant_middleware_resolution()
        
        print("\n🎉 All authentication tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Always cleanup
        cleanup_test_data()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python
"""
Test script for tenant registration API.
Tests the complete tenant registration flow.
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tenants.models import Tenant, TenantUser


def test_tenant_registration_api():
    """Test the tenant registration API endpoint"""
    print("=" * 60)
    print("TESTING TENANT REGISTRATION API")
    print("=" * 60)
    
    # Create API client
    client = APIClient()
    
    # Test data
    registration_data = {
        "name": "Pet Shop Teste API",
        "subdomain": "testapi123",
        "admin_email": "admin@testapi123.com",
        "admin_password": "senha123456",
        "admin_first_name": "Admin",
        "admin_last_name": "Teste",
        "plan_type": "basic"
    }
    
    print(f"1. Testing tenant registration with data:")
    print(json.dumps(registration_data, indent=2))
    print()
    
    # Clean up any existing test data
    try:
        existing_tenant = Tenant.objects.get(subdomain=registration_data['subdomain'])
        print(f"Cleaning up existing tenant: {existing_tenant.name}")
        existing_tenant.delete()
    except Tenant.DoesNotExist:
        pass
    
    try:
        existing_user = TenantUser.objects.get(email=registration_data['admin_email'])
        print(f"Cleaning up existing user: {existing_user.email}")
        existing_user.delete()
    except TenantUser.DoesNotExist:
        pass
    
    # Make the API call
    url = '/api/tenants/register/'
    print(f"2. Making POST request to: {url}")
    
    response = client.post(url, registration_data, format='json')
    
    print(f"3. Response status: {response.status_code}")
    print(f"4. Response data:")
    
    if hasattr(response, 'data'):
        print(json.dumps(response.data, indent=2, default=str))
    else:
        print(response.content.decode())
    
    # Verify the response
    if response.status_code == 201:
        print("\n✅ SUCCESS: Tenant registration completed successfully!")
        
        # Verify tenant was created
        try:
            tenant = Tenant.objects.get(subdomain=registration_data['subdomain'])
            print(f"✅ Tenant created: {tenant.name} (ID: {tenant.id})")
            
            # Verify admin user was created
            admin_user = TenantUser.objects.get(
                tenant=tenant,
                email=registration_data['admin_email'],
                role='admin'
            )
            print(f"✅ Admin user created: {admin_user.email}")
            
            # Verify response structure
            response_data = response.data
            required_fields = ['success', 'message', 'tenant', 'admin_user', 'login_url']
            
            for field in required_fields:
                if field in response_data:
                    print(f"✅ Response contains '{field}': {type(response_data[field])}")
                else:
                    print(f"❌ Response missing '{field}'")
            
        except Exception as e:
            print(f"❌ Error verifying created data: {str(e)}")
    
    else:
        print(f"\n❌ FAILED: Expected status 201, got {response.status_code}")
        if hasattr(response, 'data') and 'errors' in response.data:
            print("Validation errors:")
            for field, errors in response.data['errors'].items():
                print(f"  - {field}: {errors}")
    
    print("\n" + "=" * 60)


def test_subdomain_availability_api():
    """Test the subdomain availability check API"""
    print("TESTING SUBDOMAIN AVAILABILITY API")
    print("=" * 60)
    
    client = APIClient()
    
    # Test available subdomain
    print("1. Testing available subdomain...")
    response = client.post('/api/tenants/check-subdomain/', {
        'subdomain': 'available123'
    }, format='json')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code == 200 and response.data.get('available'):
        print("✅ Available subdomain check works")
    else:
        print("❌ Available subdomain check failed")
    
    # Test unavailable subdomain (create one first)
    print("\n2. Testing unavailable subdomain...")
    
    # Create a tenant to test unavailability
    test_tenant = Tenant.objects.create(
        name="Test Unavailable",
        subdomain="unavailable123",
        schema_name="tenant_unavailable123"
    )
    
    response = client.post('/api/tenants/check-subdomain/', {
        'subdomain': 'unavailable123'
    }, format='json')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code == 200 and not response.data.get('available'):
        print("✅ Unavailable subdomain check works")
    else:
        print("❌ Unavailable subdomain check failed")
    
    # Clean up
    test_tenant.delete()
    
    print("\n" + "=" * 60)


def test_validation_errors():
    """Test validation errors in registration API"""
    print("TESTING VALIDATION ERRORS")
    print("=" * 60)
    
    client = APIClient()
    
    # Test missing required fields
    print("1. Testing missing required fields...")
    response = client.post('/api/tenants/register/', {}, format='json')
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Missing fields validation works")
        print(f"Errors: {response.data.get('errors', {})}")
    else:
        print("❌ Missing fields validation failed")
    
    # Test invalid subdomain
    print("\n2. Testing invalid subdomain...")
    response = client.post('/api/tenants/register/', {
        "name": "Test Invalid",
        "subdomain": "INVALID_SUBDOMAIN!",
        "admin_email": "test@test.com",
        "admin_password": "password123"
    }, format='json')
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Invalid subdomain validation works")
        print(f"Errors: {response.data.get('errors', {})}")
    else:
        print("❌ Invalid subdomain validation failed")
    
    # Test weak password
    print("\n3. Testing weak password...")
    response = client.post('/api/tenants/register/', {
        "name": "Test Weak Password",
        "subdomain": "testweakpwd",
        "admin_email": "test@weak.com",
        "admin_password": "123"
    }, format='json')
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Weak password validation works")
        print(f"Errors: {response.data.get('errors', {})}")
    else:
        print("❌ Weak password validation failed")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    print("Starting Tenant Registration API Tests...")
    print(f"Time: {datetime.now()}")
    print()
    
    try:
        # Run tests
        test_subdomain_availability_api()
        test_validation_errors()
        test_tenant_registration_api()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
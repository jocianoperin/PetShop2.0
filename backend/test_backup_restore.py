#!/usr/bin/env python
"""
Test script for backup and restore functionality.
"""

import os
import sys
import json
import datetime
import tempfile
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
import django
django.setup()

from django.utils import timezone
from django.db import connection
from django.core.management import call_command

from tenants.models import Tenant, TenantConfiguration
from tenants.utils import tenant_context, _is_postgresql


def test_backup_restore():
    """Test backup and restore functionality"""
    print("Testing backup and restore functionality...")
    
    # Get first active tenant
    tenant = Tenant.objects.filter(is_active=True).first()
    if not tenant:
        print("No active tenants found. Test cannot continue.")
        return
    
    print(f"Using tenant: {tenant.name} ({tenant.subdomain})")
    
    # Create temporary directory for backups
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # 1. Create backup
        print("\n1. Creating backup...")
        call_command('backup_tenant', tenant_id=str(tenant.id), output_dir=temp_dir)
        
        # Check if backup was created
        tenant_backup_dir = os.path.join(temp_dir, tenant.schema_name)
        backup_files = [f for f in os.listdir(tenant_backup_dir) if f.endswith('.json') or f.endswith('.json.gz')]
        
        if not backup_files:
            print("No backup files created. Test failed.")
            return
        
        backup_file = os.path.join(tenant_backup_dir, backup_files[0])
        print(f"Backup created: {backup_file}")
        
        # 2. Modify some data to verify restore
        print("\n2. Modifying data for testing restore...")
        with tenant_context(tenant):
            # Get count of records before modification
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM api_cliente")
                before_count = cursor.fetchone()[0]
                
                # Add a test record
                cursor.execute(
                    "INSERT INTO api_cliente (nome, email, telefone, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    ["TEST_BACKUP_RESTORE", "test_backup@example.com", "123456789", timezone.now(), timezone.now()]
                )
                
                # Verify record was added
                cursor.execute("SELECT COUNT(*) FROM api_cliente")
                after_count = cursor.fetchone()[0]
                
                print(f"Added test record. Clients before: {before_count}, after: {after_count}")
        
        # 3. Restore backup
        print("\n3. Restoring backup...")
        call_command('restore_tenant', backup_file, tenant_id=str(tenant.id), force=True)
        
        # 4. Verify data was restored
        print("\n4. Verifying restored data...")
        with tenant_context(tenant):
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM api_cliente")
                restored_count = cursor.fetchone()[0]
                
                # Check if test record exists
                cursor.execute(
                    "SELECT COUNT(*) FROM api_cliente WHERE email = %s",
                    ["test_backup@example.com"]
                )
                test_record_count = cursor.fetchone()[0]
                
                print(f"Clients after restore: {restored_count}")
                print(f"Test record exists: {test_record_count > 0}")
                
                if restored_count == before_count and test_record_count == 0:
                    print("\nRestore test PASSED: Data was restored to original state.")
                else:
                    print("\nRestore test FAILED: Data was not restored correctly.")
    
    # 5. Test scheduling
    print("\n5. Testing backup scheduling...")
    
    # Schedule daily backup
    call_command('schedule_tenant_backups', tenant_id=str(tenant.id), frequency='daily', time='03:00')
    
    # Verify schedule was created
    schedule = TenantConfiguration.get_config(tenant, 'backup_schedule')
    next_backup = TenantConfiguration.get_config(tenant, 'next_scheduled_backup')
    
    if schedule and next_backup:
        print("Backup schedule created successfully:")
        print(f"  Frequency: {schedule.get('frequency')}")
        print(f"  Time: {schedule.get('time')}")
        print(f"  Next backup: {next_backup}")
        print("\nScheduling test PASSED.")
    else:
        print("\nScheduling test FAILED: Schedule was not created.")
    
    # 6. List schedules
    print("\n6. Listing backup schedules...")
    call_command('schedule_tenant_backups', list_schedules=True)
    
    print("\nBackup and restore test completed.")


if __name__ == '__main__':
    test_backup_restore()
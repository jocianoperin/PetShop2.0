"""
Management command to restore tenant data from a backup.
"""

import os
import json
import gzip
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.conf import settings
from django.utils import timezone

from tenants.models import Tenant, TenantConfiguration
from tenants.utils import tenant_context, _is_postgresql, create_tenant_schema
from tenants.services import tenant_provisioning_service


logger = logging.getLogger('tenants.restore')


class Command(BaseCommand):
    help = 'Restore tenant data from a backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            help='Path to the backup file to restore'
        )
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            help='ID or subdomain of the tenant to restore to (required for cross-tenant restore)'
        )
        parser.add_argument(
            '--create-if-missing',
            action='store_true',
            dest='create_if_missing',
            default=False,
            help='Create the tenant if it does not exist'
        )
        parser.add_argument(
            '--include-files',
            action='store_true',
            dest='include_files',
            default=False,
            help='Restore tenant-specific files from backup'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force restore even if tenant has existing data'
        )
        parser.add_argument(
            '--skip-tables',
            dest='skip_tables',
            help='Comma-separated list of tables to skip during restore'
        )
        parser.add_argument(
            '--only-tables',
            dest='only_tables',
            help='Comma-separated list of tables to restore (exclusive with --skip-tables)'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            dest='validate',
            default=True,
            help='Validate data integrity after restore'
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        tenant_id = options['tenant_id']
        create_if_missing = options['create_if_missing']
        include_files = options['include_files']
        force = options['force']
        skip_tables = options['skip_tables'].split(',') if options['skip_tables'] else []
        only_tables = options['only_tables'].split(',') if options['only_tables'] else []
        validate = options['validate']

        # Check if backup file exists
        if not os.path.exists(backup_file):
            raise CommandError(f"Backup file not found: {backup_file}")

        # Load backup data
        try:
            if backup_file.endswith('.gz'):
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to load backup file: {str(e)}")

        # Extract metadata
        metadata = backup_data.get('metadata', {})
        if not metadata:
            raise CommandError("Invalid backup file: missing metadata")

        self.stdout.write(f"Backup information:")
        self.stdout.write(f"  Tenant: {metadata.get('tenant_name')} ({metadata.get('subdomain')})")
        self.stdout.write(f"  Schema: {metadata.get('schema_name')}")
        self.stdout.write(f"  Backup date: {metadata.get('backup_date')}")
        self.stdout.write(f"  Backup type: {metadata.get('backup_type', 'full')}")

        # Determine target tenant
        target_tenant = None
        if tenant_id:
            # Try to get by ID first
            try:
                target_tenant = Tenant.objects.get(id=tenant_id)
            except (Tenant.DoesNotExist, ValueError):
                # If not found or not a valid UUID, try by subdomain
                try:
                    target_tenant = Tenant.objects.get(subdomain=tenant_id)
                except Tenant.DoesNotExist:
                    if create_if_missing:
                        self.stdout.write(f"Tenant '{tenant_id}' not found, creating...")
                        target_tenant = self._create_tenant_from_backup(backup_data)
                    else:
                        raise CommandError(f"Tenant with ID or subdomain '{tenant_id}' not found")
        else:
            # Try to find tenant by subdomain from backup
            subdomain = metadata.get('subdomain')
            if not subdomain:
                raise CommandError("Cannot determine target tenant: no subdomain in backup and no tenant specified")
            
            try:
                target_tenant = Tenant.objects.get(subdomain=subdomain)
            except Tenant.DoesNotExist:
                if create_if_missing:
                    self.stdout.write(f"Tenant '{subdomain}' not found, creating...")
                    target_tenant = self._create_tenant_from_backup(backup_data)
                else:
                    raise CommandError(
                        f"Tenant with subdomain '{subdomain}' not found. "
                        f"Use --create-if-missing to create it."
                    )

        # Check if tenant has existing data
        if not force:
            with tenant_context(target_tenant):
                # Check if any tables have data
                has_data = False
                for table_name in backup_data.get('tables', {}).keys():
                    if table_name in skip_tables:
                        continue
                    if only_tables and table_name not in only_tables:
                        continue
                    
                    with connection.cursor() as cursor:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            if count > 0:
                                has_data = True
                                break
                        except Exception:
                            # Table might not exist, which is fine
                            pass
                
                if has_data:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Target tenant '{target_tenant.name}' already has data. "
                            f"Use --force to override."
                        )
                    )
                    return

        # Perform restore
        try:
            result = self._restore_tenant(
                target_tenant, 
                backup_data, 
                skip_tables=skip_tables,
                only_tables=only_tables,
                include_files=include_files
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully restored tenant '{target_tenant.name}' from backup"
                )
            )
            
            # Show restore summary
            self.stdout.write("\nRestore Summary:")
            self.stdout.write(f"Tables restored: {result['tables_restored']}")
            self.stdout.write(f"Records restored: {result['records_restored']}")
            self.stdout.write(f"Configurations restored: {result['configs_restored']}")
            
            if include_files:
                self.stdout.write(f"Files restored: {result['files_restored']}")
            
            # Validate if requested
            if validate:
                self.stdout.write("\nValidating restored data...")
                validation = tenant_provisioning_service.validate_tenant_provisioning(target_tenant)
                
                if validation['valid']:
                    self.stdout.write(self.style.SUCCESS("Validation successful"))
                else:
                    self.stdout.write(self.style.ERROR("Validation failed:"))
                    for error in validation['errors']:
                        self.stdout.write(f"  - {error}")
                    for warning in validation['warnings']:
                        self.stdout.write(self.style.WARNING(f"  - {warning}"))
            
        except Exception as e:
            logger.error(f"Error restoring tenant {target_tenant.name}: {str(e)}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f"Failed to restore tenant '{target_tenant.name}': {str(e)}")
            )

    def _create_tenant_from_backup(self, backup_data):
        """
        Create a new tenant based on backup metadata
        
        Args:
            backup_data: The loaded backup data
            
        Returns:
            Tenant: The newly created tenant
        """
        metadata = backup_data.get('metadata', {})
        
        # Create tenant with minimal data
        tenant_data = {
            'name': metadata.get('tenant_name', 'Restored Tenant'),
            'subdomain': metadata.get('subdomain', f"restored-{timezone.now().strftime('%Y%m%d%H%M%S')}"),
            'admin_email': 'admin@example.com',  # Temporary admin
            'admin_password': 'TemporaryPassword123!',  # Temporary password
        }
        
        # Create tenant with schema
        tenant = tenant_provisioning_service.create_tenant(tenant_data)
        
        self.stdout.write(
            self.style.SUCCESS(f"Created new tenant '{tenant.name}' with subdomain '{tenant.subdomain}'")
        )
        self.stdout.write(
            self.style.WARNING(
                f"IMPORTANT: Temporary admin credentials created:\n"
                f"  Email: {tenant_data['admin_email']}\n"
                f"  Password: {tenant_data['admin_password']}\n"
                f"Please change these credentials immediately after restore!"
            )
        )
        
        return tenant

    def _restore_tenant(self, tenant, backup_data, skip_tables=None, only_tables=None, include_files=False):
        """
        Restore tenant data from backup
        
        Args:
            tenant: Target tenant to restore to
            backup_data: The loaded backup data
            skip_tables: List of tables to skip
            only_tables: List of tables to restore (exclusive with skip_tables)
            include_files: Whether to restore tenant files
            
        Returns:
            dict: Restore result information
        """
        skip_tables = skip_tables or []
        only_tables = only_tables or []
        
        # Initialize counters
        tables_restored = 0
        records_restored = 0
        configs_restored = 0
        files_restored = 0
        
        # Start transaction
        with transaction.atomic():
            # Restore configurations
            if 'configurations' in backup_data:
                for config in backup_data['configurations']:
                    # Skip internal configurations
                    if config['config_key'].startswith('_'):
                        continue
                    
                    # Create or update configuration
                    TenantConfiguration.set_config(
                        tenant=tenant,
                        key=config['config_key'],
                        value=config['config_value'],
                        config_type=config['config_type'],
                        is_sensitive=config['is_sensitive']
                    )
                    configs_restored += 1
            
            # Restore table data
            with tenant_context(tenant):
                for table_name, table_data in backup_data.get('tables', {}).items():
                    # Skip tables if requested
                    if table_name in skip_tables:
                        continue
                    if only_tables and table_name not in only_tables:
                        continue
                    
                    # Check if table exists
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                    except Exception:
                        self.stdout.write(
                            self.style.WARNING(f"Table '{table_name}' does not exist, skipping")
                        )
                        continue
                    
                    # Clear existing data if any
                    with connection.cursor() as cursor:
                        cursor.execute(f"DELETE FROM {table_name}")
                    
                    # Get columns and rows
                    columns = table_data.get('columns', [])
                    rows = table_data.get('rows', [])
                    
                    if not columns or not rows:
                        continue
                    
                    # Insert data
                    for row_data in rows:
                        # Prepare values in the correct order
                        values = []
                        placeholders = []
                        
                        for col in columns:
                            if col in row_data:
                                values.append(row_data[col])
                                placeholders.append('%s')
                            else:
                                placeholders.append('NULL')
                        
                        # Build and execute INSERT statement
                        columns_str = ', '.join(columns)
                        placeholders_str = ', '.join(placeholders)
                        
                        with connection.cursor() as cursor:
                            cursor.execute(
                                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})",
                                values
                            )
                        
                        records_restored += 1
                    
                    tables_restored += 1
                    
                    self.stdout.write(
                        f"Restored table '{table_name}': {len(rows)} records"
                    )
            
            # Restore files if requested
            if include_files:
                # Check if backup has associated files directory
                backup_file_path = os.path.abspath(backup_data['metadata'].get('backup_file', ''))
                if backup_file_path:
                    backup_dir = os.path.dirname(backup_file_path)
                    timestamp = backup_file_path.split('_')[-1].split('.')[0]
                    files_backup_dir = os.path.join(backup_dir, f"files_{timestamp}")
                    
                    if os.path.exists(files_backup_dir) and os.path.isdir(files_backup_dir):
                        # Restore files to tenant media directory
                        tenant_media_dir = os.path.join(settings.MEDIA_ROOT, f"tenant_{tenant.id}")
                        os.makedirs(tenant_media_dir, exist_ok=True)
                        
                        import shutil
                        
                        # Copy files from backup to tenant directory
                        for root, dirs, files in os.walk(files_backup_dir):
                            for file in files:
                                src_path = os.path.join(root, file)
                                rel_path = os.path.relpath(src_path, files_backup_dir)
                                dst_path = os.path.join(tenant_media_dir, rel_path)
                                
                                # Ensure destination directory exists
                                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                                
                                # Copy file
                                shutil.copy2(src_path, dst_path)
                                files_restored += 1
            
            # Record restore in tenant configuration
            TenantConfiguration.set_config(
                tenant=tenant,
                key='last_restore_date',
                value=timezone.now().isoformat(),
                config_type='string'
            )
            
            TenantConfiguration.set_config(
                tenant=tenant,
                key='last_restore_source',
                value=backup_data['metadata'].get('backup_file', 'unknown'),
                config_type='string'
            )
        
        # Return restore information
        return {
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'tables_restored': tables_restored,
            'records_restored': records_restored,
            'configs_restored': configs_restored,
            'files_restored': files_restored,
            'restore_date': timezone.now().isoformat()
        }
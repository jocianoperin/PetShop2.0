"""
Management command to backup tenant data.
Creates a backup of a specific tenant's data or all tenants.
"""

import os
import json
import gzip
import datetime
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from tenants.models import Tenant, TenantConfiguration
from tenants.utils import tenant_context, _is_postgresql, list_tenant_tables, get_tenant_database_size


logger = logging.getLogger('tenants.backup')


class Command(BaseCommand):
    help = 'Create a backup of tenant data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            help='ID or subdomain of the tenant to backup (omit for all tenants)'
        )
        parser.add_argument(
            '--output-dir',
            dest='output_dir',
            default=None,
            help='Directory to store backup files (default: BACKUP_DIR setting or "backups" folder)'
        )
        parser.add_argument(
            '--include-files',
            action='store_true',
            dest='include_files',
            default=False,
            help='Include tenant-specific files in backup'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            dest='compress',
            default=True,
            help='Compress backup files (default: True)'
        )
        parser.add_argument(
            '--no-compress',
            action='store_false',
            dest='compress',
            help='Do not compress backup files'
        )

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        output_dir = options['output_dir']
        include_files = options['include_files']
        compress = options['compress']

        # Determine backup directory
        if output_dir is None:
            output_dir = getattr(settings, 'BACKUP_DIR', None)
            if output_dir is None:
                output_dir = os.path.join(settings.BASE_DIR, 'backups')

        # Ensure backup directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Get tenant(s) to backup
        if tenant_id:
            try:
                # Try to get by ID first
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                except (Tenant.DoesNotExist, ValueError):
                    # If not found or not a valid UUID, try by subdomain
                    tenant = Tenant.objects.get(subdomain=tenant_id)
                tenants = [tenant]
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant with ID or subdomain '{tenant_id}' not found")
        else:
            # Backup all active tenants
            tenants = Tenant.objects.filter(is_active=True)
            if not tenants.exists():
                self.stdout.write(self.style.WARNING("No active tenants found"))
                return

        # Create backups
        backup_results = []
        for tenant in tenants:
            try:
                result = self._backup_tenant(tenant, output_dir, include_files, compress)
                backup_results.append(result)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully backed up tenant '{tenant.name}' to {result['backup_file']}"
                    )
                )
            except Exception as e:
                logger.error(f"Error backing up tenant {tenant.name}: {str(e)}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f"Failed to backup tenant '{tenant.name}': {str(e)}")
                )

        # Summary
        self.stdout.write("\nBackup Summary:")
        self.stdout.write(f"Total tenants processed: {len(tenants)}")
        self.stdout.write(f"Successful backups: {len(backup_results)}")
        self.stdout.write(f"Failed backups: {len(tenants) - len(backup_results)}")
        
        if backup_results:
            total_size = sum(result['size_bytes'] for result in backup_results)
            self.stdout.write(f"Total backup size: {self._format_size(total_size)}")

    def _backup_tenant(self, tenant, output_dir, include_files, compress):
        """
        Create a backup for a specific tenant
        
        Args:
            tenant: Tenant instance to backup
            output_dir: Directory to store backup
            include_files: Whether to include tenant files
            compress: Whether to compress the backup
            
        Returns:
            dict: Backup result information
        """
        start_time = timezone.now()
        
        # Create tenant-specific directory
        tenant_backup_dir = os.path.join(output_dir, tenant.schema_name)
        os.makedirs(tenant_backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{tenant.schema_name}_{timestamp}.json"
        if compress:
            backup_filename += '.gz'
        
        backup_path = os.path.join(tenant_backup_dir, backup_filename)
        
        # Collect tenant metadata
        metadata = {
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'subdomain': tenant.subdomain,
            'schema_name': tenant.schema_name,
            'backup_date': timezone.now().isoformat(),
            'backup_type': 'full',
            'django_version': settings.DJANGO_VERSION,
            'database_engine': connection.vendor,
        }
        
        # Get tenant configurations
        configs = list(TenantConfiguration.objects.filter(tenant=tenant).values())
        
        # Extract data from tenant schema
        with tenant_context(tenant):
            tables_data = {}
            
            # Get list of tables in tenant schema
            tables = list_tenant_tables(tenant)
            
            # For each table, extract data
            for table_name in tables:
                with connection.cursor() as cursor:
                    # Get table data
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    column_names = [col[0] for col in cursor.description]
                    
                    # Convert to list of dicts
                    table_data = []
                    for row in rows:
                        row_dict = {}
                        for i, col_name in enumerate(column_names):
                            row_dict[col_name] = row[i]
                        table_data.append(row_dict)
                    
                    tables_data[table_name] = {
                        'columns': column_names,
                        'rows': table_data
                    }
        
        # Combine all data
        backup_data = {
            'metadata': metadata,
            'configurations': configs,
            'tables': tables_data
        }
        
        # Write backup file
        if compress:
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, cls=DjangoJSONEncoder, indent=2)
        else:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, cls=DjangoJSONEncoder, indent=2)
        
        # Include tenant files if requested
        files_backed_up = 0
        if include_files:
            files_backup_dir = os.path.join(tenant_backup_dir, f"files_{timestamp}")
            os.makedirs(files_backup_dir, exist_ok=True)
            
            # Backup tenant-specific files (e.g., media files)
            tenant_media_dir = os.path.join(settings.MEDIA_ROOT, f"tenant_{tenant.id}")
            if os.path.exists(tenant_media_dir):
                import shutil
                
                # Copy tenant media files
                for root, dirs, files in os.walk(tenant_media_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, tenant_media_dir)
                        dst_path = os.path.join(files_backup_dir, rel_path)
                        
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(src_path, dst_path)
                        files_backed_up += 1
        
        # Calculate backup size
        backup_size = os.path.getsize(backup_path)
        
        # Record backup in tenant configuration
        TenantConfiguration.set_config(
            tenant=tenant,
            key='last_backup_date',
            value=timezone.now().isoformat(),
            config_type='string'
        )
        
        TenantConfiguration.set_config(
            tenant=tenant,
            key='last_backup_file',
            value=backup_path,
            config_type='string'
        )
        
        # Create backup record in database
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        # Return backup information
        return {
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'backup_file': backup_path,
            'timestamp': timestamp,
            'duration_seconds': duration,
            'size_bytes': backup_size,
            'tables_count': len(tables_data),
            'records_count': sum(len(table['rows']) for table in tables_data.values()),
            'files_backed_up': files_backed_up,
            'compressed': compress
        }
    
    def _format_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
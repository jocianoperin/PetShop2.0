"""
Management command to validate tenant data integrity.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings

from tenants.models import Tenant
from tenants.utils import tenant_context, _is_postgresql
from tenants.services import tenant_provisioning_service


logger = logging.getLogger('tenants.validation')


class Command(BaseCommand):
    help = 'Validate tenant data integrity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            help='ID or subdomain of the tenant to validate (omit for all tenants)'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            dest='detailed',
            default=False,
            help='Show detailed validation results'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            dest='fix',
            default=False,
            help='Attempt to fix common issues'
        )
        parser.add_argument(
            '--check-relations',
            action='store_true',
            dest='check_relations',
            default=False,
            help='Check referential integrity of relations'
        )

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        detailed = options['detailed']
        fix = options['fix']
        check_relations = options['check_relations']

        # Get tenant(s) to validate
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
            # Validate all active tenants
            tenants = Tenant.objects.filter(is_active=True)
            if not tenants.exists():
                self.stdout.write(self.style.WARNING("No active tenants found"))
                return

        # Validate tenants
        results = []
        for tenant in tenants:
            try:
                result = self._validate_tenant(tenant, check_relations, fix)
                results.append((tenant, result))
                
                # Show result
                if result['valid']:
                    self.stdout.write(
                        self.style.SUCCESS(f"Tenant '{tenant.name}' validation: PASSED")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Tenant '{tenant.name}' validation: FAILED")
                    )
                    
                    # Show errors
                    for error in result['errors']:
                        self.stdout.write(f"  - {error}")
                
                # Show warnings
                if result['warnings']:
                    for warning in result['warnings']:
                        self.stdout.write(self.style.WARNING(f"  - {warning}"))
                
                # Show detailed results if requested
                if detailed:
                    self.stdout.write("\nDetailed validation results:")
                    for check, value in result['checks'].items():
                        status = "✓" if value else "✗"
                        self.stdout.write(f"  {status} {check}: {value}")
                    
                    # Show fixed issues
                    if fix and result.get('fixed_issues'):
                        self.stdout.write("\nFixed issues:")
                        for issue in result['fixed_issues']:
                            self.stdout.write(f"  - {issue}")
                
                self.stdout.write("")
                
            except Exception as e:
                logger.error(f"Error validating tenant {tenant.name}: {str(e)}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f"Failed to validate tenant '{tenant.name}': {str(e)}")
                )

        # Summary
        valid_count = sum(1 for _, result in results if result['valid'])
        self.stdout.write("\nValidation Summary:")
        self.stdout.write(f"Total tenants validated: {len(results)}")
        self.stdout.write(f"Valid tenants: {valid_count}")
        self.stdout.write(f"Invalid tenants: {len(results) - valid_count}")

    def _validate_tenant(self, tenant, check_relations=False, fix=False):
        """
        Validate tenant data integrity
        
        Args:
            tenant: Tenant instance to validate
            check_relations: Whether to check referential integrity
            fix: Whether to attempt to fix common issues
            
        Returns:
            dict: Validation result
        """
        # Start with basic validation from provisioning service
        result = tenant_provisioning_service.validate_tenant_provisioning(tenant)
        
        # Add fixed issues list if fixing is enabled
        if fix:
            result['fixed_issues'] = []
        
        # Additional validations
        with tenant_context(tenant):
            # Check for orphaned records if requested
            if check_relations:
                self._check_referential_integrity(tenant, result, fix)
            
            # Check for duplicate records
            self._check_duplicate_records(tenant, result, fix)
            
            # Check for data consistency
            self._check_data_consistency(tenant, result, fix)
        
        return result

    def _check_referential_integrity(self, tenant, result, fix=False):
        """
        Check referential integrity of tenant data
        
        Args:
            tenant: Tenant instance
            result: Validation result dict to update
            fix: Whether to fix issues
        """
        # Define relationships to check
        relationships = [
            {
                'table': 'api_animal',
                'fk_column': 'cliente_id',
                'ref_table': 'api_cliente',
                'ref_column': 'id'
            },
            {
                'table': 'api_agendamento',
                'fk_column': 'animal_id',
                'ref_table': 'api_animal',
                'ref_column': 'id'
            },
            {
                'table': 'api_agendamento',
                'fk_column': 'servico_id',
                'ref_table': 'api_servico',
                'ref_column': 'id'
            },
            {
                'table': 'api_venda',
                'fk_column': 'cliente_id',
                'ref_table': 'api_cliente',
                'ref_column': 'id'
            }
        ]
        
        orphaned_records = {}
        
        # Check each relationship
        for rel in relationships:
            with connection.cursor() as cursor:
                # Query to find orphaned records
                query = f"""
                    SELECT a.id FROM {rel['table']} a
                    LEFT JOIN {rel['ref_table']} b ON a.{rel['fk_column']} = b.{rel['ref_column']}
                    WHERE a.{rel['fk_column']} IS NOT NULL AND b.{rel['ref_column']} IS NULL
                """
                cursor.execute(query)
                orphans = cursor.fetchall()
                
                if orphans:
                    orphaned_count = len(orphans)
                    orphaned_records[rel['table']] = orphans
                    
                    # Add to validation result
                    result['warnings'].append(
                        f"Found {orphaned_count} orphaned records in {rel['table']} "
                        f"referencing non-existent {rel['ref_table']}"
                    )
                    
                    # Fix if requested
                    if fix:
                        if rel['table'] == 'api_animal':
                            # For animals, we might want to preserve them by setting cliente_id to NULL
                            cursor.execute(
                                f"UPDATE {rel['table']} SET {rel['fk_column']} = NULL "
                                f"WHERE id IN ({','.join(str(o[0]) for o in orphans)})"
                            )
                            result['fixed_issues'].append(
                                f"Set NULL for {rel['fk_column']} in {orphaned_count} orphaned {rel['table']} records"
                            )
                        else:
                            # For other records, we might want to delete them
                            cursor.execute(
                                f"DELETE FROM {rel['table']} "
                                f"WHERE id IN ({','.join(str(o[0]) for o in orphans)})"
                            )
                            result['fixed_issues'].append(
                                f"Deleted {orphaned_count} orphaned records from {rel['table']}"
                            )
        
        # Update validation result
        result['checks']['referential_integrity'] = len(orphaned_records) == 0
        if orphaned_records:
            result['valid'] = False

    def _check_duplicate_records(self, tenant, result, fix=False):
        """
        Check for duplicate records in tenant data
        
        Args:
            tenant: Tenant instance
            result: Validation result dict to update
            fix: Whether to fix issues
        """
        # Define tables and unique columns to check
        unique_constraints = [
            {
                'table': 'api_cliente',
                'columns': ['email'],
                'ignore_null': True
            },
            {
                'table': 'api_servico',
                'columns': ['nome'],
                'ignore_null': False
            },
            {
                'table': 'api_produto',
                'columns': ['nome'],
                'ignore_null': False
            }
        ]
        
        duplicate_records = {}
        
        # Check each constraint
        for constraint in unique_constraints:
            table = constraint['table']
            columns = constraint['columns']
            ignore_null = constraint['ignore_null']
            
            # Build query to find duplicates
            columns_str = ', '.join(columns)
            where_clause = ' AND '.join(f"{col} IS NOT NULL" for col in columns) if ignore_null else '1=1'
            
            with connection.cursor() as cursor:
                query = f"""
                    SELECT {columns_str}, COUNT(*) as count
                    FROM {table}
                    WHERE {where_clause}
                    GROUP BY {columns_str}
                    HAVING COUNT(*) > 1
                """
                cursor.execute(query)
                duplicates = cursor.fetchall()
                
                if duplicates:
                    duplicate_records[table] = duplicates
                    
                    # Add to validation result
                    for dup in duplicates:
                        values = dup[:-1]  # All but the count
                        count = dup[-1]
                        
                        result['warnings'].append(
                            f"Found {count} duplicate records in {table} with {columns_str}='{values}'"
                        )
                        
                        # Fix if requested
                        if fix:
                            # Keep one record, delete the rest
                            # First, get IDs of duplicates
                            where_conditions = ' AND '.join(f"{col} = %s" for col in columns)
                            cursor.execute(
                                f"SELECT id FROM {table} WHERE {where_conditions} ORDER BY id",
                                values
                            )
                            ids = [row[0] for row in cursor.fetchall()]
                            
                            # Keep the first one, delete the rest
                            if len(ids) > 1:
                                to_delete = ids[1:]
                                cursor.execute(
                                    f"DELETE FROM {table} WHERE id IN ({','.join(str(id) for id in to_delete)})"
                                )
                                result['fixed_issues'].append(
                                    f"Deleted {len(to_delete)} duplicate records from {table} "
                                    f"with {columns_str}='{values}'"
                                )
        
        # Update validation result
        result['checks']['no_duplicates'] = len(duplicate_records) == 0

    def _check_data_consistency(self, tenant, result, fix=False):
        """
        Check data consistency in tenant data
        
        Args:
            tenant: Tenant instance
            result: Validation result dict to update
            fix: Whether to fix issues
        """
        consistency_issues = []
        
        # Check for negative values in numeric fields
        numeric_checks = [
            {
                'table': 'api_produto',
                'column': 'preco',
                'min_value': 0
            },
            {
                'table': 'api_produto',
                'column': 'estoque',
                'min_value': 0
            },
            {
                'table': 'api_servico',
                'column': 'preco',
                'min_value': 0
            },
            {
                'table': 'api_venda',
                'column': 'valor_total',
                'min_value': 0
            }
        ]
        
        for check in numeric_checks:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {check['table']} "
                    f"WHERE {check['column']} < %s",
                    [check['min_value']]
                )
                count = cursor.fetchone()[0]
                
                if count > 0:
                    consistency_issues.append(
                        f"Found {count} records in {check['table']} with negative {check['column']}"
                    )
                    
                    # Fix if requested
                    if fix:
                        cursor.execute(
                            f"UPDATE {check['table']} SET {check['column']} = %s "
                            f"WHERE {check['column']} < %s",
                            [check['min_value'], check['min_value']]
                        )
                        result['fixed_issues'].append(
                            f"Set {check['column']} to {check['min_value']} for {count} records in {check['table']}"
                        )
        
        # Check for future dates in created_at fields
        date_checks = [
            {'table': 'api_cliente', 'column': 'created_at'},
            {'table': 'api_animal', 'column': 'created_at'},
            {'table': 'api_servico', 'column': 'created_at'},
            {'table': 'api_produto', 'column': 'created_at'},
            {'table': 'api_venda', 'column': 'created_at'}
        ]
        
        for check in date_checks:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {check['table']} "
                    f"WHERE {check['column']} > NOW()"
                )
                count = cursor.fetchone()[0]
                
                if count > 0:
                    consistency_issues.append(
                        f"Found {count} records in {check['table']} with future {check['column']}"
                    )
                    
                    # Fix if requested
                    if fix:
                        cursor.execute(
                            f"UPDATE {check['table']} SET {check['column']} = NOW() "
                            f"WHERE {check['column']} > NOW()"
                        )
                        result['fixed_issues'].append(
                            f"Set {check['column']} to current time for {count} records in {check['table']}"
                        )
        
        # Add consistency issues to validation result
        for issue in consistency_issues:
            result['warnings'].append(issue)
        
        # Update validation result
        result['checks']['data_consistency'] = len(consistency_issues) == 0
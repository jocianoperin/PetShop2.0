from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from tenants.models import Tenant
from tenants.utils import create_tenant_schema


class Command(BaseCommand):
    """
    Comando para criar schema de banco para um tenant específico.
    
    Usage:
        python manage.py create_tenant_schema --tenant-id <uuid>
        python manage.py create_tenant_schema --subdomain <subdomain>
        python manage.py create_tenant_schema --all
    """
    
    help = 'Cria schema de banco de dados para tenant(s)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='ID do tenant para criar schema'
        )
        parser.add_argument(
            '--subdomain',
            type=str,
            help='Subdomínio do tenant para criar schema'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Cria schemas para todos os tenants ativos'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força criação mesmo se schema já existir'
        )

    def handle(self, *args, **options):
        if options['all']:
            self.create_all_schemas(options['force'])
        elif options['tenant_id']:
            self.create_schema_by_id(options['tenant_id'], options['force'])
        elif options['subdomain']:
            self.create_schema_by_subdomain(options['subdomain'], options['force'])
        else:
            raise CommandError(
                'Especifique --tenant-id, --subdomain ou --all'
            )

    def create_all_schemas(self, force=False):
        """Cria schemas para todos os tenants ativos"""
        tenants = Tenant.objects.filter(is_active=True)
        
        if not tenants.exists():
            self.stdout.write(
                self.style.WARNING('Nenhum tenant ativo encontrado')
            )
            return
        
        created_count = 0
        error_count = 0
        
        for tenant in tenants:
            try:
                if self.create_tenant_schema_safe(tenant, force):
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Schema criado para tenant: {tenant.name} ({tenant.schema_name})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Schema já existe para tenant: {tenant.name} ({tenant.schema_name})'
                        )
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Erro ao criar schema para {tenant.name}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processo concluído: {created_count} criados, {error_count} erros'
            )
        )

    def create_schema_by_id(self, tenant_id, force=False):
        """Cria schema para tenant específico por ID"""
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            self.create_single_schema(tenant, force)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant com ID {tenant_id} não encontrado')

    def create_schema_by_subdomain(self, subdomain, force=False):
        """Cria schema para tenant específico por subdomínio"""
        try:
            tenant = Tenant.objects.get(subdomain=subdomain)
            self.create_single_schema(tenant, force)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant com subdomínio {subdomain} não encontrado')

    def create_single_schema(self, tenant, force=False):
        """Cria schema para um tenant específico"""
        try:
            if self.create_tenant_schema_safe(tenant, force):
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Schema criado com sucesso para: {tenant.name} ({tenant.schema_name})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Schema já existe para: {tenant.name} ({tenant.schema_name})'
                    )
                )
        except Exception as e:
            raise CommandError(f'Erro ao criar schema: {str(e)}')

    def create_tenant_schema_safe(self, tenant, force=False):
        """Cria schema de forma segura, verificando se já existe"""
        with connection.cursor() as cursor:
            # Verifica se schema já existe
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [tenant.schema_name])
            
            exists = cursor.fetchone()
            
            if exists and not force:
                return False  # Schema já existe
            
            if exists and force:
                # Remove schema existente se force=True
                cursor.execute(f"DROP SCHEMA IF EXISTS {tenant.schema_name} CASCADE")
                self.stdout.write(
                    self.style.WARNING(
                        f'Schema existente removido: {tenant.schema_name}'
                    )
                )
            
            # Cria o schema
            cursor.execute(f"CREATE SCHEMA {tenant.schema_name}")
            
            # Define permissões
            cursor.execute(f"GRANT USAGE ON SCHEMA {tenant.schema_name} TO current_user")
            cursor.execute(f"GRANT CREATE ON SCHEMA {tenant.schema_name} TO current_user")
            
            return True
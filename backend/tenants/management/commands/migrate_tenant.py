from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from tenants.models import Tenant
from tenants.utils import tenant_context


class Command(BaseCommand):
    """
    Comando para executar migrações em schemas de tenant específicos.
    
    Usage:
        python manage.py migrate_tenant --tenant-id <uuid>
        python manage.py migrate_tenant --subdomain <subdomain>
        python manage.py migrate_tenant --all
    """
    
    help = 'Executa migrações em schemas de tenant específicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='ID do tenant para executar migrações'
        )
        parser.add_argument(
            '--subdomain',
            type=str,
            help='Subdomínio do tenant para executar migrações'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Executa migrações em todos os tenants ativos'
        )
        parser.add_argument(
            '--app',
            type=str,
            help='App específico para migrar'
        )
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Marca migrações como aplicadas sem executá-las'
        )

    def handle(self, *args, **options):
        if options['all']:
            self.migrate_all_tenants(options)
        elif options['tenant_id']:
            self.migrate_tenant_by_id(options['tenant_id'], options)
        elif options['subdomain']:
            self.migrate_tenant_by_subdomain(options['subdomain'], options)
        else:
            raise CommandError(
                'Especifique --tenant-id, --subdomain ou --all'
            )

    def migrate_all_tenants(self, options):
        """Executa migrações em todos os tenants ativos"""
        tenants = Tenant.objects.filter(is_active=True)
        
        if not tenants.exists():
            self.stdout.write(
                self.style.WARNING('Nenhum tenant ativo encontrado')
            )
            return
        
        success_count = 0
        error_count = 0
        
        for tenant in tenants:
            try:
                self.migrate_tenant(tenant, options)
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Migrações executadas para: {tenant.name} ({tenant.schema_name})'
                    )
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Erro ao migrar {tenant.name}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processo concluído: {success_count} sucessos, {error_count} erros'
            )
        )

    def migrate_tenant_by_id(self, tenant_id, options):
        """Executa migrações para tenant específico por ID"""
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            self.migrate_tenant(tenant, options)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Migrações executadas para: {tenant.name} ({tenant.schema_name})'
                )
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant com ID {tenant_id} não encontrado')

    def migrate_tenant_by_subdomain(self, subdomain, options):
        """Executa migrações para tenant específico por subdomínio"""
        try:
            tenant = Tenant.objects.get(subdomain=subdomain)
            self.migrate_tenant(tenant, options)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Migrações executadas para: {tenant.name} ({tenant.schema_name})'
                )
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant com subdomínio {subdomain} não encontrado')

    def migrate_tenant(self, tenant, options):
        """Executa migrações para um tenant específico"""
        # Configura o schema do tenant
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
        
        # Prepara argumentos para o comando migrate
        migrate_args = []
        migrate_options = {
            'verbosity': options.get('verbosity', 1),
            'interactive': False,
        }
        
        if options.get('app'):
            migrate_args.append(options['app'])
        
        if options.get('fake'):
            migrate_options['fake'] = True
        
        # Executa as migrações no contexto do tenant
        with tenant_context(tenant):
            call_command('migrate', *migrate_args, **migrate_options)

    def get_migration_status(self, tenant):
        """Obtém status das migrações para um tenant"""
        with tenant_context(tenant):
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT app, name, applied 
                    FROM django_migrations 
                    ORDER BY app, name
                """)
                return cursor.fetchall()
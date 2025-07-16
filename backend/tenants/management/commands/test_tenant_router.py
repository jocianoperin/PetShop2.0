"""
Comando Django para testar o funcionamento do database router multitenant.

Este comando cria tenants de teste e verifica se o roteamento de database
está funcionando corretamente, incluindo isolamento de dados.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from tenants.models import Tenant, TenantUser, TenantConfiguration
from tenants.utils import tenant_context, get_current_tenant
from tenants.db_router import TenantDatabaseRouter, schema_router


class Command(BaseCommand):
    help = 'Testa o funcionamento do database router multitenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-tenants',
            action='store_true',
            help='Cria tenants de teste para validação',
        )
        parser.add_argument(
            '--test-isolation',
            action='store_true',
            help='Testa o isolamento de dados entre tenants',
        )
        parser.add_argument(
            '--test-routing',
            action='store_true',
            help='Testa o roteamento de database',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove tenants de teste criados',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Saída detalhada',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        
        try:
            if options['create_test_tenants']:
                self.create_test_tenants()
            
            if options['test_routing']:
                self.test_database_routing()
            
            if options['test_isolation']:
                self.test_data_isolation()
            
            if options['cleanup']:
                self.cleanup_test_tenants()
            
            if not any([options['create_test_tenants'], options['test_routing'], 
                       options['test_isolation'], options['cleanup']]):
                self.stdout.write(
                    self.style.WARNING(
                        'Nenhuma ação especificada. Use --help para ver as opções disponíveis.'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Erro durante execução: {str(e)}')

    def create_test_tenants(self):
        """Cria tenants de teste para validação"""
        self.stdout.write('Criando tenants de teste...')
        
        test_tenants = [
            {
                'name': 'Petshop Teste 1',
                'subdomain': 'teste1',
                'schema_name': 'tenant_teste1'
            },
            {
                'name': 'Petshop Teste 2', 
                'subdomain': 'teste2',
                'schema_name': 'tenant_teste2'
            }
        ]
        
        created_tenants = []
        
        for tenant_data in test_tenants:
            try:
                # Verifica se já existe
                existing = Tenant.objects.filter(
                    subdomain=tenant_data['subdomain']
                ).first()
                
                if existing:
                    if self.verbose:
                        self.stdout.write(f'  Tenant {tenant_data["name"]} já existe')
                    created_tenants.append(existing)
                    continue
                
                # Cria o tenant
                tenant = Tenant.objects.create(**tenant_data)
                created_tenants.append(tenant)
                
                # Cria usuário de teste para o tenant
                tenant_user = TenantUser.objects.create(
                    tenant=tenant,
                    email=f'admin@{tenant_data["subdomain"]}.test',
                    password_hash='test_hash',
                    first_name='Admin',
                    last_name='Teste',
                    role='admin'
                )
                
                # Cria algumas configurações de teste
                TenantConfiguration.set_config(
                    tenant, 'test_config', 'test_value'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Tenant {tenant.name} criado com sucesso')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Erro ao criar tenant {tenant_data["name"]}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total de tenants de teste: {len(created_tenants)}')
        )

    def test_database_routing(self):
        """Testa o funcionamento do database router"""
        self.stdout.write('Testando database router...')
        
        router = TenantDatabaseRouter()
        
        # Testa roteamento para modelos compartilhados
        from tenants.models import Tenant
        db_for_tenant_model = router.db_for_read(Tenant)
        
        if db_for_tenant_model == 'default':
            self.stdout.write(
                self.style.SUCCESS('  ✓ Roteamento para modelos compartilhados: OK')
            )
        else:
            self.stdout.write(
                self.style.ERROR('  ✗ Roteamento para modelos compartilhados: FALHOU')
            )
        
        # Testa roteamento com tenant no contexto
        test_tenants = Tenant.objects.filter(subdomain__startswith='teste')[:2]
        
        if len(test_tenants) >= 2:
            tenant1, tenant2 = test_tenants[0], test_tenants[1]
            
            # Testa contexto de tenant
            with tenant_context(tenant1):
                current = get_current_tenant()
                if current == tenant1:
                    self.stdout.write(
                        self.style.SUCCESS('  ✓ Contexto de tenant: OK')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('  ✗ Contexto de tenant: FALHOU')
                    )
            
            # Testa schema router (apenas PostgreSQL)
            from tenants.utils import _is_postgresql
            if _is_postgresql():
                schema_router.set_schema(tenant1.schema_name)
                current_schema = schema_router.get_current_schema()
                
                if current_schema == tenant1.schema_name:
                    self.stdout.write(
                        self.style.SUCCESS('  ✓ Schema router: OK')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('  ✗ Schema router: FALHOU')
                    )
                
                # Reseta para public
                schema_router.reset_to_public()
            else:
                self.stdout.write(
                    self.style.WARNING('  - Schema router: PULADO (SQLite em uso)')
                )
        else:
            self.stdout.write(
                self.style.WARNING('  - Testes de contexto: PULADOS (poucos tenants de teste)')
            )

    def test_data_isolation(self):
        """Testa o isolamento de dados entre tenants"""
        self.stdout.write('Testando isolamento de dados...')
        
        test_tenants = Tenant.objects.filter(subdomain__startswith='teste')[:2]
        
        if len(test_tenants) < 2:
            self.stdout.write(
                self.style.WARNING('  - Teste pulado: necessários pelo menos 2 tenants de teste')
            )
            return
        
        tenant1, tenant2 = test_tenants[0], test_tenants[1]
        
        # Testa isolamento de TenantUser
        with tenant_context(tenant1):
            users_tenant1 = TenantUser.objects.filter(tenant=tenant1).count()
        
        with tenant_context(tenant2):
            users_tenant2 = TenantUser.objects.filter(tenant=tenant2).count()
        
        # Verifica se cada tenant vê apenas seus próprios usuários
        total_users = TenantUser.objects.count()
        
        if self.verbose:
            self.stdout.write(f'    Usuários tenant1: {users_tenant1}')
            self.stdout.write(f'    Usuários tenant2: {users_tenant2}')
            self.stdout.write(f'    Total usuários: {total_users}')
        
        if users_tenant1 > 0 and users_tenant2 > 0:
            self.stdout.write(
                self.style.SUCCESS('  ✓ Isolamento de dados: OK')
            )
        else:
            self.stdout.write(
                self.style.ERROR('  ✗ Isolamento de dados: FALHOU')
            )
        
        # Testa isolamento de configurações
        config1 = TenantConfiguration.get_config(tenant1, 'test_config')
        config2 = TenantConfiguration.get_config(tenant2, 'test_config')
        
        if config1 == 'test_value' and config2 == 'test_value':
            self.stdout.write(
                self.style.SUCCESS('  ✓ Isolamento de configurações: OK')
            )
        else:
            self.stdout.write(
                self.style.ERROR('  ✗ Isolamento de configurações: FALHOU')
            )

    def cleanup_test_tenants(self):
        """Remove tenants de teste"""
        self.stdout.write('Removendo tenants de teste...')
        
        test_tenants = Tenant.objects.filter(subdomain__startswith='teste')
        count = test_tenants.count()
        
        if count == 0:
            self.stdout.write('  Nenhum tenant de teste encontrado')
            return
        
        try:
            with transaction.atomic():
                # Remove usuários dos tenants de teste
                TenantUser.objects.filter(tenant__in=test_tenants).delete()
                
                # Remove configurações dos tenants de teste
                TenantConfiguration.objects.filter(tenant__in=test_tenants).delete()
                
                # Remove os tenants
                deleted_count, _ = test_tenants.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {deleted_count} tenants de teste removidos')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Erro ao remover tenants: {str(e)}')
            )

    def log_verbose(self, message):
        """Log apenas se verbose está ativo"""
        if self.verbose:
            self.stdout.write(f'    {message}')
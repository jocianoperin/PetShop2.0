"""
Comando para gerenciar fixtures de tenants.
Permite aplicar, validar e listar fixtures disponíveis.
"""

from django.core.management.base import BaseCommand, CommandError
from tenants.fixtures import tenant_fixture_manager
from tenants.models import Tenant
import json


class Command(BaseCommand):
    """
    Comando para gerenciar fixtures de tenants.
    
    Usage:
        python manage.py manage_fixtures --list
        python manage.py manage_fixtures --validate
        python manage.py manage_fixtures --apply --tenant <subdomain> --types services,products
        python manage.py manage_fixtures --apply-all --tenant <subdomain>
    """
    
    help = 'Gerencia fixtures de dados iniciais para tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista fixtures disponíveis'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Valida todos os fixtures carregados'
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica fixtures específicos a um tenant'
        )
        parser.add_argument(
            '--apply-all',
            action='store_true',
            help='Aplica todos os fixtures a um tenant'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Subdomínio ou ID do tenant'
        )
        parser.add_argument(
            '--types',
            type=str,
            help='Tipos de fixtures para aplicar (separados por vírgula)'
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Mostra detalhes dos fixtures'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_fixtures(options.get('show_details', False))
        elif options['validate']:
            self.validate_fixtures()
        elif options['apply'] or options['apply_all']:
            if not options['tenant']:
                raise CommandError('--tenant é obrigatório para aplicar fixtures')
            self.apply_fixtures(options)
        else:
            self.stdout.write(self.style.ERROR('Especifique uma ação: --list, --validate, --apply ou --apply-all'))

    def list_fixtures(self, show_details=False):
        """Lista fixtures disponíveis"""
        self.stdout.write(self.style.HTTP_INFO("Fixtures disponíveis:"))
        
        available_fixtures = tenant_fixture_manager.get_available_fixtures()
        
        for fixture_type, count in available_fixtures.items():
            self.stdout.write(f"  {fixture_type}: {count} itens")
        
        total_items = sum(available_fixtures.values())
        self.stdout.write(f"\nTotal: {total_items} itens em {len(available_fixtures)} tipos")
        
        if show_details:
            self.stdout.write(self.style.HTTP_INFO("\nDetalhes dos fixtures:"))
            self._show_fixture_details()

    def _show_fixture_details(self):
        """Mostra detalhes dos fixtures"""
        # Acessar fixtures internos (para demonstração)
        fixtures = tenant_fixture_manager._fixtures
        
        for fixture_type, items in fixtures.items():
            self.stdout.write(f"\n{fixture_type.upper()}:")
            
            if fixture_type == 'services':
                for i, service in enumerate(items[:3]):  # Mostrar apenas os primeiros 3
                    self.stdout.write(f"  {i+1}. {service['nome']} - R$ {service['preco']}")
                if len(items) > 3:
                    self.stdout.write(f"  ... e mais {len(items) - 3} serviços")
            
            elif fixture_type == 'products':
                for i, product in enumerate(items[:3]):  # Mostrar apenas os primeiros 3
                    self.stdout.write(f"  {i+1}. {product['nome']} - R$ {product['preco']} ({product['categoria']})")
                if len(items) > 3:
                    self.stdout.write(f"  ... e mais {len(items) - 3} produtos")
            
            elif fixture_type == 'configurations':
                for i, config in enumerate(items[:5]):  # Mostrar apenas os primeiros 5
                    self.stdout.write(f"  {i+1}. {config['key']}: {config['value']} ({config['type']})")
                if len(items) > 5:
                    self.stdout.write(f"  ... e mais {len(items) - 5} configurações")

    def validate_fixtures(self):
        """Valida todos os fixtures"""
        self.stdout.write(self.style.HTTP_INFO("Validando fixtures..."))
        
        errors = tenant_fixture_manager.validate_fixtures()
        
        if not errors:
            self.stdout.write(self.style.SUCCESS("✓ Todos os fixtures são válidos"))
        else:
            self.stdout.write(self.style.ERROR("✗ Erros encontrados nos fixtures:"))
            
            for fixture_type, type_errors in errors.items():
                self.stdout.write(f"\n{fixture_type}:")
                for error in type_errors:
                    self.stdout.write(f"  - {error}")
            
            raise CommandError("Fixtures contêm erros")

    def apply_fixtures(self, options):
        """Aplica fixtures a um tenant"""
        tenant_identifier = options['tenant']
        
        # Buscar tenant
        try:
            if len(tenant_identifier) == 36:  # UUID
                tenant = Tenant.objects.get(id=tenant_identifier)
            else:  # Subdomain
                tenant = Tenant.objects.get(subdomain=tenant_identifier)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant não encontrado: {tenant_identifier}')
        
        # Determinar tipos de fixtures
        if options['apply_all']:
            fixture_types = None  # Aplicar todos
            self.stdout.write(f"Aplicando todos os fixtures ao tenant: {tenant.name}")
        else:
            if not options['types']:
                raise CommandError('--types é obrigatório quando usar --apply')
            fixture_types = [t.strip() for t in options['types'].split(',')]
            self.stdout.write(f"Aplicando fixtures {fixture_types} ao tenant: {tenant.name}")
        
        # Aplicar fixtures
        try:
            results = tenant_fixture_manager.apply_fixtures(tenant, fixture_types)
            
            self.stdout.write(self.style.SUCCESS("✓ Fixtures aplicados com sucesso:"))
            
            total_applied = 0
            for fixture_type, count in results.items():
                self.stdout.write(f"  {fixture_type}: {count} itens")
                total_applied += count
            
            self.stdout.write(f"\nTotal aplicado: {total_applied} itens")
            
            # Verificar se dados foram realmente criados
            self._verify_applied_fixtures(tenant, results)
            
        except Exception as e:
            raise CommandError(f'Erro ao aplicar fixtures: {str(e)}')

    def _verify_applied_fixtures(self, tenant, results):
        """Verifica se os fixtures foram aplicados corretamente"""
        from tenants.utils import tenant_context
        from tenants.models import TenantConfiguration
        
        self.stdout.write(self.style.HTTP_INFO("\nVerificando aplicação dos fixtures..."))
        
        # Verificar serviços e produtos
        if 'services' in results or 'products' in results:
            with tenant_context(tenant):
                from api.models import Servico, Produto
                
                if 'services' in results:
                    service_count = Servico.objects.count()
                    expected_services = results['services']
                    if service_count >= expected_services:
                        self.stdout.write(f"✓ Serviços: {service_count} encontrados (esperado: {expected_services})")
                    else:
                        self.stdout.write(f"⚠ Serviços: {service_count} encontrados (esperado: {expected_services})")
                
                if 'products' in results:
                    product_count = Produto.objects.count()
                    expected_products = results['products']
                    if product_count >= expected_products:
                        self.stdout.write(f"✓ Produtos: {product_count} encontrados (esperado: {expected_products})")
                    else:
                        self.stdout.write(f"⚠ Produtos: {product_count} encontrados (esperado: {expected_products})")
        
        # Verificar configurações
        if 'configurations' in results:
            config_count = TenantConfiguration.objects.filter(tenant=tenant).count()
            expected_configs = results['configurations']
            if config_count >= expected_configs:
                self.stdout.write(f"✓ Configurações: {config_count} encontradas (esperado: {expected_configs})")
            else:
                self.stdout.write(f"⚠ Configurações: {config_count} encontradas (esperado: {expected_configs})")
        
        self.stdout.write(self.style.SUCCESS("Verificação concluída"))
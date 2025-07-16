"""
Testes para o sistema de fixtures de tenants.
"""

from django.test import TestCase, TransactionTestCase
from django.db import transaction

from .models import Tenant, TenantConfiguration
from .fixtures import TenantFixtureManager, tenant_fixture_manager
from .utils import tenant_context


class TenantFixtureManagerTest(TransactionTestCase):
    """
    Testes para o TenantFixtureManager.
    Usa TransactionTestCase para testar transações.
    """
    
    def setUp(self):
        self.fixture_manager = TenantFixtureManager()
        self.tenant = Tenant.objects.create(
            name='Pet Shop Teste Fixtures',
            subdomain='pettestefixtures',
            schema_name='tenant_pettestefixtures'
        )
    
    def test_fixture_manager_initialization(self):
        """Testa inicialização do gerenciador de fixtures"""
        available_fixtures = self.fixture_manager.get_available_fixtures()
        
        # Verificar se fixtures padrão foram carregados
        self.assertIn('services', available_fixtures)
        self.assertIn('products', available_fixtures)
        self.assertIn('configurations', available_fixtures)
        
        # Verificar se há itens em cada tipo
        self.assertGreater(available_fixtures['services'], 0)
        self.assertGreater(available_fixtures['products'], 0)
        self.assertGreater(available_fixtures['configurations'], 0)
    
    def test_apply_service_fixtures(self):
        """Testa aplicação de fixtures de serviços"""
        results = self.fixture_manager.apply_fixtures(
            self.tenant, 
            fixture_types=['services']
        )
        
        self.assertIn('services', results)
        self.assertGreater(results['services'], 0)
        
        # Verificar se serviços foram criados no contexto do tenant
        with tenant_context(self.tenant):
            from api.models import Servico
            
            services = Servico.objects.all()
            self.assertGreater(services.count(), 0)
            
            # Verificar se serviços específicos existem
            banho_tosa = services.filter(nome__icontains='Banho').first()
            self.assertIsNotNone(banho_tosa)
            self.assertGreater(banho_tosa.preco, 0)
    
    def test_apply_product_fixtures(self):
        """Testa aplicação de fixtures de produtos"""
        results = self.fixture_manager.apply_fixtures(
            self.tenant, 
            fixture_types=['products']
        )
        
        self.assertIn('products', results)
        self.assertGreater(results['products'], 0)
        
        # Verificar se produtos foram criados no contexto do tenant
        with tenant_context(self.tenant):
            from api.models import Produto
            
            products = Produto.objects.all()
            self.assertGreater(products.count(), 0)
            
            # Verificar se produtos específicos existem
            racao = products.filter(categoria='racao').first()
            self.assertIsNotNone(racao)
            self.assertGreater(racao.preco, 0)
            
            shampoo = products.filter(categoria='higiene').first()
            self.assertIsNotNone(shampoo)
    
    def test_apply_configuration_fixtures(self):
        """Testa aplicação de fixtures de configurações"""
        results = self.fixture_manager.apply_fixtures(
            self.tenant, 
            fixture_types=['configurations']
        )
        
        self.assertIn('configurations', results)
        self.assertGreater(results['configurations'], 0)
        
        # Verificar se configurações foram criadas
        configs = TenantConfiguration.objects.filter(tenant=self.tenant)
        self.assertGreater(configs.count(), 0)
        
        # Verificar configurações específicas
        business_hours = TenantConfiguration.get_config(self.tenant, 'business_hours_start')
        self.assertIsNotNone(business_hours)
        
        currency = TenantConfiguration.get_config(self.tenant, 'currency')
        self.assertEqual(currency, 'BRL')
    
    def test_apply_all_fixtures(self):
        """Testa aplicação de todos os fixtures"""
        results = self.fixture_manager.apply_fixtures(self.tenant)
        
        # Verificar se todos os tipos foram aplicados
        expected_types = ['services', 'products', 'configurations', 'categories']
        for fixture_type in expected_types:
            self.assertIn(fixture_type, results)
        
        # Verificar se dados foram criados
        with tenant_context(self.tenant):
            from api.models import Servico, Produto
            
            self.assertGreater(Servico.objects.count(), 0)
            self.assertGreater(Produto.objects.count(), 0)
        
        self.assertGreater(
            TenantConfiguration.objects.filter(tenant=self.tenant).count(), 
            0
        )
    
    def test_fixture_isolation_between_tenants(self):
        """Testa isolamento de fixtures entre tenants"""
        # Criar segundo tenant
        tenant2 = Tenant.objects.create(
            name='Pet Shop Teste 2',
            subdomain='petteste2',
            schema_name='tenant_petteste2'
        )
        
        # Aplicar fixtures em ambos os tenants
        self.fixture_manager.apply_fixtures(self.tenant, ['services'])
        self.fixture_manager.apply_fixtures(tenant2, ['services'])
        
        # Verificar isolamento
        with tenant_context(self.tenant):
            from api.models import Servico
            services_tenant1 = Servico.objects.all()
        
        with tenant_context(tenant2):
            from api.models import Servico
            services_tenant2 = Servico.objects.all()
        
        # Ambos devem ter serviços, mas isolados
        self.assertGreater(services_tenant1.count(), 0)
        self.assertGreater(services_tenant2.count(), 0)
        
        # Verificar que não há vazamento entre tenants
        with tenant_context(self.tenant):
            from api.models import Servico
            # Adicionar serviço específico no tenant 1
            Servico.objects.create(
                nome='Serviço Específico Tenant 1',
                descricao='Teste',
                preco=100.00,
                duracao_estimada='01:00:00'
            )
        
        with tenant_context(tenant2):
            from api.models import Servico
            # Verificar que o serviço específico não aparece no tenant 2
            specific_service = Servico.objects.filter(nome='Serviço Específico Tenant 1')
            self.assertEqual(specific_service.count(), 0)
    
    def test_duplicate_fixture_application(self):
        """Testa que fixtures não são duplicados quando aplicados novamente"""
        # Aplicar fixtures pela primeira vez
        results1 = self.fixture_manager.apply_fixtures(
            self.tenant, 
            fixture_types=['services']
        )
        
        # Aplicar fixtures novamente
        results2 = self.fixture_manager.apply_fixtures(
            self.tenant, 
            fixture_types=['services']
        )
        
        # Segunda aplicação não deve criar novos itens
        self.assertEqual(results2['services'], 0)
        
        # Verificar que não há duplicatas
        with tenant_context(self.tenant):
            from api.models import Servico
            
            # Contar serviços com nomes específicos
            banho_count = Servico.objects.filter(nome__icontains='Banho').count()
            self.assertLessEqual(banho_count, 2)  # Pode haver "Banho e Tosa" e "Banho Simples"
    
    def test_custom_fixtures(self):
        """Testa adição de fixtures customizados"""
        custom_services = [
            {
                'nome': 'Serviço Customizado',
                'descricao': 'Serviço adicionado via teste',
                'preco': 99.99,
                'duracao_estimada': '01:00:00',
                'ativo': True
            }
        ]
        
        # Adicionar fixture customizado
        self.fixture_manager.add_custom_fixture('services', custom_services)
        
        # Aplicar fixtures (incluindo o customizado)
        results = self.fixture_manager.apply_fixtures(
            self.tenant, 
            fixture_types=['services']
        )
        
        # Verificar se o serviço customizado foi criado
        with tenant_context(self.tenant):
            from api.models import Servico
            
            custom_service = Servico.objects.filter(nome='Serviço Customizado').first()
            self.assertIsNotNone(custom_service)
            self.assertEqual(custom_service.preco, 99.99)
    
    def test_fixture_validation(self):
        """Testa validação de fixtures"""
        errors = self.fixture_manager.validate_fixtures()
        
        # Fixtures padrão devem ser válidos
        self.assertEqual(len(errors), 0)
        
        # Testar com fixtures inválidos
        invalid_services = [
            {
                'nome': 'Serviço Inválido',
                # Faltam campos obrigatórios
            }
        ]
        
        test_manager = TenantFixtureManager()
        test_manager.add_custom_fixture('services', invalid_services)
        
        errors = test_manager.validate_fixtures()
        self.assertIn('services', errors)
        self.assertGreater(len(errors['services']), 0)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        # Limpar configurações
        TenantConfiguration.objects.filter(tenant=self.tenant).delete()
        
        # Limpar tenant
        self.tenant.delete()


class TenantFixtureIntegrationTest(TestCase):
    """
    Testes de integração para o sistema de fixtures.
    """
    
    def test_global_fixture_manager(self):
        """Testa o gerenciador global de fixtures"""
        # Verificar se a instância global está disponível
        self.assertIsInstance(tenant_fixture_manager, TenantFixtureManager)
        
        # Verificar se fixtures estão carregados
        available = tenant_fixture_manager.get_available_fixtures()
        self.assertGreater(len(available), 0)
    
    def test_fixture_types_consistency(self):
        """Testa consistência dos tipos de fixtures"""
        fixtures = tenant_fixture_manager._fixtures
        
        # Verificar estrutura dos serviços
        if 'services' in fixtures:
            for service in fixtures['services']:
                self.assertIn('nome', service)
                self.assertIn('descricao', service)
                self.assertIn('preco', service)
                self.assertIn('duracao_estimada', service)
        
        # Verificar estrutura dos produtos
        if 'products' in fixtures:
            for product in fixtures['products']:
                self.assertIn('nome', product)
                self.assertIn('descricao', product)
                self.assertIn('categoria', product)
                self.assertIn('preco', product)
        
        # Verificar estrutura das configurações
        if 'configurations' in fixtures:
            for config in fixtures['configurations']:
                self.assertIn('key', config)
                self.assertIn('value', config)
                self.assertIn('type', config)
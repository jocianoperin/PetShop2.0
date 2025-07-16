"""
Testes para o TenantProvisioningService.
Verifica criação completa de tenants, validações e rollback.
"""

import uuid
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock

from .models import Tenant, TenantUser, TenantConfiguration
from .services import TenantProvisioningService, TenantProvisioningError
from .utils import tenant_context


class TenantProvisioningServiceTest(TransactionTestCase):
    """
    Testes para o TenantProvisioningService.
    Usa TransactionTestCase para testar transações e rollback.
    """
    
    def setUp(self):
        self.service = TenantProvisioningService()
        self.valid_tenant_data = {
            'name': 'Pet Shop Teste',
            'subdomain': 'petteste',
            'admin_email': 'admin@petteste.com',
            'admin_password': 'senha123456',
            'admin_first_name': 'João',
            'admin_last_name': 'Silva',
            'plan_type': 'basic',
            'max_users': 15,
            'max_animals': 500
        }
    
    def test_create_tenant_success(self):
        """Testa criação bem-sucedida de tenant"""
        tenant = self.service.create_tenant(self.valid_tenant_data)
        
        # Verificar se tenant foi criado
        self.assertIsInstance(tenant, Tenant)
        self.assertEqual(tenant.name, 'Pet Shop Teste')
        self.assertEqual(tenant.subdomain, 'petteste')
        self.assertEqual(tenant.plan_type, 'basic')
        self.assertEqual(tenant.max_users, 15)
        self.assertEqual(tenant.max_animals, 500)
        self.assertTrue(tenant.is_active)
        
        # Verificar se usuário admin foi criado
        admin_users = TenantUser.objects.filter(tenant=tenant, role='admin')
        self.assertEqual(admin_users.count(), 1)
        
        admin_user = admin_users.first()
        self.assertEqual(admin_user.email, 'admin@petteste.com')
        self.assertEqual(admin_user.first_name, 'João')
        self.assertEqual(admin_user.last_name, 'Silva')
        self.assertTrue(admin_user.is_active)
        
        # Verificar se configurações foram criadas
        configs = TenantConfiguration.objects.filter(tenant=tenant)
        self.assertGreater(configs.count(), 0)
        
        # Verificar configurações específicas
        business_hours = TenantConfiguration.get_config(tenant, 'business_hours_start')
        self.assertEqual(business_hours, '08:00')
        
        currency = TenantConfiguration.get_config(tenant, 'currency')
        self.assertEqual(currency, 'BRL')
        
        # Verificar dados iniciais no contexto do tenant
        with tenant_context(tenant):
            from api.models import Servico, Produto
            
            services = Servico.objects.all()
            products = Produto.objects.all()
            
            self.assertGreater(services.count(), 0)
            self.assertGreater(products.count(), 0)
            
            # Verificar se há serviços de banho/tosa (pode ter nomes diferentes com fixtures)
            banho_services = services.filter(nome__icontains='Banho')
            self.assertGreater(banho_services.count(), 0)
            
            # Verificar se há produtos de ração
            racao_products = products.filter(categoria='racao')
            self.assertGreater(racao_products.count(), 0)
    
    def test_create_tenant_minimal_data(self):
        """Testa criação de tenant com dados mínimos"""
        minimal_data = {
            'name': 'Pet Shop Mínimo',
            'subdomain': 'petminimo',
            'admin_email': 'admin@petminimo.com',
            'admin_password': 'senha123456'
        }
        
        tenant = self.service.create_tenant(minimal_data)
        
        # Verificar valores padrão
        self.assertEqual(tenant.plan_type, 'basic')
        self.assertEqual(tenant.max_users, 10)
        self.assertEqual(tenant.max_animals, 1000)
        
        # Verificar usuário admin com campos opcionais vazios
        admin_user = TenantUser.objects.get(tenant=tenant, role='admin')
        self.assertEqual(admin_user.first_name, '')
        self.assertEqual(admin_user.last_name, '')
    
    def test_validate_tenant_data_missing_required_fields(self):
        """Testa validação com campos obrigatórios ausentes"""
        incomplete_data = {
            'name': 'Pet Shop Incompleto',
            'subdomain': 'petincompleto'
            # Faltam admin_email e admin_password
        }
        
        with self.assertRaises(TenantProvisioningError) as context:
            self.service.create_tenant(incomplete_data)
        
        self.assertIn('Campo obrigatório ausente', str(context.exception))
    
    def test_validate_tenant_data_invalid_subdomain(self):
        """Testa validação com subdomínio inválido"""
        invalid_data = self.valid_tenant_data.copy()
        invalid_data['subdomain'] = 'pet@shop!'  # Caracteres inválidos
        
        with self.assertRaises(TenantProvisioningError) as context:
            self.service.create_tenant(invalid_data)
        
        self.assertIn('Subdomínio deve conter apenas', str(context.exception))
    
    def test_validate_tenant_data_duplicate_subdomain(self):
        """Testa validação com subdomínio duplicado"""
        # Criar primeiro tenant
        self.service.create_tenant(self.valid_tenant_data)
        
        # Tentar criar segundo tenant com mesmo subdomínio
        duplicate_data = self.valid_tenant_data.copy()
        duplicate_data['name'] = 'Pet Shop Duplicado'
        duplicate_data['admin_email'] = 'admin2@petteste.com'
        
        with self.assertRaises(TenantProvisioningError) as context:
            self.service.create_tenant(duplicate_data)
        
        self.assertIn('já está em uso', str(context.exception))
    
    def test_validate_tenant_data_duplicate_email(self):
        """Testa validação com email duplicado"""
        # Criar primeiro tenant
        self.service.create_tenant(self.valid_tenant_data)
        
        # Tentar criar segundo tenant com mesmo email
        duplicate_data = self.valid_tenant_data.copy()
        duplicate_data['name'] = 'Pet Shop Duplicado'
        duplicate_data['subdomain'] = 'petduplicado'
        # admin_email permanece o mesmo
        
        with self.assertRaises(TenantProvisioningError) as context:
            self.service.create_tenant(duplicate_data)
        
        self.assertIn('já está em uso', str(context.exception))
    
    def test_validate_tenant_data_weak_password(self):
        """Testa validação com senha fraca"""
        weak_password_data = self.valid_tenant_data.copy()
        weak_password_data['admin_password'] = '123'  # Muito curta
        
        with self.assertRaises(TenantProvisioningError) as context:
            self.service.create_tenant(weak_password_data)
        
        self.assertIn('pelo menos 8 caracteres', str(context.exception))
    
    def test_schema_name_uniqueness(self):
        """Testa geração de nomes de schema únicos"""
        # Criar tenant com subdomínio que pode gerar conflito
        data1 = self.valid_tenant_data.copy()
        data1['subdomain'] = 'pet-shop'
        data1['admin_email'] = 'admin1@petshop.com'
        
        data2 = self.valid_tenant_data.copy()
        data2['name'] = 'Pet Shop 2'
        data2['subdomain'] = 'pet_shop'  # Pode gerar mesmo schema_name
        data2['admin_email'] = 'admin2@petshop.com'
        
        tenant1 = self.service.create_tenant(data1)
        tenant2 = self.service.create_tenant(data2)
        
        # Verificar que schema_names são diferentes
        self.assertNotEqual(tenant1.schema_name, tenant2.schema_name)
    
    @patch('tenants.services.connection')
    def test_rollback_on_schema_creation_failure(self, mock_connection):
        """Testa rollback quando criação de schema falha"""
        # Simular falha na criação do schema
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Falha no banco de dados")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        with self.assertRaises(TenantProvisioningError):
            self.service.create_tenant(self.valid_tenant_data)
        
        # Verificar que tenant não foi criado (rollback funcionou)
        self.assertFalse(
            Tenant.objects.filter(subdomain='petteste').exists()
        )
        self.assertFalse(
            TenantUser.objects.filter(email='admin@petteste.com').exists()
        )
    
    @patch('tenants.services.call_command')
    def test_rollback_on_migration_failure(self, mock_call_command):
        """Testa rollback quando migrações falham"""
        # Simular falha nas migrações
        mock_call_command.side_effect = Exception("Falha nas migrações")
        
        with self.assertRaises(TenantProvisioningError):
            self.service.create_tenant(self.valid_tenant_data)
        
        # Verificar que tenant não foi criado (rollback funcionou)
        self.assertFalse(
            Tenant.objects.filter(subdomain='petteste').exists()
        )
    
    def test_validate_tenant_provisioning_success(self):
        """Testa validação de tenant provisionado corretamente"""
        tenant = self.service.create_tenant(self.valid_tenant_data)
        
        validation_result = self.service.validate_tenant_provisioning(tenant)
        
        self.assertTrue(validation_result['valid'])
        self.assertEqual(len(validation_result['errors']), 0)
        
        # Verificar checks específicos
        checks = validation_result['checks']
        self.assertTrue(checks['tenant_active'])
        self.assertTrue(checks['has_admin_user'])
        self.assertTrue(checks['tables_accessible'])
        self.assertTrue(checks['has_configurations'])
        self.assertGreater(checks['configuration_count'], 0)
        self.assertGreater(checks['initial_services'], 0)
        self.assertGreater(checks['initial_products'], 0)
    
    def test_validate_tenant_provisioning_inactive_tenant(self):
        """Testa validação de tenant inativo"""
        tenant = self.service.create_tenant(self.valid_tenant_data)
        tenant.is_active = False
        tenant.save()
        
        validation_result = self.service.validate_tenant_provisioning(tenant)
        
        self.assertFalse(validation_result['valid'])
        self.assertIn('não está ativo', str(validation_result['errors']))
    
    def test_validate_tenant_provisioning_no_admin(self):
        """Testa validação de tenant sem usuário admin"""
        tenant = self.service.create_tenant(self.valid_tenant_data)
        
        # Remover usuário admin
        TenantUser.objects.filter(tenant=tenant, role='admin').delete()
        
        validation_result = self.service.validate_tenant_provisioning(tenant)
        
        self.assertFalse(validation_result['valid'])
        self.assertIn('administrador ativo', str(validation_result['errors']))
    
    def test_get_provisioning_status_success(self):
        """Testa obtenção de status de provisionamento"""
        tenant = self.service.create_tenant(self.valid_tenant_data)
        
        # Testar com ID
        status_by_id = self.service.get_provisioning_status(str(tenant.id))
        self.assertEqual(status_by_id['provisioning_status'], 'complete')
        self.assertEqual(status_by_id['tenant']['name'], 'Pet Shop Teste')
        
        # Testar com subdomínio
        status_by_subdomain = self.service.get_provisioning_status('petteste')
        self.assertEqual(status_by_subdomain['provisioning_status'], 'complete')
        self.assertEqual(status_by_subdomain['tenant']['subdomain'], 'petteste')
    
    def test_get_provisioning_status_not_found(self):
        """Testa obtenção de status para tenant inexistente"""
        status = self.service.get_provisioning_status('inexistente')
        
        self.assertIn('error', status)
        self.assertIn('não encontrado', status['error'])
    
    def test_tenant_context_isolation(self):
        """Testa isolamento de dados entre tenants"""
        # Criar dois tenants
        tenant1_data = self.valid_tenant_data.copy()
        tenant1 = self.service.create_tenant(tenant1_data)
        
        tenant2_data = self.valid_tenant_data.copy()
        tenant2_data['name'] = 'Pet Shop 2'
        tenant2_data['subdomain'] = 'petteste2'
        tenant2_data['admin_email'] = 'admin@petteste2.com'
        tenant2 = self.service.create_tenant(tenant2_data)
        
        # Adicionar dados específicos em cada tenant
        with tenant_context(tenant1):
            from api.models import Cliente
            cliente1 = Cliente.objects.create(
                nome='Cliente Tenant 1',
                email='cliente1@test.com',
                telefone='11999999999',
                endereco='Endereço 1'
            )
        
        with tenant_context(tenant2):
            from api.models import Cliente
            cliente2 = Cliente.objects.create(
                nome='Cliente Tenant 2',
                email='cliente2@test.com',
                telefone='11888888888',
                endereco='Endereço 2'
            )
        
        # Verificar isolamento
        with tenant_context(tenant1):
            from api.models import Cliente
            clientes_tenant1 = Cliente.objects.all()
            self.assertEqual(clientes_tenant1.count(), 1)
            self.assertEqual(clientes_tenant1.first().nome, 'Cliente Tenant 1')
        
        with tenant_context(tenant2):
            from api.models import Cliente
            clientes_tenant2 = Cliente.objects.all()
            self.assertEqual(clientes_tenant2.count(), 1)
            self.assertEqual(clientes_tenant2.first().nome, 'Cliente Tenant 2')
    
    def test_configuration_system(self):
        """Testa sistema de configurações por tenant"""
        tenant = self.service.create_tenant(self.valid_tenant_data)
        
        # Verificar configurações padrão
        business_hours = TenantConfiguration.get_config(tenant, 'business_hours_start')
        self.assertEqual(business_hours, '08:00')
        
        # Modificar configuração
        TenantConfiguration.set_config(tenant, 'business_hours_start', '09:00')
        
        # Verificar modificação
        updated_hours = TenantConfiguration.get_config(tenant, 'business_hours_start')
        self.assertEqual(updated_hours, '09:00')
        
        # Testar configuração inexistente
        inexistent = TenantConfiguration.get_config(tenant, 'config_inexistente', 'padrão')
        self.assertEqual(inexistent, 'padrão')
    
    def tearDown(self):
        """Limpeza após cada teste"""
        # Limpar todos os tenants criados nos testes
        for tenant in Tenant.objects.all():
            try:
                # Tentar remover schema se for PostgreSQL
                from tenants.utils import drop_tenant_schema
                drop_tenant_schema(tenant)
            except:
                pass  # Ignorar erros de limpeza
        
        # Limpar registros do banco
        TenantConfiguration.objects.all().delete()
        TenantUser.objects.all().delete()
        Tenant.objects.all().delete()


class TenantProvisioningServiceUnitTest(TestCase):
    """
    Testes unitários para métodos específicos do TenantProvisioningService.
    Usa TestCase regular para testes que não precisam de transações.
    """
    
    def setUp(self):
        self.service = TenantProvisioningService()
    
    def test_validate_tenant_data_valid(self):
        """Testa validação com dados válidos"""
        valid_data = {
            'name': 'Pet Shop Válido',
            'subdomain': 'petvalido',
            'admin_email': 'admin@petvalido.com',
            'admin_password': 'senha123456'
        }
        
        # Não deve lançar exceção
        try:
            self.service._validate_tenant_data(valid_data)
        except TenantProvisioningError:
            self.fail("_validate_tenant_data() lançou exceção com dados válidos")
    
    def test_validate_tenant_data_invalid_subdomain_formats(self):
        """Testa validação com diferentes formatos inválidos de subdomínio"""
        base_data = {
            'name': 'Pet Shop',
            'admin_email': 'admin@test.com',
            'admin_password': 'senha123456'
        }
        
        invalid_subdomains = [
            'pet shop',  # Espaço
            'pet@shop',  # Caractere especial
            'pet.shop',  # Ponto
            'Pet-Shop',  # Maiúscula
            '123pet',    # Começando com número (pode ser válido, mas testando)
            '',          # Vazio
        ]
        
        for subdomain in invalid_subdomains:
            with self.subTest(subdomain=subdomain):
                data = base_data.copy()
                data['subdomain'] = subdomain
                
                with self.assertRaises(TenantProvisioningError):
                    self.service._validate_tenant_data(data)
    
    def test_schema_name_generation(self):
        """Testa geração de nomes de schema"""
        test_cases = [
            ('petshop', 'tenant_petshop'),
            ('pet-shop', 'tenant_pet_shop'),
            ('pet_shop', 'tenant_pet_shop'),
            ('pet123', 'tenant_pet123'),
        ]
        
        for subdomain, expected_base in test_cases:
            with self.subTest(subdomain=subdomain):
                tenant_data = {
                    'name': f'Pet Shop {subdomain}',
                    'subdomain': subdomain,
                    'admin_email': f'admin@{subdomain}.com',
                    'admin_password': 'senha123456'
                }
                
                tenant = self.service._create_tenant_record(tenant_data)
                self.assertTrue(tenant.schema_name.startswith(expected_base))
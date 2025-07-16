"""
Testes básicos para o sistema de contexto de tenant.
Este arquivo pode ser executado para verificar se o sistema está funcionando.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from .models import Tenant, TenantUser
from .utils import (
    get_current_tenant, set_current_tenant, tenant_context,
    tenant_required, tenant_admin_required, with_tenant_context,
    push_tenant_context, pop_tenant_context, clear_tenant_context,
    multi_tenant_context, get_tenant_from_request, ensure_tenant_context
)


class TenantContextTestCase(TestCase):
    """Testes para o sistema de contexto de tenant"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Criar tenants de teste
        self.tenant1 = Tenant.objects.create(
            name="Petshop Teste 1",
            subdomain="teste1",
            schema_name="tenant_teste1"
        )
        
        self.tenant2 = Tenant.objects.create(
            name="Petshop Teste 2", 
            subdomain="teste2",
            schema_name="tenant_teste2"
        )
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Criar TenantUser
        self.tenant_user = TenantUser.objects.create(
            tenant=self.tenant1,
            email='test@example.com',
            password_hash='hashed_password',
            first_name='Test',
            last_name='User',
            role='admin'
        )
        
        self.factory = RequestFactory()
    
    def test_basic_tenant_context(self):
        """Testa o contexto básico de tenant"""
        # Inicialmente não deve haver tenant
        self.assertIsNone(get_current_tenant())
        
        # Define um tenant
        set_current_tenant(self.tenant1)
        self.assertEqual(get_current_tenant(), self.tenant1)
        
        # Limpa o contexto
        set_current_tenant(None)
        self.assertIsNone(get_current_tenant())
    
    def test_tenant_context_manager(self):
        """Testa o context manager de tenant"""
        # Inicialmente não há tenant
        self.assertIsNone(get_current_tenant())
        
        # Usa o context manager
        with tenant_context(self.tenant1):
            self.assertEqual(get_current_tenant(), self.tenant1)
            
            # Contexto aninhado
            with tenant_context(self.tenant2):
                self.assertEqual(get_current_tenant(), self.tenant2)
            
            # Volta para o tenant anterior
            self.assertEqual(get_current_tenant(), self.tenant1)
        
        # Contexto limpo após sair
        self.assertIsNone(get_current_tenant())
    
    def test_tenant_stack_operations(self):
        """Testa as operações de stack de tenant"""
        # Inicialmente não há tenant
        self.assertIsNone(get_current_tenant())
        
        # Push tenant1
        push_tenant_context(self.tenant1)
        self.assertEqual(get_current_tenant(), self.tenant1)
        
        # Push tenant2
        push_tenant_context(self.tenant2)
        self.assertEqual(get_current_tenant(), self.tenant2)
        
        # Pop volta para tenant1
        pop_tenant_context()
        self.assertEqual(get_current_tenant(), self.tenant1)
        
        # Pop volta para None
        pop_tenant_context()
        self.assertIsNone(get_current_tenant())
        
        # Clear context
        push_tenant_context(self.tenant1)
        clear_tenant_context()
        self.assertIsNone(get_current_tenant())
    
    def test_multi_tenant_context(self):
        """Testa o context manager para múltiplos tenants"""
        tenants_visited = []
        
        with multi_tenant_context(self.tenant1, self.tenant2) as tenant_iterator:
            for tenant in tenant_iterator:
                tenants_visited.append(tenant)
                # Verifica se o tenant atual está correto
                self.assertEqual(get_current_tenant(), tenant)
        
        # Verifica se todos os tenants foram visitados
        self.assertEqual(len(tenants_visited), 2)
        self.assertIn(self.tenant1, tenants_visited)
        self.assertIn(self.tenant2, tenants_visited)
        
        # Contexto deve estar limpo
        self.assertIsNone(get_current_tenant())
    
    def test_ensure_tenant_context(self):
        """Testa a função ensure_tenant_context"""
        # Inicialmente não há tenant
        self.assertIsNone(get_current_tenant())
        
        # Garante que tenant1 está no contexto
        changed = ensure_tenant_context(self.tenant1)
        self.assertTrue(changed)
        self.assertEqual(get_current_tenant(), self.tenant1)
        
        # Chama novamente - não deve mudar
        changed = ensure_tenant_context(self.tenant1)
        self.assertFalse(changed)
        self.assertEqual(get_current_tenant(), self.tenant1)
        
        # Muda para tenant2
        changed = ensure_tenant_context(self.tenant2)
        self.assertTrue(changed)
        self.assertEqual(get_current_tenant(), self.tenant2)
    
    def test_get_tenant_from_request(self):
        """Testa a extração de tenant do request"""
        # Request sem tenant
        request = self.factory.get('/')
        self.assertIsNone(get_tenant_from_request(request))
        
        # Request com tenant
        request.tenant = self.tenant1
        self.assertEqual(get_tenant_from_request(request), self.tenant1)
    
    def test_tenant_required_decorator(self):
        """Testa o decorator tenant_required"""
        @tenant_required
        def test_view(request):
            return "success"
        
        request = self.factory.get('/')
        
        # Sem tenant - deve retornar erro
        response = test_view(request)
        self.assertEqual(response.status_code, 400)
        
        # Com tenant - deve funcionar
        set_current_tenant(self.tenant1)
        response = test_view(request)
        self.assertEqual(response, "success")
        
        # Limpa contexto
        set_current_tenant(None)
    
    def test_tenant_admin_required_decorator(self):
        """Testa o decorator tenant_admin_required"""
        @tenant_admin_required
        def admin_view(request):
            return "admin_success"
        
        request = self.factory.get('/')
        request.user = self.user
        
        # Sem tenant - deve retornar erro
        response = admin_view(request)
        self.assertEqual(response.status_code, 400)
        
        # Com tenant mas sem usuário autenticado
        set_current_tenant(self.tenant1)
        request.user = User()  # Usuário não autenticado
        response = admin_view(request)
        self.assertEqual(response.status_code, 401)
        
        # Com tenant e usuário admin
        request.user = self.user
        response = admin_view(request)
        self.assertEqual(response, "admin_success")
        
        # Limpa contexto
        set_current_tenant(None)
    
    def test_with_tenant_context_decorator(self):
        """Testa o decorator with_tenant_context"""
        @with_tenant_context('teste1')
        def tenant_specific_view(request):
            return get_current_tenant()
        
        request = self.factory.get('/')
        
        # Deve executar no contexto do tenant especificado
        result = tenant_specific_view(request)
        self.assertEqual(result, self.tenant1)
        
        # Contexto deve estar limpo após a execução
        self.assertIsNone(get_current_tenant())


def run_basic_tests():
    """Função para executar testes básicos sem Django test runner"""
    print("=== Testando Sistema de Contexto de Tenant ===")
    
    try:
        # Teste básico de contexto
        print("1. Testando contexto básico...")
        assert get_current_tenant() is None
        
        # Simula um tenant (sem banco de dados)
        class MockTenant:
            def __init__(self, name, schema_name):
                self.name = name
                self.schema_name = schema_name
        
        mock_tenant = MockTenant("Test Tenant", "test_schema")
        
        set_current_tenant(mock_tenant)
        assert get_current_tenant() == mock_tenant
        
        set_current_tenant(None)
        assert get_current_tenant() is None
        
        print("✓ Contexto básico funcionando")
        
        # Teste de context manager
        print("2. Testando context manager...")
        with tenant_context(mock_tenant):
            assert get_current_tenant() == mock_tenant
        
        assert get_current_tenant() is None
        print("✓ Context manager funcionando")
        
        # Teste de stack
        print("3. Testando stack de contexto...")
        push_tenant_context(mock_tenant)
        assert get_current_tenant() == mock_tenant
        
        pop_tenant_context()
        assert get_current_tenant() is None
        
        print("✓ Stack de contexto funcionando")
        
        print("\n=== Todos os testes básicos passaram! ===")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {str(e)}")
        return False


if __name__ == "__main__":
    # Executa testes básicos se chamado diretamente
    run_basic_tests()
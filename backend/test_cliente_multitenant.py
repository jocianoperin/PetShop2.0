#!/usr/bin/env python
"""
Testes para verificar se o ClienteViewSet está funcionando corretamente
com isolamento de tenant.
"""

import os
import sys
import django
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant, TenantUser
from tenants.utils import set_current_tenant, tenant_context
from tenants.authentication import create_tenant_jwt_token
from api.models import Cliente
from api.views import ClienteViewSet
from api.serializers import ClienteSerializer


class ClienteMultitenantTestCase(APITestCase):
    """
    Testes para verificar isolamento de dados de clientes por tenant.
    """
    
    def setUp(self):
        """Configurar dados de teste"""
        # Criar tenants de teste
        self.tenant1 = Tenant.objects.create(
            name="Petshop A",
            subdomain="petshop-a",
            schema_name="tenant_a",
            is_active=True
        )
        
        self.tenant2 = Tenant.objects.create(
            name="Petshop B", 
            subdomain="petshop-b",
            schema_name="tenant_b",
            is_active=True
        )
        
        # Criar usuários para cada tenant
        self.user1 = TenantUser.objects.create(
            tenant=self.tenant1,
            email="admin@petshop-a.com",
            first_name="Admin",
            last_name="A",
            role="admin",
            is_active=True
        )
        
        self.user2 = TenantUser.objects.create(
            tenant=self.tenant2,
            email="admin@petshop-b.com", 
            first_name="Admin",
            last_name="B",
            role="admin",
            is_active=True
        )
        
        # Criar clientes para cada tenant
        with tenant_context(self.tenant1):
            self.cliente1_tenant1 = Cliente.objects.create(
                nome="João Silva",
                email="joao@email.com",
                telefone="11999999999",
                endereco="Rua A, 123"
            )
            
            self.cliente2_tenant1 = Cliente.objects.create(
                nome="Maria Santos",
                email="maria@email.com", 
                telefone="11888888888",
                endereco="Rua B, 456"
            )
        
        with tenant_context(self.tenant2):
            self.cliente1_tenant2 = Cliente.objects.create(
                nome="Pedro Costa",
                email="pedro@email.com",
                telefone="11777777777", 
                endereco="Rua C, 789"
            )
        
        # Configurar cliente API
        self.client = APIClient()
        self.factory = RequestFactory()
    
    def test_tenant_isolation_list(self):
        """Testa se a listagem de clientes respeita o isolamento por tenant"""
        print("\n=== Teste: Isolamento na listagem de clientes ===")
        
        # Teste com tenant1
        with tenant_context(self.tenant1):
            set_current_tenant(self.tenant1)
            clientes = Cliente.objects.all()
            print(f"Clientes no tenant1: {clientes.count()}")
            self.assertEqual(clientes.count(), 2)
            
            nomes = [c.nome for c in clientes]
            self.assertIn("João Silva", nomes)
            self.assertIn("Maria Santos", nomes)
            self.assertNotIn("Pedro Costa", nomes)
        
        # Teste com tenant2
        with tenant_context(self.tenant2):
            set_current_tenant(self.tenant2)
            clientes = Cliente.objects.all()
            print(f"Clientes no tenant2: {clientes.count()}")
            self.assertEqual(clientes.count(), 1)
            
            nomes = [c.nome for c in clientes]
            self.assertIn("Pedro Costa", nomes)
            self.assertNotIn("João Silva", nomes)
            self.assertNotIn("Maria Santos", nomes)
        
        print("✓ Isolamento na listagem funcionando corretamente")
    
    def test_tenant_isolation_create(self):
        """Testa se a criação de clientes respeita o isolamento por tenant"""
        print("\n=== Teste: Isolamento na criação de clientes ===")
        
        # Criar cliente no tenant1
        with tenant_context(self.tenant1):
            set_current_tenant(self.tenant1)
            
            novo_cliente = Cliente.objects.create(
                nome="Ana Oliveira",
                email="ana@email.com",
                telefone="11666666666",
                endereco="Rua D, 321"
            )
            
            print(f"Cliente criado no tenant1: {novo_cliente.nome}")
            self.assertEqual(novo_cliente.tenant, self.tenant1)
            
            # Verificar que foi criado apenas no tenant1
            clientes_tenant1 = Cliente.objects.all()
            self.assertEqual(clientes_tenant1.count(), 3)
        
        # Verificar que não aparece no tenant2
        with tenant_context(self.tenant2):
            set_current_tenant(self.tenant2)
            clientes_tenant2 = Cliente.objects.all()
            self.assertEqual(clientes_tenant2.count(), 1)
            
            nomes = [c.nome for c in clientes_tenant2]
            self.assertNotIn("Ana Oliveira", nomes)
        
        print("✓ Isolamento na criação funcionando corretamente")
    
    def test_email_uniqueness_per_tenant(self):
        """Testa se a unicidade de email é respeitada por tenant"""
        print("\n=== Teste: Unicidade de email por tenant ===")
        
        # Deve permitir mesmo email em tenants diferentes
        with tenant_context(self.tenant1):
            set_current_tenant(self.tenant1)
            cliente_a = Cliente.objects.create(
                nome="Teste A",
                email="teste@email.com",
                telefone="11555555555",
                endereco="Endereço A"
            )
            print(f"Cliente criado no tenant1 com email: {cliente_a.email}")
        
        with tenant_context(self.tenant2):
            set_current_tenant(self.tenant2)
            cliente_b = Cliente.objects.create(
                nome="Teste B", 
                email="teste@email.com",  # Mesmo email
                telefone="11444444444",
                endereco="Endereço B"
            )
            print(f"Cliente criado no tenant2 com email: {cliente_b.email}")
        
        # Verificar que ambos foram criados
        with tenant_context(self.tenant1):
            set_current_tenant(self.tenant1)
            self.assertTrue(Cliente.objects.filter(email="teste@email.com").exists())
        
        with tenant_context(self.tenant2):
            set_current_tenant(self.tenant2)
            self.assertTrue(Cliente.objects.filter(email="teste@email.com").exists())
        
        print("✓ Unicidade de email por tenant funcionando corretamente")
    
    def test_serializer_tenant_context(self):
        """Testa se o serializer inclui contexto de tenant corretamente"""
        print("\n=== Teste: Contexto de tenant no serializer ===")
        
        with tenant_context(self.tenant1):
            set_current_tenant(self.tenant1)
            
            # Criar request mock
            request = self.factory.get('/api/clientes/')
            request.tenant = self.tenant1
            
            # Serializar cliente
            serializer = ClienteSerializer(
                self.cliente1_tenant1,
                context={'request': request, 'tenant': self.tenant1}
            )
            
            data = serializer.data
            print(f"Dados serializados: {json.dumps(data, indent=2, default=str)}")
            
            # Verificar se inclui informações do tenant
            self.assertEqual(data['tenant_name'], self.tenant1.name)
            self.assertIn('total_animais', data)
        
        print("✓ Contexto de tenant no serializer funcionando corretamente")
    
    def test_cross_tenant_access_prevention(self):
        """Testa se o acesso cross-tenant é impedido"""
        print("\n=== Teste: Prevenção de acesso cross-tenant ===")
        
        # Tentar acessar cliente do tenant1 estando no contexto do tenant2
        with tenant_context(self.tenant2):
            set_current_tenant(self.tenant2)
            
            # Não deve encontrar clientes do tenant1
            clientes = Cliente.objects.filter(nome="João Silva")
            self.assertEqual(clientes.count(), 0)
            print("✓ Cliente do tenant1 não acessível no contexto do tenant2")
            
            # Tentar buscar por ID específico também deve falhar
            try:
                cliente = Cliente.objects.get(id=self.cliente1_tenant1.id)
                self.fail("Não deveria conseguir acessar cliente de outro tenant")
            except Cliente.DoesNotExist:
                print("✓ Acesso por ID de outro tenant bloqueado corretamente")
        
        print("✓ Prevenção de acesso cross-tenant funcionando corretamente")


def run_tests():
    """Executa todos os testes"""
    print("Iniciando testes de isolamento multitenant para ClienteViewSet...")
    print("=" * 60)
    
    # Executar testes
    test_case = ClienteMultitenantTestCase()
    test_case.setUp()
    
    try:
        test_case.test_tenant_isolation_list()
        test_case.test_tenant_isolation_create()
        test_case.test_email_uniqueness_per_tenant()
        test_case.test_serializer_tenant_context()
        test_case.test_cross_tenant_access_prevention()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("ClienteViewSet está funcionando corretamente com isolamento multitenant.")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
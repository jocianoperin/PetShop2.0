"""
Testes para os modelos base tenant-aware.
"""

import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import models

from .models import Tenant
from .base_models import TenantAwareModel, TenantAwareManager
from .utils import tenant_context, set_current_tenant, get_current_tenant


# Modelo de teste para usar nos testes
class TestModel(TenantAwareModel):
    """Modelo de teste para validar funcionalidade tenant-aware"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        app_label = 'tenants'


class TenantAwareManagerTestCase(TestCase):
    """Testes para o TenantAwareManager"""
    
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
        
        # Limpar contexto de tenant
        set_current_tenant(None)
    
    def tearDown(self):
        """Limpeza após os testes"""
        set_current_tenant(None)
    
    def test_get_queryset_without_tenant_context(self):
        """Testa que queryset retorna vazio sem contexto de tenant"""
        # Sem tenant no contexto, deve retornar queryset vazio
        queryset = TestModel.objects.all()
        self.assertEqual(queryset.count(), 0)
    
    def test_get_queryset_with_tenant_context(self):
        """Testa que queryset filtra por tenant atual"""
        # Criar objetos em diferentes tenants
        with tenant_context(self.tenant1):
            obj1 = TestModel.objects.create(name="Objeto Tenant 1")
        
        with tenant_context(self.tenant2):
            obj2 = TestModel.objects.create(name="Objeto Tenant 2")
        
        # Verificar isolamento
        with tenant_context(self.tenant1):
            queryset = TestModel.objects.all()
            self.assertEqual(queryset.count(), 1)
            self.assertEqual(queryset.first().name, "Objeto Tenant 1")
        
        with tenant_context(self.tenant2):
            queryset = TestModel.objects.all()
            self.assertEqual(queryset.count(), 1)
            self.assertEqual(queryset.first().name, "Objeto Tenant 2")
    
    def test_create_without_tenant_context(self):
        """Testa que create falha sem contexto de tenant"""
        with self.assertRaises(ValidationError):
            TestModel.objects.create(name="Teste")
    
    def test_create_with_tenant_context(self):
        """Testa que create funciona com contexto de tenant"""
        with tenant_context(self.tenant1):
            obj = TestModel.objects.create(name="Teste")
            self.assertEqual(obj.tenant, self.tenant1)
    
    def test_create_with_explicit_tenant(self):
        """Testa create com tenant explícito"""
        with tenant_context(self.tenant1):
            # Deve funcionar se o tenant explícito é o mesmo do contexto
            obj = TestModel.objects.create(name="Teste", tenant=self.tenant1)
            self.assertEqual(obj.tenant, self.tenant1)
            
            # Deve falhar se o tenant explícito é diferente do contexto
            with self.assertRaises(ValidationError):
                TestModel.objects.create(name="Teste 2", tenant=self.tenant2)
    
    def test_bulk_create(self):
        """Testa bulk_create com tenant-aware"""
        with tenant_context(self.tenant1):
            objs = [
                TestModel(name="Obj 1"),
                TestModel(name="Obj 2"),
                TestModel(name="Obj 3")
            ]
            created_objs = TestModel.objects.bulk_create(objs)
            
            # Verificar que todos foram criados com o tenant correto
            for obj in created_objs:
                self.assertEqual(obj.tenant, self.tenant1)
            
            # Verificar que foram criados no banco
            self.assertEqual(TestModel.objects.count(), 3)
    
    def test_bulk_create_mixed_tenants(self):
        """Testa que bulk_create falha com objetos de tenants diferentes"""
        with tenant_context(self.tenant1):
            objs = [
                TestModel(name="Obj 1", tenant=self.tenant1),
                TestModel(name="Obj 2", tenant=self.tenant2),  # Tenant diferente
            ]
            
            with self.assertRaises(ValidationError):
                TestModel.objects.bulk_create(objs)
    
    def test_get_or_create(self):
        """Testa get_or_create com tenant-aware"""
        with tenant_context(self.tenant1):
            # Primeira chamada deve criar
            obj1, created1 = TestModel.objects.get_or_create(
                name="Teste",
                defaults={'description': 'Descrição teste'}
            )
            self.assertTrue(created1)
            self.assertEqual(obj1.tenant, self.tenant1)
            
            # Segunda chamada deve retornar o existente
            obj2, created2 = TestModel.objects.get_or_create(
                name="Teste",
                defaults={'description': 'Outra descrição'}
            )
            self.assertFalse(created2)
            self.assertEqual(obj1.id, obj2.id)
    
    def test_get_or_create_different_tenants(self):
        """Testa que get_or_create isola por tenant"""
        # Criar objeto no tenant1
        with tenant_context(self.tenant1):
            obj1, created1 = TestModel.objects.get_or_create(name="Teste")
            self.assertTrue(created1)
        
        # Tentar get_or_create no tenant2 deve criar novo objeto
        with tenant_context(self.tenant2):
            obj2, created2 = TestModel.objects.get_or_create(name="Teste")
            self.assertTrue(created2)
            self.assertNotEqual(obj1.id, obj2.id)
            self.assertEqual(obj2.tenant, self.tenant2)
    
    def test_all_tenants_manager(self):
        """Testa o manager all_tenants"""
        # Criar objetos em diferentes tenants
        with tenant_context(self.tenant1):
            TestModel.objects.create(name="Obj Tenant 1")
        
        with tenant_context(self.tenant2):
            TestModel.objects.create(name="Obj Tenant 2")
        
        # all_tenants deve retornar todos os objetos
        all_objects = TestModel.objects.all_tenants()
        self.assertEqual(all_objects.count(), 2)
        
        # Verificar que temos objetos de ambos os tenants
        tenant_ids = set(obj.tenant.id for obj in all_objects)
        self.assertEqual(tenant_ids, {self.tenant1.id, self.tenant2.id})
    
    def test_for_tenant_manager(self):
        """Testa o método for_tenant"""
        # Criar objetos em diferentes tenants
        with tenant_context(self.tenant1):
            TestModel.objects.create(name="Obj Tenant 1")
        
        with tenant_context(self.tenant2):
            TestModel.objects.create(name="Obj Tenant 2")
        
        # for_tenant deve retornar apenas objetos do tenant especificado
        tenant1_objects = TestModel.objects.for_tenant(self.tenant1)
        self.assertEqual(tenant1_objects.count(), 1)
        self.assertEqual(tenant1_objects.first().name, "Obj Tenant 1")
        
        tenant2_objects = TestModel.objects.for_tenant(self.tenant2)
        self.assertEqual(tenant2_objects.count(), 1)
        self.assertEqual(tenant2_objects.first().name, "Obj Tenant 2")
    
    def test_count_by_tenant(self):
        """Testa o método count_by_tenant"""
        # Criar objetos em diferentes quantidades por tenant
        with tenant_context(self.tenant1):
            TestModel.objects.create(name="Obj 1")
            TestModel.objects.create(name="Obj 2")
        
        with tenant_context(self.tenant2):
            TestModel.objects.create(name="Obj 3")
        
        # count_by_tenant deve retornar contagens corretas
        counts = TestModel.objects.count_by_tenant()
        counts_dict = {item['tenant__subdomain']: item['count'] for item in counts}
        
        self.assertEqual(counts_dict['teste1'], 2)
        self.assertEqual(counts_dict['teste2'], 1)


class TenantAwareModelTestCase(TestCase):
    """Testes para o TenantAwareModel"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
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
        set_current_tenant(None)
    
    def tearDown(self):
        """Limpeza após os testes"""
        set_current_tenant(None)
    
    def test_save_without_tenant_context(self):
        """Testa que save falha sem contexto de tenant"""
        obj = TestModel(name="Teste")
        with self.assertRaises(ValidationError):
            obj.save()
    
    def test_save_with_tenant_context(self):
        """Testa que save funciona com contexto de tenant"""
        with tenant_context(self.tenant1):
            obj = TestModel(name="Teste")
            obj.save()
            self.assertEqual(obj.tenant, self.tenant1)
    
    def test_save_with_explicit_tenant(self):
        """Testa save com tenant explícito"""
        with tenant_context(self.tenant1):
            # Deve funcionar se o tenant explícito é o mesmo do contexto
            obj = TestModel(name="Teste", tenant=self.tenant1)
            obj.save()
            self.assertEqual(obj.tenant, self.tenant1)
    
    def test_save_cross_tenant_validation(self):
        """Testa que não é possível salvar objetos de outro tenant"""
        # Criar objeto no tenant1
        with tenant_context(self.tenant1):
            obj = TestModel.objects.create(name="Teste")
        
        # Tentar salvar no contexto do tenant2 deve falhar
        with tenant_context(self.tenant2):
            obj.name = "Teste Modificado"
            with self.assertRaises(ValidationError):
                obj.save()
    
    def test_delete_cross_tenant_validation(self):
        """Testa que não é possível excluir objetos de outro tenant"""
        # Criar objeto no tenant1
        with tenant_context(self.tenant1):
            obj = TestModel.objects.create(name="Teste")
        
        # Tentar excluir no contexto do tenant2 deve falhar
        with tenant_context(self.tenant2):
            with self.assertRaises(ValidationError):
                obj.delete()
    
    def test_tenant_properties(self):
        """Testa as propriedades de conveniência do tenant"""
        with tenant_context(self.tenant1):
            obj = TestModel.objects.create(name="Teste")
            
            self.assertEqual(obj.tenant_name, "Petshop Teste 1")
            self.assertEqual(obj.tenant_subdomain, "teste1")
    
    def test_clean_inactive_tenant(self):
        """Testa validação de tenant inativo"""
        # Desativar tenant
        self.tenant1.is_active = False
        self.tenant1.save()
        
        with tenant_context(self.tenant1):
            obj = TestModel(name="Teste", tenant=self.tenant1)
            with self.assertRaises(ValidationError):
                obj.clean()
    
    def test_get_tenant_field_name(self):
        """Testa método get_tenant_field_name"""
        self.assertEqual(TestModel.get_tenant_field_name(), 'tenant')


class TenantAwareQuerySetTestCase(TestCase):
    """Testes para o TenantAwareQuerySet"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
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
        
        # Criar objetos de teste
        with tenant_context(self.tenant1):
            TestModel.objects.create(name="Obj 1 Tenant 1")
            TestModel.objects.create(name="Obj 2 Tenant 1")
        
        with tenant_context(self.tenant2):
            TestModel.objects.create(name="Obj 1 Tenant 2")
        
        set_current_tenant(None)
    
    def tearDown(self):
        """Limpeza após os testes"""
        set_current_tenant(None)
    
    def test_for_tenant_queryset_method(self):
        """Testa método for_tenant do queryset"""
        # Usar all_tenants para acessar todos os objetos
        all_objects = TestModel.objects.all_tenants()
        
        # Filtrar por tenant específico
        tenant1_objects = all_objects.for_tenant(self.tenant1)
        self.assertEqual(tenant1_objects.count(), 2)
        
        tenant2_objects = all_objects.for_tenant(self.tenant2)
        self.assertEqual(tenant2_objects.count(), 1)
    
    def test_exclude_tenant_queryset_method(self):
        """Testa método exclude_tenant do queryset"""
        all_objects = TestModel.objects.all_tenants()
        
        # Excluir tenant1, deve retornar apenas objetos do tenant2
        without_tenant1 = all_objects.exclude_tenant(self.tenant1)
        self.assertEqual(without_tenant1.count(), 1)
        self.assertEqual(without_tenant1.first().tenant, self.tenant2)
    
    def test_current_tenant_only_queryset_method(self):
        """Testa método current_tenant_only do queryset"""
        all_objects = TestModel.objects.all_tenants()
        
        # Sem contexto de tenant, deve retornar vazio
        current_only = all_objects.current_tenant_only()
        self.assertEqual(current_only.count(), 0)
        
        # Com contexto de tenant, deve filtrar corretamente
        with tenant_context(self.tenant1):
            current_only = all_objects.current_tenant_only()
            self.assertEqual(current_only.count(), 2)
    
    def test_active_tenants_only_queryset_method(self):
        """Testa método active_tenants_only do queryset"""
        # Desativar tenant2
        self.tenant2.is_active = False
        self.tenant2.save()
        
        all_objects = TestModel.objects.all_tenants()
        active_only = all_objects.active_tenants_only()
        
        # Deve retornar apenas objetos do tenant1 (ativo)
        self.assertEqual(active_only.count(), 2)
        for obj in active_only:
            self.assertEqual(obj.tenant, self.tenant1)
    
    def test_by_tenant_plan_queryset_method(self):
        """Testa método by_tenant_plan do queryset"""
        # Alterar plano do tenant2
        self.tenant2.plan_type = 'premium'
        self.tenant2.save()
        
        all_objects = TestModel.objects.all_tenants()
        
        # Filtrar por plano básico
        basic_plan = all_objects.by_tenant_plan('basic')
        self.assertEqual(basic_plan.count(), 2)  # tenant1 objetos
        
        # Filtrar por plano premium
        premium_plan = all_objects.by_tenant_plan('premium')
        self.assertEqual(premium_plan.count(), 1)  # tenant2 objetos
    
    def test_tenant_statistics_queryset_method(self):
        """Testa método tenant_statistics do queryset"""
        all_objects = TestModel.objects.all_tenants()
        stats = all_objects.tenant_statistics()
        
        # Deve retornar estatísticas por tenant
        stats_dict = {item['tenant__subdomain']: item['count'] for item in stats}
        self.assertEqual(stats_dict['teste1'], 2)
        self.assertEqual(stats_dict['teste2'], 1)
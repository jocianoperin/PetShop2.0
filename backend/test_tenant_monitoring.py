#!/usr/bin/env python
"""
Teste simples para verificar o funcionamento do sistema de monitoramento multitenant.
"""

import os
import sys
import django
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant, TenantUser
from tenants.monitoring import (
    TenantLoggingMiddleware, 
    TenantMetrics, 
    get_tenant_metrics,
    audit_logger,
    get_tenant_metrics_summary,
    get_system_health
)
from tenants.utils import set_current_tenant


class TestTenantMonitoring(TestCase):
    """Testes para o sistema de monitoramento multitenant"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.factory = RequestFactory()
        
        # Criar tenant de teste
        self.tenant = Tenant.objects.create(
            name="Petshop Teste",
            subdomain="teste",
            schema_name="tenant_teste"
        )
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Middleware de teste
        self.middleware = TenantLoggingMiddleware(lambda r: None)
    
    def test_tenant_metrics_creation(self):
        """Testa criação de métricas por tenant"""
        tenant_id = str(self.tenant.id)
        
        # Obtém métricas do tenant
        metrics = get_tenant_metrics(tenant_id)
        
        # Verifica se é uma instância válida
        self.assertIsInstance(metrics, TenantMetrics)
        self.assertEqual(metrics.request_count, 0)
        self.assertEqual(metrics.error_count, 0)
    
    def test_metrics_request_tracking(self):
        """Testa rastreamento de requisições"""
        tenant_id = str(self.tenant.id)
        metrics = get_tenant_metrics(tenant_id)
        
        # Adiciona algumas requisições
        metrics.add_request(0.5, '/api/clientes/', 200)
        metrics.add_request(1.2, '/api/animais/', 200)
        metrics.add_request(0.8, '/api/clientes/', 404)
        
        # Verifica contadores
        self.assertEqual(metrics.request_count, 3)
        self.assertEqual(metrics.error_count, 1)
        self.assertEqual(len(metrics.response_times), 3)
        
        # Verifica tempo médio de resposta
        avg_time = metrics.get_avg_response_time()
        expected_avg = (0.5 + 1.2 + 0.8) / 3
        self.assertAlmostEqual(avg_time, expected_avg, places=2)
        
        # Verifica taxa de erro
        error_rate = metrics.get_error_rate()
        self.assertAlmostEqual(error_rate, 33.33, places=1)
    
    def test_audit_logging(self):
        """Testa sistema de auditoria"""
        set_current_tenant(self.tenant)
        
        # Registra algumas ações
        audit_logger.log_action('CREATE', self.user.id, {'resource': 'cliente'})
        audit_logger.log_action('UPDATE', self.user.id, {'resource': 'animal'})
        audit_logger.log_login(self.user.id, success=True, ip_address='127.0.0.1')
        
        # Verifica se as ações foram registradas nas métricas
        tenant_id = str(self.tenant.id)
        metrics = get_tenant_metrics(tenant_id)
        
        self.assertEqual(len(metrics.actions), 3)
        self.assertEqual(metrics.user_actions[self.user.id], 3)
    
    def test_middleware_request_processing(self):
        """Testa processamento de requisições pelo middleware"""
        # Criar requisição de teste
        request = self.factory.get('/api/clientes/')
        request.user = self.user
        
        # Mock do tenant atual
        with patch('tenants.monitoring.get_current_tenant', return_value=self.tenant):
            # Processar requisição
            self.middleware.process_request(request)
            
            # Verificar se informações foram adicionadas ao request
            self.assertTrue(hasattr(request, '_tenant_start_time'))
            self.assertTrue(hasattr(request, '_tenant_info'))
            
            tenant_info = request._tenant_info
            self.assertEqual(tenant_info['tenant_id'], str(self.tenant.id))
            self.assertEqual(tenant_info['tenant_name'], self.tenant.name)
            self.assertEqual(tenant_info['method'], 'GET')
            self.assertEqual(tenant_info['path'], '/api/clientes/')
    
    def test_metrics_summary(self):
        """Testa geração de resumo de métricas"""
        tenant_id = str(self.tenant.id)
        metrics = get_tenant_metrics(tenant_id)
        
        # Adiciona dados de teste
        metrics.add_request(0.5, '/api/clientes/', 200)
        metrics.add_request(1.0, '/api/animais/', 200)
        metrics.add_request(2.0, '/api/clientes/', 500)
        
        # Obtém resumo
        summary = get_tenant_metrics_summary(tenant_id)
        
        # Verifica estrutura do resumo
        expected_keys = [
            'request_count', 'avg_response_time', 'error_count', 
            'error_rate', 'last_activity', 'db_queries_count',
            'actions_count', 'top_endpoints', 'active_users'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # Verifica valores
        self.assertEqual(summary['request_count'], 3)
        self.assertEqual(summary['error_count'], 1)
        self.assertAlmostEqual(summary['error_rate'], 33.33, places=1)
        self.assertIn('/api/clientes/', summary['top_endpoints'])
    
    def test_system_health(self):
        """Testa informações de saúde do sistema"""
        # Adiciona dados de teste
        tenant_id = str(self.tenant.id)
        metrics = get_tenant_metrics(tenant_id)
        metrics.add_request(0.5, '/api/test/', 200)
        metrics.add_request(1.0, '/api/test/', 500)
        
        # Obtém saúde do sistema
        health = get_system_health()
        
        # Verifica estrutura
        expected_keys = [
            'total_tenants', 'total_requests', 'total_errors',
            'global_error_rate', 'avg_response_time', 'active_tenants',
            'timestamp'
        ]
        
        for key in expected_keys:
            self.assertIn(key, health)
        
        # Verifica valores básicos
        self.assertGreaterEqual(health['total_tenants'], 1)
        self.assertGreaterEqual(health['total_requests'], 2)
        self.assertGreaterEqual(health['total_errors'], 1)
    
    def test_db_query_monitoring(self):
        """Testa monitoramento de queries do banco"""
        tenant_id = str(self.tenant.id)
        metrics = get_tenant_metrics(tenant_id)
        
        # Adiciona queries de teste
        metrics.add_db_query({
            'sql': 'SELECT * FROM api_cliente',
            'time': 0.05
        })
        metrics.add_db_query({
            'sql': 'INSERT INTO api_animal VALUES (...)',
            'time': 0.12
        })
        
        # Verifica se foram registradas
        self.assertEqual(len(metrics.db_queries), 2)
        
        # Verifica estrutura das queries
        query = metrics.db_queries[0]
        self.assertIn('sql', query)
        self.assertIn('time', query)
        self.assertIn('timestamp', query)


def run_tests():
    """Executa os testes"""
    print("🧪 Executando testes do sistema de monitoramento multitenant...")
    
    # Configurar banco de teste
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.db import connection
    from django.core.management.color import no_style
    
    setup_test_environment()
    
    try:
        # Criar tabelas de teste
        style = no_style()
        sql = connection.ops.sql_table_creation_suffix()
        
        # Executar testes
        import unittest
        
        # Criar suite de testes
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestTenantMonitoring)
        
        # Executar testes
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Resultado
        if result.wasSuccessful():
            print("✅ Todos os testes passaram!")
            return True
        else:
            print("❌ Alguns testes falharam.")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar testes: {str(e)}")
        return False
    finally:
        teardown_test_environment()


def test_monitoring_integration():
    """Teste de integração do sistema de monitoramento"""
    print("\n🔍 Testando integração do sistema de monitoramento...")
    
    try:
        # Importar componentes
        from tenants.monitoring import (
            TenantLoggingMiddleware,
            audit_logger,
            get_tenant_metrics,
            get_system_health
        )
        
        print("✅ Importação dos componentes de monitoramento: OK")
        
        # Testar criação de métricas
        metrics = get_tenant_metrics('test-tenant-id')
        print("✅ Criação de métricas por tenant: OK")
        
        # Testar saúde do sistema
        health = get_system_health()
        print("✅ Informações de saúde do sistema: OK")
        
        # Testar middleware
        middleware = TenantLoggingMiddleware(lambda r: None)
        print("✅ Inicialização do middleware: OK")
        
        print("✅ Integração do sistema de monitoramento: SUCESSO")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("🚀 Iniciando testes do sistema de monitoramento multitenant")
    print("=" * 60)
    
    # Teste de integração básica
    integration_ok = test_monitoring_integration()
    
    if integration_ok:
        # Testes unitários completos
        tests_ok = run_tests()
        
        if tests_ok:
            print("\n🎉 Sistema de monitoramento implementado com sucesso!")
            print("\nRecursos implementados:")
            print("- ✅ Middleware de logging por tenant")
            print("- ✅ Métricas de performance por tenant")
            print("- ✅ Sistema de auditoria de ações")
            print("- ✅ Monitoramento de queries do banco")
            print("- ✅ Informações de saúde do sistema")
        else:
            print("\n⚠️  Sistema implementado, mas alguns testes falharam.")
    else:
        print("\n❌ Falha na integração do sistema de monitoramento.")
    
    print("\n" + "=" * 60)
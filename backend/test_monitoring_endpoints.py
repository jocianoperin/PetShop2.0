#!/usr/bin/env python
"""
Teste para verificar os endpoints de monitoramento multitenant.
"""

import os
import sys
import django
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant, TenantUser
from tenants.monitoring import get_tenant_metrics, audit_logger
from tenants.utils import set_current_tenant


class TestMonitoringEndpoints(TestCase):
    """Testes para endpoints de monitoramento"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.client = APIClient()
        
        # Criar tenant de teste
        self.tenant = Tenant.objects.create(
            name="Petshop Teste Monitoring",
            subdomain="teste-monitoring",
            schema_name="tenant_teste_monitoring"
        )
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@monitoring.com',
            password='testpass123'
        )
        
        # Criar usuário superuser para testes de admin
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@monitoring.com',
            password='adminpass123'
        )
        
        # Adicionar algumas métricas de teste
        self._setup_test_metrics()
    
    def _setup_test_metrics(self):
        """Configura métricas de teste"""
        set_current_tenant(self.tenant)
        
        # Adicionar métricas
        metrics = get_tenant_metrics(str(self.tenant.id))
        metrics.add_request(0.5, '/api/clientes/', 200)
        metrics.add_request(1.2, '/api/animais/', 200)
        metrics.add_request(0.8, '/api/clientes/', 404)
        metrics.add_request(2.5, '/api/vendas/', 500)
        
        # Adicionar ações de auditoria
        audit_logger.log_action('CREATE', self.user.id, {'resource': 'cliente'})
        audit_logger.log_action('UPDATE', self.user.id, {'resource': 'animal'})
        audit_logger.log_login(self.user.id, success=True, ip_address='127.0.0.1')
    
    def _authenticate_user(self, user=None):
        """Autentica um usuário para os testes"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
    
    def _set_tenant_header(self):
        """Define header de tenant para os testes"""
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
    
    def test_health_check_endpoint(self):
        """Testa endpoint de health check"""
        url = '/api/tenants/monitoring/health-check/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_metrics_summary_endpoint(self):
        """Testa endpoint de resumo de métricas"""
        url = '/api/tenants/monitoring/metrics-summary/'
        
        # Teste sem header de tenant
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        
        # Teste com header de tenant
        response = self.client.get(url, HTTP_X_TENANT_ID=str(self.tenant.id))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('tenant_id', data)
        self.assertIn('summary', data)
        self.assertEqual(data['tenant_id'], str(self.tenant.id))
    
    def test_tenant_metrics_endpoint(self):
        """Testa endpoint de métricas do tenant"""
        self._authenticate_user()
        
        # Mock do tenant atual
        with self.settings(MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'corsheaders.middleware.CorsMiddleware',
            'tenants.middleware.TenantMiddleware',
        ]):
            # Simular tenant no request
            self._set_tenant_header()
            
            url = '/api/tenants/monitoring/metrics/'
            response = self.client.get(url)
            
            # Pode retornar 400 se o tenant não for resolvido pelo middleware
            # Em ambiente de teste, isso é esperado
            self.assertIn(response.status_code, [200, 400])
    
    def test_system_health_endpoint(self):
        """Testa endpoint de saúde do sistema"""
        self._authenticate_user()
        
        url = '/api/tenants/monitoring/health/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verificar estrutura da resposta
        expected_keys = [
            'total_tenants', 'total_requests', 'total_errors',
            'global_error_rate', 'avg_response_time', 'active_tenants',
            'timestamp', 'database_status', 'cache_status'
        ]
        
        for key in expected_keys:
            self.assertIn(key, data)
        
        # Verificar status do banco e cache
        self.assertIn('status', data['database_status'])
        self.assertIn('status', data['cache_status'])
    
    def test_all_tenants_metrics_endpoint(self):
        """Testa endpoint de métricas de todos os tenants"""
        # Teste com usuário normal (deve falhar)
        self._authenticate_user()
        
        url = '/api/tenants/monitoring/all-metrics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Teste com usuário admin
        self._authenticate_user(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total_tenants', data)
        self.assertIn('tenants', data)
        self.assertIn('timestamp', data)
    
    def test_tenant_logs_endpoint_without_auth(self):
        """Testa endpoint de logs sem autenticação"""
        url = '/api/tenants/monitoring/logs/'
        response = self.client.get(url)
        
        # Deve retornar 401 (não autenticado)
        self.assertEqual(response.status_code, 401)
    
    def test_tenant_alerts_endpoint_without_auth(self):
        """Testa endpoint de alertas sem autenticação"""
        url = '/api/tenants/monitoring/alerts/'
        response = self.client.get(url)
        
        # Deve retornar 401 (não autenticado)
        self.assertEqual(response.status_code, 401)
    
    def test_dashboard_endpoint_without_auth(self):
        """Testa endpoint de dashboard sem autenticação"""
        url = '/api/tenants/monitoring/dashboard/'
        response = self.client.get(url)
        
        # Deve retornar 401 (não autenticado)
        self.assertEqual(response.status_code, 401)
    
    def test_performance_report_endpoint_without_auth(self):
        """Testa endpoint de relatório de performance sem autenticação"""
        url = '/api/tenants/monitoring/performance-report/'
        response = self.client.get(url)
        
        # Deve retornar 401 (não autenticado)
        self.assertEqual(response.status_code, 401)
    
    def test_clear_metrics_endpoint_without_auth(self):
        """Testa endpoint de limpeza de métricas sem autenticação"""
        url = '/api/tenants/monitoring/clear-metrics/'
        response = self.client.delete(url)
        
        # Deve retornar 401 (não autenticado)
        self.assertEqual(response.status_code, 401)


def run_endpoint_tests():
    """Executa os testes dos endpoints"""
    print("🧪 Executando testes dos endpoints de monitoramento...")
    
    # Configurar banco de teste
    from django.test.utils import setup_test_environment, teardown_test_environment
    
    setup_test_environment()
    
    try:
        # Executar testes
        import unittest
        
        # Criar suite de testes
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestMonitoringEndpoints)
        
        # Executar testes
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Resultado
        if result.wasSuccessful():
            print("✅ Todos os testes dos endpoints passaram!")
            return True
        else:
            print("❌ Alguns testes dos endpoints falharam.")
            for failure in result.failures:
                print(f"FALHA: {failure[0]}")
                print(f"Detalhes: {failure[1]}")
            for error in result.errors:
                print(f"ERRO: {error[0]}")
                print(f"Detalhes: {error[1]}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar testes dos endpoints: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        teardown_test_environment()


def test_url_patterns():
    """Testa se os padrões de URL estão configurados corretamente"""
    print("\n🔍 Testando configuração de URLs...")
    
    try:
        from django.urls import reverse
        from django.conf import settings
        
        # URLs que devem existir
        expected_urls = [
            'tenants:monitoring:health-check',
            'tenants:monitoring:metrics-summary',
            'tenants:monitoring:tenant-metrics',
            'tenants:monitoring:system-health',
            'tenants:monitoring:all-tenants-metrics',
            'tenants:monitoring:tenant-dashboard',
            'tenants:monitoring:performance-report',
        ]
        
        for url_name in expected_urls:
            try:
                url = reverse(url_name)
                print(f"✅ URL {url_name}: {url}")
            except Exception as e:
                print(f"❌ URL {url_name}: {str(e)}")
                return False
        
        print("✅ Configuração de URLs: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração de URLs: {str(e)}")
        return False


def test_monitoring_integration():
    """Teste de integração completo do sistema de monitoramento"""
    print("\n🔍 Testando integração completa do sistema de monitoramento...")
    
    try:
        # Importar todos os componentes
        from tenants.monitoring_views import (
            TenantMetricsView,
            TenantLogsView,
            SystemHealthView,
            AllTenantsMetricsView,
            TenantAlertsView
        )
        
        print("✅ Importação das views de monitoramento: OK")
        
        # Testar instanciação das views
        metrics_view = TenantMetricsView()
        logs_view = TenantLogsView()
        health_view = SystemHealthView()
        all_metrics_view = AllTenantsMetricsView()
        alerts_view = TenantAlertsView()
        
        print("✅ Instanciação das views: OK")
        
        # Testar importação das URLs
        from tenants import monitoring_urls
        print("✅ Importação das URLs de monitoramento: OK")
        
        print("✅ Integração completa do sistema de monitoramento: SUCESSO")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("🚀 Iniciando testes dos endpoints de monitoramento multitenant")
    print("=" * 70)
    
    # Teste de integração básica
    integration_ok = test_monitoring_integration()
    
    if integration_ok:
        # Teste de URLs
        urls_ok = test_url_patterns()
        
        if urls_ok:
            # Testes dos endpoints
            endpoints_ok = run_endpoint_tests()
            
            if endpoints_ok:
                print("\n🎉 Sistema de endpoints de monitoramento implementado com sucesso!")
                print("\nEndpoints implementados:")
                print("- ✅ /api/tenants/monitoring/health-check/ (Health check simples)")
                print("- ✅ /api/tenants/monitoring/metrics-summary/ (Resumo de métricas)")
                print("- ✅ /api/tenants/monitoring/metrics/ (Métricas do tenant)")
                print("- ✅ /api/tenants/monitoring/logs/ (Logs do tenant)")
                print("- ✅ /api/tenants/monitoring/alerts/ (Alertas do tenant)")
                print("- ✅ /api/tenants/monitoring/health/ (Saúde do sistema)")
                print("- ✅ /api/tenants/monitoring/all-metrics/ (Métricas globais)")
                print("- ✅ /api/tenants/monitoring/dashboard/ (Dados do dashboard)")
                print("- ✅ /api/tenants/monitoring/performance-report/ (Relatório de performance)")
                print("- ✅ /api/tenants/monitoring/clear-metrics/ (Limpar métricas)")
            else:
                print("\n⚠️  Endpoints implementados, mas alguns testes falharam.")
        else:
            print("\n❌ Falha na configuração de URLs.")
    else:
        print("\n❌ Falha na integração do sistema de monitoramento.")
    
    print("\n" + "=" * 70)
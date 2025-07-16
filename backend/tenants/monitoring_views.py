"""
Views para endpoints de métricas e monitoramento multitenant.
"""

import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .monitoring import (
    get_tenant_metrics_summary,
    get_all_tenants_metrics,
    get_system_health,
    get_tenant_logs,
    clear_tenant_metrics
)
from .utils import get_current_tenant, tenant_required
from .decorators import require_tenant, cache_tenant_metrics
from .models import Tenant


class TenantMetricsView(APIView):
    """
    API para métricas específicas de um tenant
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtém métricas do tenant atual"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({
                'error': 'Tenant não identificado',
                'code': 'TENANT_REQUIRED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtém métricas do tenant
            metrics = get_tenant_metrics_summary(str(tenant.id))
            
            # Adiciona informações do tenant
            metrics['tenant_info'] = {
                'id': str(tenant.id),
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'plan_type': tenant.plan_type,
                'is_active': tenant.is_active
            }
            
            return Response(metrics, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao obter métricas do tenant',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TenantLogsView(APIView):
    """
    API para logs específicos de um tenant
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtém logs do tenant atual"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({
                'error': 'Tenant não identificado',
                'code': 'TENANT_REQUIRED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Parâmetros de query
            limit = int(request.GET.get('limit', 100))
            level = request.GET.get('level', None)  # INFO, WARNING, ERROR
            
            # Limita o número máximo de logs
            limit = min(limit, 1000)
            
            # Obtém logs do tenant
            logs = get_tenant_logs(str(tenant.id), limit)
            
            # Filtra por nível se especificado
            if level:
                logs = [log for log in logs if log.get('level') == level.upper()]
            
            return Response({
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'logs_count': len(logs),
                'logs': logs
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                'error': 'Parâmetro limit deve ser um número inteiro',
                'code': 'INVALID_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Erro ao obter logs do tenant',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemHealthView(APIView):
    """
    API para informações de saúde do sistema
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_tenant_metrics(300))  # Cache por 5 minutos
    def get(self, request):
        """Obtém informações de saúde do sistema"""
        try:
            health = get_system_health()
            
            # Adiciona informações adicionais
            health['database_status'] = self._check_database_health()
            health['cache_status'] = self._check_cache_health()
            
            return Response(health, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao obter saúde do sistema',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_database_health(self):
        """Verifica saúde do banco de dados"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}
    
    def _check_cache_health(self):
        """Verifica saúde do cache"""
        try:
            test_key = 'health_check_test'
            test_value = 'ok'
            cache.set(test_key, test_value, timeout=60)
            cached_value = cache.get(test_key)
            
            if cached_value == test_value:
                cache.delete(test_key)
                return {'status': 'healthy', 'message': 'Cache working OK'}
            else:
                return {'status': 'unhealthy', 'message': 'Cache not working properly'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Cache error: {str(e)}'}


class AllTenantsMetricsView(APIView):
    """
    API para métricas de todos os tenants (apenas para admins)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtém métricas de todos os tenants"""
        # Verificar se o usuário é superuser
        if not request.user.is_superuser:
            return Response({
                'error': 'Acesso negado. Apenas administradores podem acessar métricas globais.',
                'code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Obtém métricas de todos os tenants
            all_metrics = get_all_tenants_metrics()
            
            # Adiciona informações dos tenants
            enriched_metrics = {}
            for tenant_id, metrics in all_metrics.items():
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                    enriched_metrics[tenant_id] = {
                        'tenant_info': {
                            'id': str(tenant.id),
                            'name': tenant.name,
                            'subdomain': tenant.subdomain,
                            'plan_type': tenant.plan_type,
                            'is_active': tenant.is_active,
                            'created_at': tenant.created_at.isoformat()
                        },
                        'metrics': metrics
                    }
                except Tenant.DoesNotExist:
                    # Tenant pode ter sido deletado
                    enriched_metrics[tenant_id] = {
                        'tenant_info': {'status': 'deleted'},
                        'metrics': metrics
                    }
            
            return Response({
                'total_tenants': len(enriched_metrics),
                'tenants': enriched_metrics,
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao obter métricas globais',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TenantAlertsView(APIView):
    """
    API para alertas específicos de um tenant
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtém alertas do tenant atual"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({
                'error': 'Tenant não identificado',
                'code': 'TENANT_REQUIRED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtém métricas do tenant
            metrics = get_tenant_metrics_summary(str(tenant.id))
            
            # Gera alertas baseado nas métricas
            alerts = self._generate_alerts(metrics, tenant)
            
            return Response({
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'alerts_count': len(alerts),
                'alerts': alerts,
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao obter alertas do tenant',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_alerts(self, metrics, tenant):
        """Gera alertas baseado nas métricas"""
        from django.conf import settings
        
        alerts = []
        thresholds = getattr(settings, 'TENANT_MONITORING', {}).get('ALERT_THRESHOLDS', {})
        
        # Alerta de taxa de erro alta
        error_rate_threshold = thresholds.get('ERROR_RATE', 10.0)
        if metrics.get('error_rate', 0) > error_rate_threshold:
            alerts.append({
                'type': 'HIGH_ERROR_RATE',
                'severity': 'warning',
                'message': f'Taxa de erro alta: {metrics["error_rate"]:.1f}% (limite: {error_rate_threshold}%)',
                'value': metrics['error_rate'],
                'threshold': error_rate_threshold,
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta de tempo de resposta alto
        response_time_threshold = thresholds.get('RESPONSE_TIME', 5.0)
        if metrics.get('avg_response_time', 0) > response_time_threshold:
            alerts.append({
                'type': 'SLOW_RESPONSE_TIME',
                'severity': 'warning',
                'message': f'Tempo de resposta alto: {metrics["avg_response_time"]:.2f}s (limite: {response_time_threshold}s)',
                'value': metrics['avg_response_time'],
                'threshold': response_time_threshold,
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta de muitas queries por requisição
        db_queries_threshold = thresholds.get('DB_QUERIES_PER_REQUEST', 50)
        avg_queries = metrics.get('db_queries_count', 0) / max(metrics.get('request_count', 1), 1)
        if avg_queries > db_queries_threshold:
            alerts.append({
                'type': 'HIGH_DB_USAGE',
                'severity': 'info',
                'message': f'Muitas queries por requisição: {avg_queries:.1f} (limite: {db_queries_threshold})',
                'value': avg_queries,
                'threshold': db_queries_threshold,
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta de inatividade
        last_activity = metrics.get('last_activity')
        if last_activity:
            try:
                last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                hours_since_activity = (datetime.now() - last_activity_dt.replace(tzinfo=None)).total_seconds() / 3600
                
                if hours_since_activity > 24:  # Mais de 24 horas sem atividade
                    alerts.append({
                        'type': 'TENANT_INACTIVE',
                        'severity': 'info',
                        'message': f'Tenant inativo há {hours_since_activity:.1f} horas',
                        'value': hours_since_activity,
                        'threshold': 24,
                        'timestamp': datetime.now().isoformat()
                    })
            except (ValueError, TypeError):
                pass
        
        return alerts


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_tenant
def clear_tenant_metrics_view(request):
    """
    Limpa métricas do tenant atual
    """
    tenant = get_current_tenant()
    
    try:
        clear_tenant_metrics(str(tenant.id))
        
        return Response({
            'message': 'Métricas do tenant limpas com sucesso',
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Erro ao limpar métricas do tenant',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_dashboard_data(request):
    """
    Endpoint para dados do dashboard do tenant
    """
    tenant = get_current_tenant()
    if not tenant:
        return Response({
            'error': 'Tenant não identificado',
            'code': 'TENANT_REQUIRED'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Obtém métricas
        metrics = get_tenant_metrics_summary(str(tenant.id))
        
        # Obtém logs recentes (apenas erros e warnings)
        recent_logs = get_tenant_logs(str(tenant.id), 20)
        important_logs = [
            log for log in recent_logs 
            if log.get('level') in ['WARNING', 'ERROR']
        ]
        
        # Calcula estatísticas do período
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        # Dados do dashboard
        dashboard_data = {
            'tenant_info': {
                'id': str(tenant.id),
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'plan_type': tenant.plan_type
            },
            'metrics': metrics,
            'recent_alerts': TenantAlertsView()._generate_alerts(metrics, tenant),
            'recent_logs': important_logs[:10],  # Últimos 10 logs importantes
            'quick_stats': {
                'total_requests': metrics.get('request_count', 0),
                'error_rate': metrics.get('error_rate', 0),
                'avg_response_time': metrics.get('avg_response_time', 0),
                'active_users': metrics.get('active_users', 0)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Erro ao obter dados do dashboard',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_performance_report(request):
    """
    Relatório de performance detalhado do tenant
    """
    tenant = get_current_tenant()
    if not tenant:
        return Response({
            'error': 'Tenant não identificado',
            'code': 'TENANT_REQUIRED'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Obtém métricas detalhadas
        metrics = get_tenant_metrics_summary(str(tenant.id))
        
        # Análise de performance
        performance_analysis = {
            'response_time_analysis': {
                'avg_response_time': metrics.get('avg_response_time', 0),
                'status': 'good' if metrics.get('avg_response_time', 0) < 1.0 else 'warning' if metrics.get('avg_response_time', 0) < 3.0 else 'critical'
            },
            'error_rate_analysis': {
                'error_rate': metrics.get('error_rate', 0),
                'status': 'good' if metrics.get('error_rate', 0) < 5.0 else 'warning' if metrics.get('error_rate', 0) < 15.0 else 'critical'
            },
            'usage_analysis': {
                'request_count': metrics.get('request_count', 0),
                'active_users': metrics.get('active_users', 0),
                'top_endpoints': metrics.get('top_endpoints', {})
            }
        }
        
        # Recomendações
        recommendations = []
        
        if metrics.get('avg_response_time', 0) > 2.0:
            recommendations.append({
                'type': 'performance',
                'message': 'Considere otimizar queries do banco de dados para melhorar o tempo de resposta',
                'priority': 'high'
            })
        
        if metrics.get('error_rate', 0) > 10.0:
            recommendations.append({
                'type': 'reliability',
                'message': 'Taxa de erro alta detectada. Verifique logs para identificar problemas',
                'priority': 'critical'
            })
        
        if metrics.get('db_queries_count', 0) > metrics.get('request_count', 1) * 20:
            recommendations.append({
                'type': 'database',
                'message': 'Muitas queries por requisição. Considere usar cache ou otimizar consultas',
                'priority': 'medium'
            })
        
        report = {
            'tenant_info': {
                'id': str(tenant.id),
                'name': tenant.name,
                'subdomain': tenant.subdomain
            },
            'report_period': {
                'generated_at': datetime.now().isoformat(),
                'data_points': metrics.get('request_count', 0)
            },
            'performance_analysis': performance_analysis,
            'recommendations': recommendations,
            'raw_metrics': metrics
        }
        
        return Response(report, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Erro ao gerar relatório de performance',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Views funcionais para compatibilidade
@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Endpoint simples de health check"""
    try:
        health = get_system_health()
        return JsonResponse({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'basic_stats': {
                'total_tenants': health.get('total_tenants', 0),
                'total_requests': health.get('total_requests', 0)
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def metrics_summary(request):
    """Endpoint para resumo rápido de métricas"""
    tenant_header = request.headers.get('X-Tenant-ID')
    
    if not tenant_header:
        return JsonResponse({
            'error': 'Header X-Tenant-ID requerido',
            'code': 'TENANT_HEADER_REQUIRED'
        }, status=400)
    
    try:
        metrics = get_tenant_metrics_summary(tenant_header)
        return JsonResponse({
            'tenant_id': tenant_header,
            'summary': {
                'requests': metrics.get('request_count', 0),
                'errors': metrics.get('error_count', 0),
                'avg_time': round(metrics.get('avg_response_time', 0), 3)
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'error': 'Erro ao obter métricas',
            'details': str(e)
        }, status=500)
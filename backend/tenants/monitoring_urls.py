"""
URLs para endpoints de monitoramento multitenant.
"""

from django.urls import path
from . import monitoring_views

app_name = 'monitoring'

urlpatterns = [
    # Endpoints principais de métricas
    path('metrics/', monitoring_views.TenantMetricsView.as_view(), name='tenant-metrics'),
    path('logs/', monitoring_views.TenantLogsView.as_view(), name='tenant-logs'),
    path('alerts/', monitoring_views.TenantAlertsView.as_view(), name='tenant-alerts'),
    
    # Endpoints de sistema
    path('health/', monitoring_views.SystemHealthView.as_view(), name='system-health'),
    path('all-metrics/', monitoring_views.AllTenantsMetricsView.as_view(), name='all-tenants-metrics'),
    
    # Endpoints de dashboard
    path('dashboard/', monitoring_views.tenant_dashboard_data, name='tenant-dashboard'),
    path('performance-report/', monitoring_views.tenant_performance_report, name='performance-report'),
    
    # Endpoints de ação
    path('clear-metrics/', monitoring_views.clear_tenant_metrics_view, name='clear-metrics'),
    
    # Endpoints simples (sem autenticação)
    path('health-check/', monitoring_views.health_check, name='health-check'),
    path('metrics-summary/', monitoring_views.metrics_summary, name='metrics-summary'),
]
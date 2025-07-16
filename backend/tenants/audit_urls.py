"""
URLs para sistema de auditoria e conformidade LGPD.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .audit_views import AuditLogViewSet, LGPDRequestViewSet, ComplianceReportViewSet

app_name = 'audit'

# Router para ViewSets
router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-logs')
router.register(r'lgpd-requests', LGPDRequestViewSet, basename='lgpd-requests')
router.register(r'compliance', ComplianceReportViewSet, basename='compliance-reports')

urlpatterns = [
    # APIs de auditoria via router
    path('', include(router.urls)),
    
    # Endpoints específicos de auditoria
    path('logs/statistics/', AuditLogViewSet.as_view({'get': 'statistics'}), name='audit-statistics'),
    path('logs/export/', AuditLogViewSet.as_view({'get': 'export_csv'}), name='audit-export'),
    
    # Endpoints de solicitações LGPD
    path('lgpd-requests/<uuid:pk>/process/', LGPDRequestViewSet.as_view({'post': 'process'}), name='lgpd-process'),
    
    # Endpoints de relatórios de conformidade
    path('compliance/lgpd-summary/', ComplianceReportViewSet.as_view({'get': 'lgpd_summary'}), name='lgpd-summary'),
    path('compliance/data-subject-report/', ComplianceReportViewSet.as_view({'get': 'data_subject_report'}), name='data-subject-report'),
    path('compliance/full-report/', ComplianceReportViewSet.as_view({'get': 'full_compliance_report'}), name='full-compliance-report'),
    path('compliance/export-csv/', ComplianceReportViewSet.as_view({'get': 'export_compliance_csv'}), name='export-compliance-csv'),
    path('compliance/export-json/', ComplianceReportViewSet.as_view({'get': 'export_compliance_json'}), name='export-compliance-json'),
    path('compliance/quick-check/', ComplianceReportViewSet.as_view({'get': 'quick_compliance_check'}), name='quick-compliance-check'),
    path('compliance/data-cleanup/', ComplianceReportViewSet.as_view({'post': 'schedule_data_cleanup'}), name='schedule-data-cleanup'),
]
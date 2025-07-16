"""
Views para sistema de auditoria e relatórios de conformidade LGPD.
Fornece APIs para consulta de logs de auditoria e geração de relatórios.
"""

from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .audit_models import AuditLog, LGPDRequest, DataChangeLog, AuditEventType
from .decorators import require_tenant
from .utils import get_current_tenant
from .lgpd_reports import LGPDComplianceReporter, generate_quick_compliance_report, schedule_data_cleanup
import csv
import json


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consulta de logs de auditoria.
    Permite filtros por data, usuário, tipo de evento, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return AuditLog.objects.none()
        
        queryset = AuditLog.objects.filter(tenant_id=tenant.id)
        
        # Filtros
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        user_email = self.request.query_params.get('user_email')
        if user_email:
            queryset = queryset.filter(user_email__icontains=user_email)
        
        # Filtro por data
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=end_date)
            except ValueError:
                pass
        
        # Filtro por dados sensíveis
        sensitive_only = self.request.query_params.get('sensitive_only')
        if sensitive_only and sensitive_only.lower() == 'true':
            queryset = queryset.filter(is_sensitive_data=True)
        
        return queryset.order_by('-timestamp')
    
    def list(self, request, *args, **kwargs):
        """Lista logs de auditoria com paginação"""
        queryset = self.get_queryset()
        
        # Paginação
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        paginator = Paginator(queryset, page_size)
        page_number = request.query_params.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Serializar dados
        logs = []
        for log in page_obj:
            logs.append({
                'id': str(log.id),
                'timestamp': log.timestamp.isoformat(),
                'event_type': log.event_type,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'action': log.action,
                'user_email': log.user_email,
                'ip_address': log.ip_address,
                'success': log.success,
                'is_sensitive_data': log.is_sensitive_data,
                'metadata': log.metadata
            })
        
        return Response({
            'results': logs,
            'count': paginator.count,
            'page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Retorna estatísticas dos logs de auditoria"""
        queryset = self.get_queryset()
        
        # Estatísticas por período (últimos 30 dias)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_logs = queryset.filter(timestamp__gte=thirty_days_ago)
        
        stats = {
            'total_events': queryset.count(),
            'recent_events': recent_logs.count(),
            'events_by_type': dict(
                recent_logs.values('event_type')
                .annotate(count=Count('id'))
                .values_list('event_type', 'count')
            ),
            'events_by_resource': dict(
                recent_logs.values('resource_type')
                .annotate(count=Count('id'))
                .values_list('resource_type', 'count')
            ),
            'failed_events': recent_logs.filter(success=False).count(),
            'sensitive_data_events': recent_logs.filter(is_sensitive_data=True).count(),
            'unique_users': recent_logs.exclude(user_email='').values('user_email').distinct().count()
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Exporta logs de auditoria em formato CSV"""
        queryset = self.get_queryset()[:10000]  # Limitar a 10k registros
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Event Type', 'Resource Type', 'Resource ID',
            'Action', 'User Email', 'IP Address', 'Success', 'Sensitive Data'
        ])
        
        for log in queryset:
            writer.writerow([
                log.timestamp.isoformat(),
                log.event_type,
                log.resource_type,
                log.resource_id,
                log.action,
                log.user_email,
                log.ip_address,
                log.success,
                log.is_sensitive_data
            ])
        
        return response


class LGPDRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de solicitações LGPD.
    Permite criar, listar e processar solicitações de direitos dos titulares.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return LGPDRequest.objects.none()
        
        return LGPDRequest.objects.filter(tenant_id=tenant.id)
    
    def create(self, request, *args, **kwargs):
        """Cria nova solicitação LGPD"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        data = request.data.copy()
        data['tenant_id'] = tenant.id
        
        # Calcular data limite (15 dias úteis)
        due_date = timezone.now() + timedelta(days=21)  # ~15 dias úteis
        data['due_date'] = due_date
        
        # Criar solicitação
        lgpd_request = LGPDRequest.objects.create(
            tenant_id=tenant.id,
            requester_name=data.get('requester_name'),
            requester_email=data.get('requester_email'),
            requester_document=data.get('requester_document', ''),
            request_type=data.get('request_type'),
            description=data.get('description'),
            affected_data_types=data.get('affected_data_types', []),
            due_date=due_date
        )
        
        # Log da criação
        lgpd_request.add_processing_log(
            'created',
            request.user.email if hasattr(request.user, 'email') else 'system',
            {'created_by': 'api'}
        )
        
        return Response({
            'id': str(lgpd_request.id),
            'status': lgpd_request.status,
            'due_date': lgpd_request.due_date.isoformat(),
            'message': 'Solicitação LGPD criada com sucesso'
        }, status=201)
    
    def list(self, request, *args, **kwargs):
        """Lista solicitações LGPD com filtros"""
        queryset = self.get_queryset()
        
        # Filtros
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        request_type = request.query_params.get('request_type')
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        # Paginação
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        paginator = Paginator(queryset, page_size)
        page_number = request.query_params.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Serializar dados
        requests_data = []
        for lgpd_req in page_obj:
            requests_data.append({
                'id': str(lgpd_req.id),
                'requester_name': lgpd_req.requester_name,
                'requester_email': lgpd_req.requester_email,
                'request_type': lgpd_req.request_type,
                'status': lgpd_req.status,
                'created_at': lgpd_req.created_at.isoformat(),
                'due_date': lgpd_req.due_date.isoformat(),
                'description': lgpd_req.description
            })
        
        return Response({
            'results': requests_data,
            'count': paginator.count,
            'page': page_obj.number,
            'total_pages': paginator.num_pages
        })
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Processa uma solicitação LGPD"""
        lgpd_request = self.get_object()
        action_type = request.data.get('action')
        
        if action_type == 'approve':
            lgpd_request.status = LGPDRequest.Status.IN_PROGRESS
            lgpd_request.assigned_to = request.user.id if hasattr(request.user, 'id') else None
            lgpd_request.add_processing_log(
                'approved',
                request.user.email if hasattr(request.user, 'email') else 'system',
                {'approved_by': request.user.email if hasattr(request.user, 'email') else 'system'}
            )
        
        elif action_type == 'complete':
            lgpd_request.status = LGPDRequest.Status.COMPLETED
            lgpd_request.completed_at = timezone.now()
            lgpd_request.response_data = request.data.get('response_data', {})
            lgpd_request.add_processing_log(
                'completed',
                request.user.email if hasattr(request.user, 'email') else 'system',
                {'completion_notes': request.data.get('notes', '')}
            )
        
        elif action_type == 'reject':
            lgpd_request.status = LGPDRequest.Status.REJECTED
            lgpd_request.rejection_reason = request.data.get('reason', '')
            lgpd_request.add_processing_log(
                'rejected',
                request.user.email if hasattr(request.user, 'email') else 'system',
                {'rejection_reason': lgpd_request.rejection_reason}
            )
        
        lgpd_request.save()
        
        return Response({
            'status': lgpd_request.status,
            'message': f'Solicitação {action_type}d com sucesso'
        })


class ComplianceReportViewSet(viewsets.ViewSet):
    """
    ViewSet para geração de relatórios de conformidade LGPD.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def lgpd_summary(self, request):
        """Relatório resumo de conformidade LGPD"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        # Período do relatório (últimos 12 meses)
        twelve_months_ago = timezone.now() - timedelta(days=365)
        
        # Estatísticas de solicitações LGPD
        lgpd_requests = LGPDRequest.objects.filter(
            tenant_id=tenant.id,
            created_at__gte=twelve_months_ago
        )
        
        # Estatísticas de auditoria
        audit_logs = AuditLog.objects.filter(
            tenant_id=tenant.id,
            timestamp__gte=twelve_months_ago,
            is_sensitive_data=True
        )
        
        # Mudanças em dados pessoais
        data_changes = DataChangeLog.objects.filter(
            tenant_id=tenant.id,
            changed_at__gte=twelve_months_ago,
            is_personal_data=True
        )
        
        report = {
            'report_period': {
                'start_date': twelve_months_ago.isoformat(),
                'end_date': timezone.now().isoformat()
            },
            'lgpd_requests': {
                'total': lgpd_requests.count(),
                'by_type': dict(
                    lgpd_requests.values('request_type')
                    .annotate(count=Count('id'))
                    .values_list('request_type', 'count')
                ),
                'by_status': dict(
                    lgpd_requests.values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                ),
                'average_processing_time_days': self._calculate_avg_processing_time(lgpd_requests),
                'overdue_requests': lgpd_requests.filter(
                    due_date__lt=timezone.now(),
                    status__in=[LGPDRequest.Status.PENDING, LGPDRequest.Status.IN_PROGRESS]
                ).count()
            },
            'data_access_events': {
                'total_sensitive_access': audit_logs.count(),
                'by_event_type': dict(
                    audit_logs.values('event_type')
                    .annotate(count=Count('id'))
                    .values_list('event_type', 'count')
                ),
                'failed_access_attempts': audit_logs.filter(success=False).count(),
                'unique_users_accessing_data': audit_logs.exclude(user_email='')
                    .values('user_email').distinct().count()
            },
            'data_changes': {
                'total_personal_data_changes': data_changes.count(),
                'sensitive_data_changes': data_changes.filter(is_sensitive_data=True).count(),
                'by_table': dict(
                    data_changes.values('table_name')
                    .annotate(count=Count('id'))
                    .values_list('table_name', 'count')
                ),
                'by_category': dict(
                    data_changes.values('data_category')
                    .annotate(count=Count('id'))
                    .values_list('data_category', 'count')
                )
            },
            'compliance_metrics': {
                'data_retention_compliance': self._check_data_retention_compliance(tenant),
                'consent_management_active': self._check_consent_management(tenant),
                'audit_log_retention_days': 2555,  # 7 anos
                'last_security_review': self._get_last_security_review(tenant)
            }
        }
        
        return Response(report)
    
    @action(detail=False, methods=['get'])
    def data_subject_report(self, request):
        """Relatório de atividades por titular de dados"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email parameter required'}, status=400)
        
        # Buscar todas as atividades relacionadas ao titular
        audit_logs = AuditLog.objects.filter(
            tenant_id=tenant.id,
            user_email=email
        ).order_by('-timestamp')[:100]  # Últimas 100 atividades
        
        # Solicitações LGPD do titular
        lgpd_requests = LGPDRequest.objects.filter(
            tenant_id=tenant.id,
            requester_email=email
        ).order_by('-created_at')
        
        # Mudanças em dados do titular
        data_changes = DataChangeLog.objects.filter(
            tenant_id=tenant.id,
            is_personal_data=True
        ).order_by('-changed_at')[:50]
        
        report = {
            'data_subject_email': email,
            'report_generated_at': timezone.now().isoformat(),
            'activities': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'event_type': log.event_type,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'ip_address': log.ip_address,
                    'success': log.success
                }
                for log in audit_logs
            ],
            'lgpd_requests': [
                {
                    'id': str(req.id),
                    'request_type': req.request_type,
                    'status': req.status,
                    'created_at': req.created_at.isoformat(),
                    'description': req.description
                }
                for req in lgpd_requests
            ],
            'data_changes': [
                {
                    'timestamp': change.changed_at.isoformat(),
                    'table_name': change.table_name,
                    'field_name': change.field_name,
                    'data_category': change.data_category,
                    'is_sensitive_data': change.is_sensitive_data
                }
                for change in data_changes
            ]
        }
        
        return Response(report)
    
    def _calculate_avg_processing_time(self, requests):
        """Calcula tempo médio de processamento de solicitações"""
        completed_requests = requests.filter(
            status=LGPDRequest.Status.COMPLETED,
            completed_at__isnull=False
        )
        
        if not completed_requests.exists():
            return 0
        
        total_time = sum(
            (req.completed_at - req.created_at).days
            for req in completed_requests
        )
        
        return total_time / completed_requests.count()
    
    def _check_data_retention_compliance(self, tenant):
        """Verifica conformidade com políticas de retenção"""
        # Verificar se há logs muito antigos que deveriam ser removidos
        retention_limit = timezone.now() - timedelta(days=2555)  # 7 anos
        old_logs = AuditLog.objects.filter(
            tenant_id=tenant.id,
            timestamp__lt=retention_limit
        ).count()
        
        return {
            'compliant': old_logs == 0,
            'old_records_count': old_logs,
            'retention_period_days': 2555
        }
    
    def _check_consent_management(self, tenant):
        """Verifica se o gerenciamento de consentimento está ativo"""
        from .encrypted_models import ConsentRecord
        
        recent_consents = ConsentRecord.objects.filter(
            tenant_id=tenant.id,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return recent_consents > 0
    
    def _get_last_security_review(self, tenant):
        """Obtém data da última revisão de segurança"""
        last_security_event = AuditLog.objects.filter(
            tenant_id=tenant.id,
            event_type=AuditEventType.SECURITY_EVENT
        ).order_by('-timestamp').first()
        
        if last_security_event:
            return last_security_event.timestamp.isoformat()
        
        return None
    
    @action(detail=False, methods=['get'])
    def full_compliance_report(self, request):
        """Gera relatório completo de conformidade LGPD"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        # Parâmetros de data
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                start_date = None
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                end_date = None
        
        # Gerar relatório usando o sistema de relatórios LGPD
        reporter = LGPDComplianceReporter(str(tenant.id))
        report = reporter.generate_full_compliance_report(start_date, end_date)
        
        return Response(report)
    
    @action(detail=False, methods=['get'])
    def export_compliance_csv(self, request):
        """Exporta relatório de conformidade em CSV"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        # Gerar relatório
        reporter = LGPDComplianceReporter(str(tenant.id))
        report = reporter.generate_full_compliance_report()
        
        # Exportar para CSV
        return reporter.export_to_csv(report)
    
    @action(detail=False, methods=['get'])
    def export_compliance_json(self, request):
        """Exporta relatório de conformidade em JSON"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        # Gerar relatório
        reporter = LGPDComplianceReporter(str(tenant.id))
        report = reporter.generate_full_compliance_report()
        
        # Exportar para JSON
        return reporter.export_to_json(report)
    
    @action(detail=False, methods=['post'])
    def schedule_data_cleanup(self, request):
        """Agenda limpeza de dados antigos para conformidade"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        retention_days = request.data.get('retention_days', 2555)  # 7 anos por padrão
        
        try:
            cleanup_result = schedule_data_cleanup(str(tenant.id), retention_days)
            return Response({
                'message': 'Limpeza de dados executada com sucesso',
                'result': cleanup_result
            })
        except Exception as e:
            return Response({
                'error': 'Erro ao executar limpeza de dados',
                'details': str(e)
            }, status=500)
    
    @action(detail=False, methods=['get'])
    def quick_compliance_check(self, request):
        """Verificação rápida de conformidade LGPD"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        try:
            report = generate_quick_compliance_report(str(tenant.id))
            
            # Extrair apenas métricas essenciais para resposta rápida
            quick_check = {
                'tenant_id': str(tenant.id),
                'compliance_score': report['compliance_metrics']['overall_compliance_score'],
                'compliance_level': report['compliance_metrics']['compliance_level'],
                'overdue_lgpd_requests': report['data_subject_rights']['overdue_requests'],
                'failed_operations_last_30_days': report['data_processing_activities'].get('failed_access_attempts', 0),
                'data_retention_compliant': report['data_retention']['retention_compliance'],
                'recommendations_count': len(report['recommendations']),
                'high_priority_issues': len([r for r in report['recommendations'] if r['priority'] == 'HIGH']),
                'last_check': timezone.now().isoformat()
            }
            
            return Response(quick_check)
        except Exception as e:
            return Response({
                'error': 'Erro ao gerar verificação de conformidade',
                'details': str(e)
            }, status=500)
"""
Sistema de relatórios de conformidade LGPD.
Gera relatórios detalhados para auditoria e conformidade com a Lei Geral de Proteção de Dados.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.http import HttpResponse
from io import StringIO
from .audit_models import AuditLog, LGPDRequest, DataChangeLog, AuditEventType
from .encrypted_models import ConsentRecord
from .utils import get_current_tenant


class LGPDComplianceReporter:
    """
    Classe principal para geração de relatórios de conformidade LGPD.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    def generate_full_compliance_report(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Gera relatório completo de conformidade LGPD.
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=365)  # Último ano
        if not end_date:
            end_date = timezone.now()
        
        report = {
            'report_metadata': {
                'tenant_id': self.tenant_id,
                'generated_at': timezone.now().isoformat(),
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'report_type': 'full_compliance'
            },
            'data_subject_rights': self._analyze_data_subject_rights(start_date, end_date),
            'data_processing_activities': self._analyze_data_processing(start_date, end_date),
            'consent_management': self._analyze_consent_management(start_date, end_date),
            'data_breaches': self._analyze_security_incidents(start_date, end_date),
            'data_retention': self._analyze_data_retention(),
            'access_controls': self._analyze_access_controls(start_date, end_date),
            'third_party_sharing': self._analyze_third_party_sharing(start_date, end_date),
            'compliance_metrics': self._calculate_compliance_metrics(start_date, end_date),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _analyze_data_subject_rights(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Analisa o exercício de direitos dos titulares de dados.
        """
        lgpd_requests = LGPDRequest.objects.filter(
            tenant_id=self.tenant_id,
            created_at__range=[start_date, end_date]
        )
        
        # Estatísticas por tipo de solicitação
        requests_by_type = dict(
            lgpd_requests.values('request_type')
            .annotate(count=Count('id'))
            .values_list('request_type', 'count')
        )
        
        # Estatísticas por status
        requests_by_status = dict(
            lgpd_requests.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Tempo médio de processamento
        completed_requests = lgpd_requests.filter(
            status=LGPDRequest.Status.COMPLETED,
            completed_at__isnull=False
        )
        
        avg_processing_time = 0
        if completed_requests.exists():
            total_time = sum(
                (req.completed_at - req.created_at).days
                for req in completed_requests
            )
            avg_processing_time = total_time / completed_requests.count()
        
        # Solicitações em atraso
        overdue_requests = lgpd_requests.filter(
            due_date__lt=timezone.now(),
            status__in=[LGPDRequest.Status.PENDING, LGPDRequest.Status.IN_PROGRESS]
        )
        
        return {
            'total_requests': lgpd_requests.count(),
            'requests_by_type': requests_by_type,
            'requests_by_status': requests_by_status,
            'average_processing_time_days': round(avg_processing_time, 2),
            'overdue_requests': overdue_requests.count(),
            'compliance_rate': self._calculate_compliance_rate(lgpd_requests),
            'most_common_request_type': max(requests_by_type.items(), key=lambda x: x[1])[0] if requests_by_type else None
        }
    
    def _analyze_data_processing(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Analisa atividades de processamento de dados pessoais.
        """
        # Logs de auditoria para dados pessoais
        personal_data_logs = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date],
            is_sensitive_data=True
        )
        
        # Atividades por tipo de evento
        activities_by_type = dict(
            personal_data_logs.values('event_type')
            .annotate(count=Count('id'))
            .values_list('event_type', 'count')
        )
        
        # Atividades por recurso
        activities_by_resource = dict(
            personal_data_logs.values('resource_type')
            .annotate(count=Count('id'))
            .values_list('resource_type', 'count')
        )
        
        # Usuários únicos que acessaram dados pessoais
        unique_users = personal_data_logs.exclude(user_email='').values('user_email').distinct().count()
        
        # Falhas de acesso
        failed_access = personal_data_logs.filter(success=False).count()
        
        return {
            'total_processing_activities': personal_data_logs.count(),
            'activities_by_type': activities_by_type,
            'activities_by_resource': activities_by_resource,
            'unique_users_accessing_data': unique_users,
            'failed_access_attempts': failed_access,
            'success_rate': round((personal_data_logs.filter(success=True).count() / personal_data_logs.count() * 100), 2) if personal_data_logs.count() > 0 else 100
        }
    
    def _analyze_consent_management(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Analisa o gerenciamento de consentimentos.
        """
        try:
            consents = ConsentRecord.objects.filter(
                tenant_id=self.tenant_id,
                created_at__range=[start_date, end_date]
            )
            
            # Consentimentos por tipo
            consents_by_type = dict(
                consents.values('consent_type')
                .annotate(count=Count('id'))
                .values_list('consent_type', 'count')
            )
            
            # Consentimentos por status
            consents_by_status = dict(
                consents.values('consent_status')
                .annotate(count=Count('id'))
                .values_list('consent_status', 'count')
            )
            
            # Retiradas de consentimento
            withdrawn_consents = consents.filter(consent_status='withdrawn').count()
            
            return {
                'total_consents': consents.count(),
                'consents_by_type': consents_by_type,
                'consents_by_status': consents_by_status,
                'withdrawn_consents': withdrawn_consents,
                'withdrawal_rate': round((withdrawn_consents / consents.count() * 100), 2) if consents.count() > 0 else 0,
                'active_consents': consents.filter(consent_status='granted').count()
            }
        except Exception:
            # ConsentRecord pode não existir ainda
            return {
                'total_consents': 0,
                'consents_by_type': {},
                'consents_by_status': {},
                'withdrawn_consents': 0,
                'withdrawal_rate': 0,
                'active_consents': 0,
                'note': 'Consent management system not yet implemented'
            }
    
    def _analyze_security_incidents(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Analisa incidentes de segurança e possíveis violações de dados.
        """
        security_events = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date],
            event_type=AuditEventType.SECURITY_EVENT
        )
        
        # Tipos de incidentes
        incidents_by_type = {}
        for event in security_events:
            action = event.action
            incidents_by_type[action] = incidents_by_type.get(action, 0) + 1
        
        # Tentativas de acesso negado
        permission_denied = security_events.filter(action='permission_denied').count()
        
        # Falhas de login
        login_failures = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date],
            event_type=AuditEventType.LOGIN,
            success=False
        ).count()
        
        return {
            'total_security_events': security_events.count(),
            'incidents_by_type': incidents_by_type,
            'permission_denied_attempts': permission_denied,
            'failed_login_attempts': login_failures,
            'potential_data_breaches': 0,  # Implementar lógica específica se necessário
            'security_score': self._calculate_security_score(security_events.count(), login_failures, permission_denied)
        }
    
    def _analyze_data_retention(self) -> Dict[str, Any]:
        """
        Analisa conformidade com políticas de retenção de dados.
        """
        # Verificar logs antigos que deveriam ser removidos
        retention_limit = timezone.now() - timedelta(days=2555)  # 7 anos
        old_audit_logs = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__lt=retention_limit
        ).count()
        
        # Verificar dados pessoais antigos
        old_data_changes = DataChangeLog.objects.filter(
            tenant_id=self.tenant_id,
            changed_at__lt=retention_limit,
            is_personal_data=True
        ).count()
        
        return {
            'retention_policy_days': 2555,  # 7 anos
            'old_audit_logs_count': old_audit_logs,
            'old_personal_data_changes_count': old_data_changes,
            'retention_compliance': old_audit_logs == 0 and old_data_changes == 0,
            'next_cleanup_date': (timezone.now() + timedelta(days=30)).isoformat(),
            'recommendations': [
                'Implementar limpeza automática de logs antigos',
                'Revisar políticas de retenção regularmente',
                'Documentar justificativas para retenção de dados'
            ] if old_audit_logs > 0 or old_data_changes > 0 else []
        }
    
    def _analyze_access_controls(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Analisa controles de acesso e autorizações.
        """
        # Logs de acesso a dados sensíveis
        access_logs = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date],
            is_sensitive_data=True
        )
        
        # Usuários únicos com acesso
        unique_users = access_logs.exclude(user_email='').values('user_email').distinct().count()
        
        # Acessos por usuário
        access_by_user = dict(
            access_logs.exclude(user_email='')
            .values('user_email')
            .annotate(count=Count('id'))
            .values_list('user_email', 'count')
        )
        
        # Horários de acesso (para detectar acessos fora do horário)
        unusual_hours_access = 0
        for log in access_logs:
            hour = log.timestamp.hour
            if hour < 6 or hour > 22:  # Fora do horário comercial
                unusual_hours_access += 1
        
        return {
            'total_access_events': access_logs.count(),
            'unique_users_with_access': unique_users,
            'access_by_user': access_by_user,
            'unusual_hours_access': unusual_hours_access,
            'most_active_user': max(access_by_user.items(), key=lambda x: x[1])[0] if access_by_user else None,
            'access_control_score': self._calculate_access_control_score(access_logs, unusual_hours_access)
        }
    
    def _analyze_third_party_sharing(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Analisa compartilhamento de dados com terceiros.
        """
        # Logs de exportação que podem indicar compartilhamento
        export_logs = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date],
            event_type=AuditEventType.EXPORT,
            is_sensitive_data=True
        )
        
        # Logs de LGPD que podem ser exportações para terceiros
        lgpd_exports = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date],
            event_type=AuditEventType.LGPD_EXPORT
        )
        
        return {
            'data_exports': export_logs.count(),
            'lgpd_data_exports': lgpd_exports.count(),
            'total_third_party_sharing': export_logs.count() + lgpd_exports.count(),
            'sharing_compliance': True,  # Assumir conformidade por padrão
            'documented_sharing_agreements': 0,  # Implementar se necessário
            'recommendations': [
                'Documentar todos os acordos de compartilhamento',
                'Implementar controles de exportação mais rigorosos',
                'Revisar necessidade de cada exportação'
            ] if export_logs.count() > 10 else []
        }
    
    def _calculate_compliance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Calcula métricas gerais de conformidade.
        """
        # Solicitações LGPD
        lgpd_requests = LGPDRequest.objects.filter(
            tenant_id=self.tenant_id,
            created_at__range=[start_date, end_date]
        )
        
        # Logs de auditoria
        audit_logs = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__range=[start_date, end_date]
        )
        
        # Calcular pontuação de conformidade
        compliance_score = self._calculate_overall_compliance_score(lgpd_requests, audit_logs)
        
        return {
            'overall_compliance_score': compliance_score,
            'compliance_level': self._get_compliance_level(compliance_score),
            'total_audit_events': audit_logs.count(),
            'sensitive_data_events': audit_logs.filter(is_sensitive_data=True).count(),
            'failed_operations': audit_logs.filter(success=False).count(),
            'success_rate': round((audit_logs.filter(success=True).count() / audit_logs.count() * 100), 2) if audit_logs.count() > 0 else 100,
            'data_protection_maturity': self._assess_data_protection_maturity()
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """
        Gera recomendações para melhorar a conformidade LGPD.
        """
        recommendations = []
        
        # Verificar se há solicitações LGPD em atraso
        overdue_requests = LGPDRequest.objects.filter(
            tenant_id=self.tenant_id,
            due_date__lt=timezone.now(),
            status__in=[LGPDRequest.Status.PENDING, LGPDRequest.Status.IN_PROGRESS]
        ).count()
        
        if overdue_requests > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Subject Rights',
                'title': 'Solicitações LGPD em Atraso',
                'description': f'Existem {overdue_requests} solicitações LGPD em atraso que precisam ser processadas.',
                'action_required': 'Processar solicitações pendentes imediatamente'
            })
        
        # Verificar logs antigos
        old_logs = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__lt=timezone.now() - timedelta(days=2555)
        ).count()
        
        if old_logs > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Data Retention',
                'title': 'Logs de Auditoria Antigos',
                'description': f'Existem {old_logs} logs de auditoria que excedem o período de retenção.',
                'action_required': 'Implementar processo de limpeza automática de logs'
            })
        
        # Verificar falhas de segurança
        recent_security_events = AuditLog.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__gte=timezone.now() - timedelta(days=30),
            event_type=AuditEventType.SECURITY_EVENT
        ).count()
        
        if recent_security_events > 10:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Security',
                'title': 'Eventos de Segurança Elevados',
                'description': f'Foram detectados {recent_security_events} eventos de segurança no último mês.',
                'action_required': 'Revisar controles de acesso e implementar medidas de segurança adicionais'
            })
        
        # Recomendações gerais
        recommendations.extend([
            {
                'priority': 'LOW',
                'category': 'Documentation',
                'title': 'Documentação de Processos',
                'description': 'Manter documentação atualizada de todos os processos de tratamento de dados.',
                'action_required': 'Revisar e atualizar documentação regularmente'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Training',
                'title': 'Treinamento em LGPD',
                'description': 'Garantir que todos os usuários recebam treinamento adequado sobre LGPD.',
                'action_required': 'Implementar programa de treinamento contínuo'
            }
        ])
        
        return recommendations
    
    def _calculate_compliance_rate(self, lgpd_requests) -> float:
        """
        Calcula taxa de conformidade para solicitações LGPD.
        """
        if lgpd_requests.count() == 0:
            return 100.0
        
        from django.db import models
        completed_on_time = lgpd_requests.filter(
            status=LGPDRequest.Status.COMPLETED,
            completed_at__lte=models.F('due_date')
        ).count()
        
        return round((completed_on_time / lgpd_requests.count() * 100), 2)
    
    def _calculate_security_score(self, total_events: int, login_failures: int, permission_denied: int) -> int:
        """
        Calcula pontuação de segurança (0-100).
        """
        if total_events == 0:
            return 100
        
        # Penalizar por eventos de segurança
        penalty = min(total_events * 2, 50)  # Máximo 50 pontos de penalidade
        penalty += min(login_failures * 1, 25)  # Máximo 25 pontos por falhas de login
        penalty += min(permission_denied * 3, 25)  # Máximo 25 pontos por acessos negados
        
        return max(100 - penalty, 0)
    
    def _calculate_access_control_score(self, access_logs, unusual_hours: int) -> int:
        """
        Calcula pontuação de controle de acesso (0-100).
        """
        if access_logs.count() == 0:
            return 100
        
        # Penalizar por acessos em horários incomuns
        unusual_rate = unusual_hours / access_logs.count()
        penalty = min(unusual_rate * 100, 30)  # Máximo 30 pontos de penalidade
        
        return max(100 - penalty, 70)  # Mínimo 70 pontos
    
    def _calculate_overall_compliance_score(self, lgpd_requests, audit_logs) -> int:
        """
        Calcula pontuação geral de conformidade (0-100).
        """
        scores = []
        
        # Pontuação baseada em solicitações LGPD
        if lgpd_requests.count() > 0:
            compliance_rate = self._calculate_compliance_rate(lgpd_requests)
            scores.append(compliance_rate)
        
        # Pontuação baseada em logs de auditoria
        if audit_logs.count() > 0:
            success_rate = audit_logs.filter(success=True).count() / audit_logs.count() * 100
            scores.append(success_rate)
        
        # Pontuação baseada em eventos de segurança
        security_events = audit_logs.filter(event_type=AuditEventType.SECURITY_EVENT).count()
        security_score = self._calculate_security_score(security_events, 0, 0)
        scores.append(security_score)
        
        # Média das pontuações
        return round(sum(scores) / len(scores)) if scores else 85  # Padrão 85 se não houver dados
    
    def _get_compliance_level(self, score: int) -> str:
        """
        Determina o nível de conformidade baseado na pontuação.
        """
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 80:
            return 'GOOD'
        elif score >= 70:
            return 'SATISFACTORY'
        elif score >= 60:
            return 'NEEDS_IMPROVEMENT'
        else:
            return 'CRITICAL'
    
    def _assess_data_protection_maturity(self) -> str:
        """
        Avalia o nível de maturidade em proteção de dados.
        """
        # Verificar se há processos implementados
        has_audit_logs = AuditLog.objects.filter(tenant_id=self.tenant_id).exists()
        has_lgpd_requests = LGPDRequest.objects.filter(tenant_id=self.tenant_id).exists()
        
        try:
            has_consent_management = ConsentRecord.objects.filter(tenant_id=self.tenant_id).exists()
        except:
            has_consent_management = False
        
        maturity_score = 0
        if has_audit_logs:
            maturity_score += 1
        if has_lgpd_requests:
            maturity_score += 1
        if has_consent_management:
            maturity_score += 1
        
        maturity_levels = {
            0: 'INITIAL',
            1: 'DEVELOPING',
            2: 'MANAGED',
            3: 'OPTIMIZED'
        }
        
        return maturity_levels.get(maturity_score, 'INITIAL')
    
    def export_to_csv(self, report_data: Dict[str, Any]) -> HttpResponse:
        """
        Exporta relatório para formato CSV.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="lgpd_compliance_report_{self.tenant_id}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Cabeçalho
        writer.writerow(['LGPD Compliance Report'])
        writer.writerow(['Generated at:', report_data['report_metadata']['generated_at']])
        writer.writerow(['Tenant ID:', self.tenant_id])
        writer.writerow(['Period:', f"{report_data['report_metadata']['period_start']} to {report_data['report_metadata']['period_end']}"])
        writer.writerow([])
        
        # Métricas de conformidade
        writer.writerow(['Compliance Metrics'])
        compliance = report_data['compliance_metrics']
        writer.writerow(['Overall Score:', compliance['overall_compliance_score']])
        writer.writerow(['Compliance Level:', compliance['compliance_level']])
        writer.writerow(['Success Rate:', f"{compliance['success_rate']}%"])
        writer.writerow([])
        
        # Direitos dos titulares
        writer.writerow(['Data Subject Rights'])
        rights = report_data['data_subject_rights']
        writer.writerow(['Total Requests:', rights['total_requests']])
        writer.writerow(['Average Processing Time (days):', rights['average_processing_time_days']])
        writer.writerow(['Overdue Requests:', rights['overdue_requests']])
        writer.writerow([])
        
        # Recomendações
        writer.writerow(['Recommendations'])
        writer.writerow(['Priority', 'Category', 'Title', 'Description'])
        for rec in report_data['recommendations']:
            writer.writerow([rec['priority'], rec['category'], rec['title'], rec['description']])
        
        return response
    
    def export_to_json(self, report_data: Dict[str, Any]) -> HttpResponse:
        """
        Exporta relatório para formato JSON.
        """
        response = HttpResponse(
            json.dumps(report_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="lgpd_compliance_report_{self.tenant_id}_{timezone.now().strftime("%Y%m%d")}.json"'
        
        return response


# Função utilitária para gerar relatório rápido
def generate_quick_compliance_report(tenant_id: str) -> Dict[str, Any]:
    """
    Gera relatório rápido de conformidade para um tenant.
    """
    reporter = LGPDComplianceReporter(tenant_id)
    return reporter.generate_full_compliance_report()


# Função para agendar limpeza de dados antigos
def schedule_data_cleanup(tenant_id: str, retention_days: int = 2555):
    """
    Agenda limpeza de dados antigos para conformidade com retenção.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    # Remover logs de auditoria antigos
    old_audit_logs = AuditLog.objects.filter(
        tenant_id=tenant_id,
        timestamp__lt=cutoff_date
    )
    
    # Remover logs de mudanças de dados antigos
    old_data_changes = DataChangeLog.objects.filter(
        tenant_id=tenant_id,
        changed_at__lt=cutoff_date
    )
    
    audit_count = old_audit_logs.count()
    changes_count = old_data_changes.count()
    
    # Executar limpeza
    old_audit_logs.delete()
    old_data_changes.delete()
    
    return {
        'audit_logs_removed': audit_count,
        'data_changes_removed': changes_count,
        'cleanup_date': timezone.now().isoformat()
    }
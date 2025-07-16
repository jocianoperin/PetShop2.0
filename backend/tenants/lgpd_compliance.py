"""
Sistema de conformidade LGPD para dados sensíveis por tenant.
Implementa validações, auditoria e relatórios de conformidade.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.conf import settings
from .models import Tenant
from .encrypted_models import DataProcessingLog, ConsentRecord

logger = logging.getLogger('tenants.lgpd')


class LGPDValidator:
    """
    Validador de conformidade LGPD para operações de dados pessoais.
    """
    
    # Categorias de dados pessoais segundo LGPD
    PERSONAL_DATA_CATEGORIES = {
        'identificacao': ['nome', 'cpf', 'rg', 'documento', 'email'],
        'contato': ['telefone', 'endereco', 'endereco_completo'],
        'financeiro': ['dados_bancarios', 'cartao_credito', 'renda'],
        'saude': ['historico_medico', 'observacoes_medicas', 'medicamentos', 'alergias'],
        'comportamental': ['observacoes_pessoais', 'preferencias'],
        'biometrico': ['foto', 'impressao_digital', 'reconhecimento_facial']
    }
    
    # Dados sensíveis que requerem consentimento específico
    SENSITIVE_DATA = {
        'saude', 'biometrico', 'origem_racial', 'conviccao_religiosa',
        'opiniao_politica', 'filiacao_sindical', 'vida_sexual'
    }
    
    # Bases legais para processamento (Art. 7º LGPD)
    LEGAL_BASIS = {
        'consent': 'Consentimento do titular',
        'contract': 'Execução de contrato',
        'legal_obligation': 'Cumprimento de obrigação legal',
        'vital_interests': 'Proteção da vida ou incolumidade física',
        'public_interest': 'Execução de políticas públicas',
        'legitimate_interests': 'Interesse legítimo do controlador'
    }
    
    @classmethod
    def validate_data_processing(cls, tenant: Tenant, data_subject_type: str, 
                                data_subject_id: str, field_name: str, 
                                operation: str, legal_basis: str = 'consent') -> bool:
        """
        Valida se o processamento de dados está em conformidade com LGPD.
        
        Args:
            tenant: Tenant que está processando os dados
            data_subject_type: Tipo do titular dos dados ('cliente', 'animal', 'usuario')
            data_subject_id: ID do titular dos dados
            field_name: Nome do campo sendo processado
            operation: Operação sendo realizada ('read', 'write', 'update', 'delete')
            legal_basis: Base legal para o processamento
            
        Returns:
            bool: True se o processamento é válido, False caso contrário
        """
        try:
            # 1. Verificar se é dado pessoal
            if not cls.is_personal_data(field_name):
                return True
            
            # 2. Verificar se é dado sensível
            if cls.is_sensitive_data(field_name):
                # Dados sensíveis sempre requerem consentimento específico
                if legal_basis != 'consent':
                    logger.warning(
                        f"Sensitive data {field_name} requires explicit consent. "
                        f"Legal basis '{legal_basis}' not sufficient."
                    )
                    return False
                
                # Verificar consentimento específico
                if not cls.has_valid_consent(tenant, data_subject_type, data_subject_id, field_name):
                    logger.warning(
                        f"No valid consent found for sensitive data {field_name} "
                        f"for {data_subject_type} {data_subject_id}"
                    )
                    return False
            
            # 3. Verificar base legal
            if not cls.validate_legal_basis(legal_basis, field_name, operation):
                return False
            
            # 4. Verificar finalidade
            if not cls.validate_purpose_limitation(tenant, data_subject_type, field_name):
                return False
            
            # 5. Log da validação
            cls.log_validation_result(
                tenant, data_subject_type, data_subject_id, 
                field_name, operation, legal_basis, True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating LGPD compliance: {str(e)}")
            cls.log_validation_result(
                tenant, data_subject_type, data_subject_id, 
                field_name, operation, legal_basis, False, str(e)
            )
            return False
    
    @classmethod
    def is_personal_data(cls, field_name: str) -> bool:
        """Verifica se um campo contém dados pessoais"""
        field_lower = field_name.lower()
        
        # Lista de exceções - campos que contêm palavras de dados pessoais mas não são dados pessoais
        exceptions = ['nome_produto', 'nome_servico', 'nome_categoria', 'nome_item']
        
        if field_lower in exceptions:
            return False
        
        for category, fields in cls.PERSONAL_DATA_CATEGORIES.items():
            for field in fields:
                # Verificar correspondência exata
                if field == field_lower:
                    return True
                # Verificar se o campo pessoal está contido no nome do campo
                # mas não em contextos que não são dados pessoais
                if field in field_lower and not any(exc in field_lower for exc in ['produto', 'servico', 'categoria', 'item']):
                    return True
        return False
    
    @classmethod
    def is_sensitive_data(cls, field_name: str) -> bool:
        """Verifica se um campo contém dados pessoais sensíveis"""
        field_lower = field_name.lower()
        
        # Verificar categorias sensíveis
        sensitive_keywords = [
            'historico_medico', 'observacoes_medicas', 'medicamentos', 
            'alergias', 'condicoes_especiais', 'foto', 'biometrico'
        ]
        
        return any(keyword in field_lower for keyword in sensitive_keywords)
    
    @classmethod
    def has_valid_consent(cls, tenant: Tenant, data_subject_type: str, 
                         data_subject_id: str, field_name: str) -> bool:
        """Verifica se há consentimento válido para o processamento"""
        try:
            consent = ConsentRecord.objects.get(
                tenant=tenant,
                data_subject_type=data_subject_type,
                data_subject_id=data_subject_id,
                consent_given=True,
                revoked_at__isnull=True
            )
            
            # Verificar se o campo está nas categorias de dados consentidas
            return field_name in consent.data_categories
            
        except ConsentRecord.DoesNotExist:
            return False
        except ConsentRecord.MultipleObjectsReturned:
            # Se há múltiplos consentimentos, verificar se algum é válido
            consents = ConsentRecord.objects.filter(
                tenant=tenant,
                data_subject_type=data_subject_type,
                data_subject_id=data_subject_id,
                consent_given=True,
                revoked_at__isnull=True
            )
            
            for consent in consents:
                if field_name in consent.data_categories:
                    return True
            return False
    
    @classmethod
    def validate_legal_basis(cls, legal_basis: str, field_name: str, operation: str) -> bool:
        """Valida se a base legal é apropriada para a operação"""
        if legal_basis not in cls.LEGAL_BASIS:
            logger.warning(f"Invalid legal basis: {legal_basis}")
            return False
        
        # Regras específicas por base legal
        if legal_basis == 'consent':
            # Consentimento é sempre válido se presente
            return True
        elif legal_basis == 'contract':
            # Execução de contrato - válido para dados necessários ao serviço
            contract_fields = ['nome', 'email', 'telefone', 'endereco']
            return any(field in field_name.lower() for field in contract_fields)
        elif legal_basis == 'legal_obligation':
            # Obrigação legal - válido para dados exigidos por lei
            legal_fields = ['cpf', 'rg', 'documento']
            return any(field in field_name.lower() for field in legal_fields)
        elif legal_basis == 'vital_interests':
            # Proteção da vida - válido para dados médicos em emergências
            vital_fields = ['historico_medico', 'alergias', 'medicamentos']
            return any(field in field_name.lower() for field in vital_fields)
        
        return True
    
    @classmethod
    def validate_purpose_limitation(cls, tenant: Tenant, data_subject_type: str, field_name: str) -> bool:
        """Valida se o processamento está dentro da finalidade declarada"""
        # Por enquanto, assumimos que o processamento está dentro da finalidade
        # Em uma implementação completa, isso seria verificado contra as finalidades
        # declaradas no registro de atividades de tratamento
        return True
    
    @classmethod
    def log_validation_result(cls, tenant: Tenant, data_subject_type: str, 
                            data_subject_id: str, field_name: str, operation: str,
                            legal_basis: str, success: bool, error_message: str = None):
        """Registra o resultado da validação para auditoria"""
        try:
            DataProcessingLog.objects.create(
                tenant=tenant,
                user_id='system',
                model_name=data_subject_type,
                field_name=field_name,
                record_id=data_subject_id,
                operation=f"lgpd_validation_{operation}",
                success=success,
                error_message=error_message or '',
                legal_basis=legal_basis
            )
        except Exception as e:
            logger.error(f"Failed to log LGPD validation: {str(e)}")


class LGPDReportGenerator:
    """
    Gerador de relatórios de conformidade LGPD.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
    
    def generate_compliance_report(self, start_date: datetime = None, 
                                 end_date: datetime = None) -> Dict[str, Any]:
        """
        Gera relatório completo de conformidade LGPD.
        
        Args:
            start_date: Data inicial do período (padrão: 30 dias atrás)
            end_date: Data final do período (padrão: hoje)
            
        Returns:
            Dict com o relatório de conformidade
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        report = {
            'tenant': {
                'id': str(self.tenant.id),
                'name': self.tenant.name,
                'subdomain': self.tenant.subdomain
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'generated_at': timezone.now().isoformat(),
            'data_processing': self._get_data_processing_stats(start_date, end_date),
            'consent_management': self._get_consent_stats(),
            'data_subjects': self._get_data_subjects_stats(),
            'compliance_score': self._calculate_compliance_score(),
            'recommendations': self._get_compliance_recommendations()
        }
        
        return report
    
    def _get_data_processing_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Estatísticas de processamento de dados"""
        logs = DataProcessingLog.objects.filter(
            tenant=self.tenant,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        total_operations = logs.count()
        successful_operations = logs.filter(success=True).count()
        failed_operations = logs.filter(success=False).count()
        
        # Operações por tipo
        operations_by_type = {}
        for log in logs.values('operation').annotate(count=models.Count('operation')):
            operations_by_type[log['operation']] = log['count']
        
        # Bases legais utilizadas
        legal_basis_usage = {}
        for log in logs.values('legal_basis').annotate(count=models.Count('legal_basis')):
            legal_basis_usage[log['legal_basis']] = log['count']
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'operations_by_type': operations_by_type,
            'legal_basis_usage': legal_basis_usage
        }
    
    def _get_consent_stats(self) -> Dict[str, Any]:
        """Estatísticas de consentimento"""
        consents = ConsentRecord.objects.filter(tenant=self.tenant)
        
        total_consents = consents.count()
        active_consents = consents.filter(consent_given=True, revoked_at__isnull=True).count()
        revoked_consents = consents.filter(revoked_at__isnull=False).count()
        
        # Consentimentos por tipo
        consents_by_type = {}
        for consent in consents.values('consent_type').annotate(count=models.Count('consent_type')):
            consents_by_type[consent['consent_type']] = consent['count']
        
        # Consentimentos por categoria de dados
        data_categories_usage = {}
        for consent in consents.filter(consent_given=True):
            for category in consent.data_categories:
                data_categories_usage[category] = data_categories_usage.get(category, 0) + 1
        
        return {
            'total_consents': total_consents,
            'active_consents': active_consents,
            'revoked_consents': revoked_consents,
            'consent_rate': (active_consents / total_consents * 100) if total_consents > 0 else 0,
            'consents_by_type': consents_by_type,
            'data_categories_usage': data_categories_usage
        }
    
    def _get_data_subjects_stats(self) -> Dict[str, Any]:
        """Estatísticas de titulares de dados"""
        from .encrypted_models import EncryptedClienteData, EncryptedAnimalData
        
        cliente_data_count = EncryptedClienteData.objects.filter(tenant=self.tenant).count()
        animal_data_count = EncryptedAnimalData.objects.filter(tenant=self.tenant).count()
        
        # Dados com consentimento
        cliente_with_consent = EncryptedClienteData.objects.filter(
            tenant=self.tenant,
            consent_given_at__isnull=False
        ).count()
        
        return {
            'total_cliente_records': cliente_data_count,
            'total_animal_records': animal_data_count,
            'cliente_with_consent': cliente_with_consent,
            'consent_coverage': (cliente_with_consent / cliente_data_count * 100) if cliente_data_count > 0 else 0
        }
    
    def _calculate_compliance_score(self) -> float:
        """Calcula score de conformidade LGPD (0-100)"""
        score = 100.0
        
        # Verificar cobertura de consentimento
        consent_stats = self._get_consent_stats()
        if consent_stats['consent_rate'] < 90:
            score -= (90 - consent_stats['consent_rate']) * 0.5
        
        # Verificar taxa de sucesso nas operações
        processing_stats = self._get_data_processing_stats(
            timezone.now() - timedelta(days=30),
            timezone.now()
        )
        if processing_stats['success_rate'] < 95:
            score -= (95 - processing_stats['success_rate']) * 0.3
        
        # Verificar se há dados sem consentimento
        data_subjects_stats = self._get_data_subjects_stats()
        if data_subjects_stats['consent_coverage'] < 100:
            score -= (100 - data_subjects_stats['consent_coverage']) * 0.2
        
        return max(0.0, score)
    
    def _get_compliance_recommendations(self) -> List[str]:
        """Gera recomendações para melhorar conformidade"""
        recommendations = []
        
        consent_stats = self._get_consent_stats()
        data_subjects_stats = self._get_data_subjects_stats()
        
        if consent_stats['consent_rate'] < 90:
            recommendations.append(
                "Implementar processo de coleta de consentimento para aumentar a taxa de consentimento"
            )
        
        if data_subjects_stats['consent_coverage'] < 100:
            recommendations.append(
                "Regularizar consentimento para todos os registros de dados pessoais"
            )
        
        if consent_stats['revoked_consents'] > 0:
            recommendations.append(
                "Revisar processos para reduzir revogações de consentimento"
            )
        
        # Verificar se há dados sensíveis sem consentimento específico
        from .encrypted_models import EncryptedAnimalData
        animal_data_without_consent = EncryptedAnimalData.objects.filter(
            tenant=self.tenant,
            consent_given_at__isnull=True
        ).count()
        
        if animal_data_without_consent > 0:
            recommendations.append(
                f"Obter consentimento específico para {animal_data_without_consent} registros de dados médicos sensíveis"
            )
        
        if not recommendations:
            recommendations.append("Parabéns! Seu tenant está em conformidade com a LGPD")
        
        return recommendations


class LGPDDataSubjectRights:
    """
    Implementa os direitos dos titulares de dados conforme LGPD.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
    
    def export_personal_data(self, data_subject_type: str, data_subject_id: str) -> Dict[str, Any]:
        """
        Exporta todos os dados pessoais de um titular (Art. 18, IV LGPD).
        
        Args:
            data_subject_type: Tipo do titular ('cliente', 'animal')
            data_subject_id: ID do titular
            
        Returns:
            Dict com todos os dados pessoais do titular
        """
        from .encrypted_models import EncryptedClienteData, EncryptedAnimalData
        
        exported_data = {
            'tenant': self.tenant.name,
            'data_subject_type': data_subject_type,
            'data_subject_id': data_subject_id,
            'exported_at': timezone.now().isoformat(),
            'data': {}
        }
        
        try:
            if data_subject_type == 'cliente':
                encrypted_data = EncryptedClienteData.objects.get(
                    tenant=self.tenant,
                    cliente_id=data_subject_id
                )
                exported_data['data'] = encrypted_data.decrypt_all_fields()
                
            elif data_subject_type == 'animal':
                encrypted_data = EncryptedAnimalData.objects.get(
                    tenant=self.tenant,
                    animal_id=data_subject_id
                )
                exported_data['data'] = encrypted_data.decrypt_all_fields()
            
            # Log da exportação
            DataProcessingLog.objects.create(
                tenant=self.tenant,
                user_id='data_subject',
                model_name=data_subject_type,
                field_name='all_personal_data',
                record_id=data_subject_id,
                operation='export',
                success=True,
                legal_basis='consent'
            )
            
        except Exception as e:
            logger.error(f"Failed to export personal data: {str(e)}")
            exported_data['error'] = str(e)
            
            # Log do erro
            DataProcessingLog.objects.create(
                tenant=self.tenant,
                user_id='data_subject',
                model_name=data_subject_type,
                field_name='all_personal_data',
                record_id=data_subject_id,
                operation='export',
                success=False,
                error_message=str(e),
                legal_basis='consent'
            )
        
        return exported_data
    
    def delete_personal_data(self, data_subject_type: str, data_subject_id: str, 
                           reason: str = 'data_subject_request') -> bool:
        """
        Exclui dados pessoais de um titular (Art. 18, VI LGPD).
        
        Args:
            data_subject_type: Tipo do titular ('cliente', 'animal')
            data_subject_id: ID do titular
            reason: Motivo da exclusão
            
        Returns:
            bool: True se a exclusão foi bem-sucedida
        """
        from .encrypted_models import EncryptedClienteData, EncryptedAnimalData
        
        try:
            if data_subject_type == 'cliente':
                EncryptedClienteData.objects.filter(
                    tenant=self.tenant,
                    cliente_id=data_subject_id
                ).delete()
                
            elif data_subject_type == 'animal':
                EncryptedAnimalData.objects.filter(
                    tenant=self.tenant,
                    animal_id=data_subject_id
                ).delete()
            
            # Revogar consentimentos relacionados
            ConsentRecord.objects.filter(
                tenant=self.tenant,
                data_subject_type=data_subject_type,
                data_subject_id=data_subject_id
            ).update(
                consent_given=False,
                revoked_at=timezone.now(),
                revoked_by='data_deletion'
            )
            
            # Log da exclusão
            DataProcessingLog.objects.create(
                tenant=self.tenant,
                user_id='data_subject',
                model_name=data_subject_type,
                field_name='all_personal_data',
                record_id=data_subject_id,
                operation='delete',
                success=True,
                legal_basis='consent'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete personal data: {str(e)}")
            
            # Log do erro
            DataProcessingLog.objects.create(
                tenant=self.tenant,
                user_id='data_subject',
                model_name=data_subject_type,
                field_name='all_personal_data',
                record_id=data_subject_id,
                operation='delete',
                success=False,
                error_message=str(e),
                legal_basis='consent'
            )
            
            return False
    
    def update_consent(self, data_subject_type: str, data_subject_id: str,
                      data_categories: List[str], processing_activities: List[str],
                      purpose: str, consent_given: bool = True) -> bool:
        """
        Atualiza consentimento de um titular de dados.
        
        Args:
            data_subject_type: Tipo do titular
            data_subject_id: ID do titular
            data_categories: Categorias de dados consentidas
            processing_activities: Atividades de processamento consentidas
            purpose: Finalidade do processamento
            consent_given: Se o consentimento foi dado ou revogado
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        try:
            consent, created = ConsentRecord.objects.get_or_create(
                tenant=self.tenant,
                data_subject_type=data_subject_type,
                data_subject_id=data_subject_id,
                purpose=purpose,
                defaults={
                    'data_categories': data_categories,
                    'processing_activities': processing_activities,
                    'consent_given': consent_given,
                    'consent_type': 'explicit',
                    'given_at': timezone.now() if consent_given else None,
                    'given_by': 'data_subject'
                }
            )
            
            if not created:
                consent.data_categories = data_categories
                consent.processing_activities = processing_activities
                consent.consent_given = consent_given
                
                if consent_given:
                    consent.given_at = timezone.now()
                    consent.revoked_at = None
                else:
                    consent.revoked_at = timezone.now()
                    consent.revoked_by = 'data_subject'
                
                consent.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update consent: {str(e)}")
            return False
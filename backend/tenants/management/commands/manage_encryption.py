"""
Comando de gerenciamento para operações de criptografia por tenant.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from tenants.models import Tenant
from tenants.encryption import encryption_manager, LGPDComplianceManager
from tenants.encrypted_models import EncryptedClienteData, EncryptedAnimalData, DataProcessingLog
from tenants.lgpd_compliance import LGPDValidator, LGPDReportGenerator
import logging

logger = logging.getLogger('tenants.encryption')


class Command(BaseCommand):
    help = 'Gerencia operações de criptografia para tenants'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            choices=['rotate_key', 'encrypt_existing', 'validate_encryption', 'audit_report', 'lgpd_report', 'validate_lgpd'],
            help='Operação a ser executada'
        )
        
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='ID do tenant específico (opcional)'
        )
        
        parser.add_argument(
            '--tenant-subdomain',
            type=str,
            help='Subdomínio do tenant específico (opcional)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a execução sem confirmação'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações (apenas simulação)'
        )
    
    def handle(self, *args, **options):
        operation = options['operation']
        tenant_id = options.get('tenant_id')
        tenant_subdomain = options.get('tenant_subdomain')
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        # Determinar tenant(s) alvo
        tenants = self.get_target_tenants(tenant_id, tenant_subdomain)
        
        if not tenants:
            raise CommandError("Nenhum tenant encontrado com os critérios especificados")
        
        # Executar operação
        if operation == 'rotate_key':
            self.rotate_tenant_keys(tenants, force, dry_run)
        elif operation == 'encrypt_existing':
            self.encrypt_existing_data(tenants, force, dry_run)
        elif operation == 'validate_encryption':
            self.validate_encryption(tenants)
        elif operation == 'audit_report':
            self.generate_audit_report(tenants)
        elif operation == 'lgpd_report':
            self.generate_lgpd_report(tenants)
        elif operation == 'validate_lgpd':
            self.validate_lgpd_compliance(tenants)
    
    def get_target_tenants(self, tenant_id, tenant_subdomain):
        """Obtém os tenants alvo baseado nos parâmetros"""
        if tenant_id:
            try:
                return [Tenant.objects.get(id=tenant_id)]
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant com ID {tenant_id} não encontrado")
        
        if tenant_subdomain:
            try:
                return [Tenant.objects.get(subdomain=tenant_subdomain)]
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant com subdomínio {tenant_subdomain} não encontrado")
        
        # Se nenhum critério específico, retorna todos os tenants ativos
        return Tenant.objects.filter(is_active=True)
    
    def rotate_tenant_keys(self, tenants, force, dry_run):
        """Rotaciona chaves de criptografia dos tenants"""
        self.stdout.write(
            self.style.WARNING(
                "ATENÇÃO: A rotação de chaves invalidará todos os dados criptografados existentes!"
            )
        )
        
        if not force:
            confirm = input("Tem certeza que deseja continuar? (digite 'sim' para confirmar): ")
            if confirm.lower() != 'sim':
                self.stdout.write("Operação cancelada.")
                return
        
        for tenant in tenants:
            self.stdout.write(f"Rotacionando chave para tenant: {tenant.name} ({tenant.id})")
            
            if dry_run:
                self.stdout.write(self.style.WARNING("  [DRY RUN] Chave seria rotacionada"))
                continue
            
            try:
                success = encryption_manager.rotate_tenant_key(str(tenant.id))
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Chave rotacionada com sucesso para {tenant.name}")
                    )
                    
                    # Log da rotação
                    logger.info(f"Key rotation completed for tenant {tenant.id}")
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Falha na rotação da chave para {tenant.name}")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Erro na rotação da chave para {tenant.name}: {str(e)}")
                )
    
    def encrypt_existing_data(self, tenants, force, dry_run):
        """Criptografa dados existentes que ainda não estão criptografados"""
        for tenant in tenants:
            self.stdout.write(f"Criptografando dados existentes para tenant: {tenant.name}")
            
            # Contar registros a serem processados
            cliente_count = EncryptedClienteData.objects.filter(tenant=tenant).count()
            animal_count = EncryptedAnimalData.objects.filter(tenant=tenant).count()
            
            self.stdout.write(f"  - {cliente_count} registros de clientes")
            self.stdout.write(f"  - {animal_count} registros de animais")
            
            if dry_run:
                self.stdout.write(self.style.WARNING("  [DRY RUN] Dados seriam criptografados"))
                continue
            
            try:
                with transaction.atomic():
                    # Processar dados de clientes
                    for encrypted_data in EncryptedClienteData.objects.filter(tenant=tenant):
                        self.encrypt_model_fields(encrypted_data)
                    
                    # Processar dados de animais
                    for encrypted_data in EncryptedAnimalData.objects.filter(tenant=tenant):
                        self.encrypt_model_fields(encrypted_data)
                
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Dados criptografados com sucesso para {tenant.name}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Erro na criptografia para {tenant.name}: {str(e)}")
                )
    
    def encrypt_model_fields(self, instance):
        """Criptografa campos de um modelo específico"""
        encrypted_fields = instance.get_encrypted_fields()
        
        for field_name in encrypted_fields:
            field_value = getattr(instance, field_name, None)
            if field_value:
                # Verificar se já está criptografado
                encrypted_field_name = f"{field_name}_encrypted"
                if not getattr(instance, encrypted_field_name, None):
                    instance.encrypt_field(field_name, field_value)
        
        instance.save()
    
    def validate_encryption(self, tenants):
        """Valida a integridade da criptografia"""
        total_errors = 0
        
        for tenant in tenants:
            self.stdout.write(f"Validando criptografia para tenant: {tenant.name}")
            tenant_errors = 0
            
            # Validar dados de clientes
            for encrypted_data in EncryptedClienteData.objects.filter(tenant=tenant):
                errors = self.validate_model_encryption(encrypted_data)
                tenant_errors += errors
            
            # Validar dados de animais
            for encrypted_data in EncryptedAnimalData.objects.filter(tenant=tenant):
                errors = self.validate_model_encryption(encrypted_data)
                tenant_errors += errors
            
            if tenant_errors == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Criptografia válida para {tenant.name}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {tenant_errors} erros encontrados para {tenant.name}")
                )
            
            total_errors += tenant_errors
        
        if total_errors == 0:
            self.stdout.write(self.style.SUCCESS("Validação concluída sem erros"))
        else:
            self.stdout.write(
                self.style.ERROR(f"Validação concluída com {total_errors} erros")
            )
    
    def validate_model_encryption(self, instance):
        """Valida a criptografia de um modelo específico"""
        errors = 0
        encrypted_fields = instance.get_encrypted_fields()
        
        for field_name in encrypted_fields:
            try:
                # Tentar descriptografar o campo
                decrypted_value = instance.decrypt_field(field_name)
                if decrypted_value is None:
                    encrypted_field_name = f"{field_name}_encrypted"
                    encrypted_value = getattr(instance, encrypted_field_name, None)
                    if encrypted_value:  # Há dados criptografados mas falha na descriptografia
                        self.stdout.write(
                            self.style.ERROR(
                                f"    ✗ Falha na descriptografia: {instance.__class__.__name__} "
                                f"ID {instance.id} campo {field_name}"
                            )
                        )
                        errors += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"    ✗ Erro na validação: {instance.__class__.__name__} "
                        f"ID {instance.id} campo {field_name}: {str(e)}"
                    )
                )
                errors += 1
        
        return errors
    
    def generate_audit_report(self, tenants):
        """Gera relatório de auditoria LGPD"""
        self.stdout.write(self.style.SUCCESS("=== RELATÓRIO DE AUDITORIA LGPD ==="))
        
        for tenant in tenants:
            self.stdout.write(f"\nTenant: {tenant.name} ({tenant.subdomain})")
            self.stdout.write("-" * 50)
            
            # Estatísticas de dados criptografados
            cliente_data_count = EncryptedClienteData.objects.filter(tenant=tenant).count()
            animal_data_count = EncryptedAnimalData.objects.filter(tenant=tenant).count()
            
            self.stdout.write(f"Registros de dados criptografados:")
            self.stdout.write(f"  - Clientes: {cliente_data_count}")
            self.stdout.write(f"  - Animais: {animal_data_count}")
            
            # Logs de processamento (últimos 30 dias)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            recent_logs = DataProcessingLog.objects.filter(
                tenant=tenant,
                timestamp__gte=thirty_days_ago
            )
            
            self.stdout.write(f"\nAtividade de processamento (últimos 30 dias):")
            self.stdout.write(f"  - Total de operações: {recent_logs.count()}")
            
            # Operações por tipo
            operations = recent_logs.values('operation').annotate(
                count=models.Count('operation')
            ).order_by('-count')
            
            for op in operations:
                self.stdout.write(f"  - {op['operation']}: {op['count']}")
            
            # Erros recentes
            error_logs = recent_logs.filter(success=False)
            if error_logs.exists():
                self.stdout.write(f"\n⚠️  Erros recentes: {error_logs.count()}")
                for error in error_logs[:5]:  # Mostrar apenas os 5 mais recentes
                    self.stdout.write(
                        f"    - {error.timestamp}: {error.operation} em "
                        f"{error.model_name}.{error.field_name} - {error.error_message}"
                    )
            
            # Conformidade LGPD
            self.stdout.write(f"\nConformidade LGPD:")
            
            # Verificar se há dados sem consentimento
            cliente_data_without_consent = EncryptedClienteData.objects.filter(
                tenant=tenant,
                consent_given_at__isnull=True
            ).count()
            
            if cliente_data_without_consent > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  {cliente_data_without_consent} registros de clientes sem consentimento registrado"
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ Todos os registros possuem consentimento"))
        
        self.stdout.write(self.style.SUCCESS("\n=== FIM DO RELATÓRIO ==="))    

    def generate_lgpd_report(self, tenants):
        """Gera relatório completo de conformidade LGPD"""
        self.stdout.write(self.style.SUCCESS("=== RELATÓRIO DE CONFORMIDADE LGPD ==="))
        
        for tenant in tenants:
            self.stdout.write(f"\nTenant: {tenant.name} ({tenant.subdomain})")
            self.stdout.write("=" * 60)
            
            # Gerar relatório usando LGPDReportGenerator
            report_generator = LGPDReportGenerator(tenant)
            report = report_generator.generate_compliance_report()
            
            # Exibir informações do período
            self.stdout.write(f"Período: {report['period']['start_date'][:10]} a {report['period']['end_date'][:10]}")
            
            # Score de conformidade
            score = report['compliance_score']
            if score >= 90:
                score_style = self.style.SUCCESS
                score_icon = "✓"
            elif score >= 70:
                score_style = self.style.WARNING
                score_icon = "⚠️"
            else:
                score_style = self.style.ERROR
                score_icon = "✗"
            
            self.stdout.write(f"Score de Conformidade: {score_style(f'{score_icon} {score:.1f}/100')}")
            
            # Estatísticas de processamento de dados
            processing = report['data_processing']
            self.stdout.write(f"\nProcessamento de Dados:")
            self.stdout.write(f"  - Total de operações: {processing['total_operations']}")
            self.stdout.write(f"  - Taxa de sucesso: {processing['success_rate']:.1f}%")
            self.stdout.write(f"  - Operações falharam: {processing['failed_operations']}")
            
            if processing['operations_by_type']:
                self.stdout.write(f"  - Operações por tipo:")
                for op_type, count in processing['operations_by_type'].items():
                    self.stdout.write(f"    • {op_type}: {count}")
            
            # Estatísticas de consentimento
            consent = report['consent_management']
            self.stdout.write(f"\nGerenciamento de Consentimento:")
            self.stdout.write(f"  - Total de consentimentos: {consent['total_consents']}")
            self.stdout.write(f"  - Consentimentos ativos: {consent['active_consents']}")
            self.stdout.write(f"  - Taxa de consentimento: {consent['consent_rate']:.1f}%")
            self.stdout.write(f"  - Consentimentos revogados: {consent['revoked_consents']}")
            
            if consent['consents_by_type']:
                self.stdout.write(f"  - Consentimentos por tipo:")
                for consent_type, count in consent['consents_by_type'].items():
                    self.stdout.write(f"    • {consent_type}: {count}")
            
            # Estatísticas de titulares de dados
            subjects = report['data_subjects']
            self.stdout.write(f"\nTitulares de Dados:")
            self.stdout.write(f"  - Registros de clientes: {subjects['total_cliente_records']}")
            self.stdout.write(f"  - Registros de animais: {subjects['total_animal_records']}")
            self.stdout.write(f"  - Clientes com consentimento: {subjects['cliente_with_consent']}")
            self.stdout.write(f"  - Cobertura de consentimento: {subjects['consent_coverage']:.1f}%")
            
            # Recomendações
            recommendations = report['recommendations']
            if recommendations:
                self.stdout.write(f"\nRecomendações:")
                for i, recommendation in enumerate(recommendations, 1):
                    self.stdout.write(f"  {i}. {recommendation}")
        
        self.stdout.write(self.style.SUCCESS("\n=== FIM DO RELATÓRIO LGPD ==="))
    
    def validate_lgpd_compliance(self, tenants):
        """Valida conformidade LGPD para os tenants"""
        self.stdout.write(self.style.SUCCESS("=== VALIDAÇÃO DE CONFORMIDADE LGPD ==="))
        
        total_issues = 0
        
        for tenant in tenants:
            self.stdout.write(f"\nValidando tenant: {tenant.name}")
            self.stdout.write("-" * 40)
            
            tenant_issues = 0
            
            # 1. Verificar dados pessoais sem consentimento
            cliente_without_consent = EncryptedClienteData.objects.filter(
                tenant=tenant,
                consent_given_at__isnull=True
            ).count()
            
            if cliente_without_consent > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {cliente_without_consent} registros de clientes sem consentimento"
                    )
                )
                tenant_issues += cliente_without_consent
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ Todos os clientes possuem consentimento"))
            
            # 2. Verificar dados médicos sensíveis sem consentimento
            animal_without_consent = EncryptedAnimalData.objects.filter(
                tenant=tenant,
                consent_given_at__isnull=True
            ).count()
            
            if animal_without_consent > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {animal_without_consent} registros de dados médicos sem consentimento"
                    )
                )
                tenant_issues += animal_without_consent
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ Todos os dados médicos possuem consentimento"))
            
            # 3. Verificar consentimentos expirados ou inválidos
            from tenants.encrypted_models import ConsentRecord
            from django.utils import timezone
            from datetime import timedelta
            
            # Considerar consentimentos com mais de 2 anos como expirados
            two_years_ago = timezone.now() - timedelta(days=730)
            expired_consents = ConsentRecord.objects.filter(
                tenant=tenant,
                consent_given=True,
                given_at__lt=two_years_ago
            ).count()
            
            if expired_consents > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  {expired_consents} consentimentos podem estar expirados (>2 anos)"
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ Nenhum consentimento expirado encontrado"))
            
            # 4. Verificar logs de processamento com falhas
            recent_failed_logs = DataProcessingLog.objects.filter(
                tenant=tenant,
                success=False,
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            if recent_failed_logs > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  {recent_failed_logs} falhas no processamento de dados (últimos 7 dias)"
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ Nenhuma falha recente no processamento"))
            
            # 5. Verificar se há dados criptografados órfãos
            orphaned_cliente_data = 0
            orphaned_animal_data = 0
            
            # Verificar dados de clientes órfãos (sem referência no modelo principal)
            from api.models import Cliente
            for encrypted_data in EncryptedClienteData.objects.filter(tenant=tenant):
                try:
                    Cliente.objects.get(id=encrypted_data.cliente_id, tenant=tenant)
                except Cliente.DoesNotExist:
                    orphaned_cliente_data += 1
            
            # Verificar dados de animais órfãos
            from api.models import Animal
            for encrypted_data in EncryptedAnimalData.objects.filter(tenant=tenant):
                try:
                    Animal.objects.get(id=encrypted_data.animal_id, tenant=tenant)
                except Animal.DoesNotExist:
                    orphaned_animal_data += 1
            
            if orphaned_cliente_data > 0 or orphaned_animal_data > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Dados órfãos encontrados: {orphaned_cliente_data} clientes, "
                        f"{orphaned_animal_data} animais"
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ Nenhum dado órfão encontrado"))
            
            # Resumo do tenant
            if tenant_issues == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Tenant {tenant.name} está em conformidade com LGPD")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Tenant {tenant.name} possui {tenant_issues} problemas de conformidade")
                )
            
            total_issues += tenant_issues
        
        # Resumo geral
        self.stdout.write(f"\n{'='*60}")
        if total_issues == 0:
            self.stdout.write(
                self.style.SUCCESS("🎉 TODOS OS TENANTS ESTÃO EM CONFORMIDADE COM LGPD!")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"⚠️  TOTAL DE PROBLEMAS ENCONTRADOS: {total_issues}")
            )
            self.stdout.write(
                "Recomendação: Execute 'manage_encryption lgpd_report' para obter "
                "recomendações detalhadas de correção."
            )
        
        self.stdout.write(self.style.SUCCESS("=== FIM DA VALIDAÇÃO LGPD ==="))
"""
Testes para o sistema de conformidade LGPD.
"""

import os
import django
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.encrypted_models import EncryptedClienteData, EncryptedAnimalData, ConsentRecord
from tenants.lgpd_compliance import LGPDValidator, LGPDReportGenerator, LGPDDataSubjectRights
from tenants.utils import set_current_tenant


class LGPDComplianceTest(TestCase):
    """Testes para conformidade LGPD"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Limpar dados existentes
        Tenant.objects.filter(subdomain="lgpd-teste").delete()
        
        self.tenant = Tenant.objects.create(
            name="Petshop LGPD Teste",
            subdomain="lgpd-teste",
            schema_name="tenant_lgpd_teste"
        )
        
        set_current_tenant(self.tenant)
    
    def test_lgpd_validator_personal_data_detection(self):
        """Testa detecção de dados pessoais"""
        # Dados pessoais
        self.assertTrue(LGPDValidator.is_personal_data('email'))
        self.assertTrue(LGPDValidator.is_personal_data('cpf'))
        self.assertTrue(LGPDValidator.is_personal_data('telefone'))
        self.assertTrue(LGPDValidator.is_personal_data('endereco'))
        
        # Dados não pessoais
        self.assertFalse(LGPDValidator.is_personal_data('nome_produto'))
        self.assertFalse(LGPDValidator.is_personal_data('preco'))
        self.assertFalse(LGPDValidator.is_personal_data('categoria'))
        
        print("✓ Teste de detecção de dados pessoais passou")
    
    def test_lgpd_validator_sensitive_data_detection(self):
        """Testa detecção de dados sensíveis"""
        # Dados sensíveis
        self.assertTrue(LGPDValidator.is_sensitive_data('historico_medico'))
        self.assertTrue(LGPDValidator.is_sensitive_data('observacoes_medicas'))
        self.assertTrue(LGPDValidator.is_sensitive_data('medicamentos'))
        self.assertTrue(LGPDValidator.is_sensitive_data('alergias'))
        
        # Dados não sensíveis
        self.assertFalse(LGPDValidator.is_sensitive_data('nome'))
        self.assertFalse(LGPDValidator.is_sensitive_data('email'))
        self.assertFalse(LGPDValidator.is_sensitive_data('telefone'))
        
        print("✓ Teste de detecção de dados sensíveis passou")
    
    def test_consent_management(self):
        """Testa gerenciamento de consentimento"""
        # Criar registro de consentimento
        consent = ConsentRecord.objects.create(
            tenant=self.tenant,
            data_subject_type='cliente',
            data_subject_id='1',
            purpose='Prestação de serviços veterinários',
            data_categories=['nome', 'email', 'telefone', 'historico_medico'],
            processing_activities=['armazenamento', 'consulta', 'atualizacao'],
            consent_given=True,
            consent_type='explicit',
            given_at=timezone.now(),
            given_by='cliente'
        )
        
        # Verificar consentimento
        self.assertTrue(
            LGPDValidator.has_valid_consent(
                self.tenant, 'cliente', '1', 'historico_medico'
            )
        )
        
        # Revogar consentimento
        consent.revoke_consent('cliente')
        self.assertFalse(consent.consent_given)
        self.assertIsNotNone(consent.revoked_at)
        
        # Verificar que consentimento foi revogado
        self.assertFalse(
            LGPDValidator.has_valid_consent(
                self.tenant, 'cliente', '1', 'historico_medico'
            )
        )
        
        print("✓ Teste de gerenciamento de consentimento passou")
    
    def test_data_processing_validation(self):
        """Testa validação de processamento de dados"""
        # Criar consentimento para dados sensíveis
        ConsentRecord.objects.create(
            tenant=self.tenant,
            data_subject_type='animal',
            data_subject_id='1',
            purpose='Tratamento médico veterinário',
            data_categories=['historico_medico', 'medicamentos', 'alergias'],
            processing_activities=['armazenamento', 'consulta'],
            consent_given=True,
            consent_type='explicit',
            given_at=timezone.now(),
            given_by='proprietario'
        )
        
        # Validar processamento com consentimento
        self.assertTrue(
            LGPDValidator.validate_data_processing(
                self.tenant, 'animal', '1', 'historico_medico', 'read', 'consent'
            )
        )
        
        # Validar processamento sem consentimento (deve falhar)
        self.assertFalse(
            LGPDValidator.validate_data_processing(
                self.tenant, 'animal', '2', 'historico_medico', 'read', 'consent'
            )
        )
        
        # Validar dados não sensíveis (deve passar)
        self.assertTrue(
            LGPDValidator.validate_data_processing(
                self.tenant, 'cliente', '1', 'nome', 'read', 'contract'
            )
        )
        
        print("✓ Teste de validação de processamento passou")
    
    def test_lgpd_report_generator(self):
        """Testa geração de relatórios LGPD"""
        # Criar alguns dados de teste
        ConsentRecord.objects.create(
            tenant=self.tenant,
            data_subject_type='cliente',
            data_subject_id='1',
            purpose='Prestação de serviços',
            data_categories=['nome', 'email'],
            processing_activities=['armazenamento'],
            consent_given=True,
            consent_type='explicit',
            given_at=timezone.now()
        )
        
        # Gerar relatório
        report_generator = LGPDReportGenerator(self.tenant)
        report = report_generator.generate_compliance_report()
        
        # Verificar estrutura do relatório
        self.assertIn('tenant', report)
        self.assertIn('period', report)
        self.assertIn('data_processing', report)
        self.assertIn('consent_management', report)
        self.assertIn('compliance_score', report)
        self.assertIn('recommendations', report)
        
        # Verificar dados do tenant
        self.assertEqual(report['tenant']['name'], self.tenant.name)
        self.assertEqual(report['tenant']['subdomain'], self.tenant.subdomain)
        
        # Verificar score de conformidade
        self.assertIsInstance(report['compliance_score'], float)
        self.assertGreaterEqual(report['compliance_score'], 0)
        self.assertLessEqual(report['compliance_score'], 100)
        
        print("✓ Teste de geração de relatórios passou")
    
    def test_data_subject_rights_export(self):
        """Testa exportação de dados pessoais (direito do titular)"""
        # Criar dados criptografados de cliente
        encrypted_cliente = EncryptedClienteData.objects.create(
            tenant=self.tenant,
            cliente_id=1,
            consent_given_at=timezone.now(),
            consent_given_by="cliente",
            consent_type="explicit"
        )
        
        # Definir dados sensíveis
        encrypted_cliente.cpf = "123.456.789-00"
        encrypted_cliente.rg = "12.345.678-9"
        encrypted_cliente.endereco_completo = "Rua Teste, 123"
        encrypted_cliente.save()
        
        # Exportar dados
        rights_manager = LGPDDataSubjectRights(self.tenant)
        exported_data = rights_manager.export_personal_data('cliente', '1')
        
        # Verificar exportação
        self.assertIn('data', exported_data)
        self.assertIn('tenant', exported_data)
        self.assertEqual(exported_data['data_subject_type'], 'cliente')
        self.assertEqual(exported_data['data_subject_id'], '1')
        
        # Verificar se os dados foram descriptografados
        if 'cpf' in exported_data['data']:
            self.assertEqual(exported_data['data']['cpf'], "123.456.789-00")
        
        print("✓ Teste de exportação de dados passou")
    
    def test_data_subject_rights_deletion(self):
        """Testa exclusão de dados pessoais (direito ao esquecimento)"""
        # Criar dados criptografados
        encrypted_cliente = EncryptedClienteData.objects.create(
            tenant=self.tenant,
            cliente_id=2,
            consent_given_at=timezone.now()
        )
        encrypted_cliente.cpf = "987.654.321-00"
        encrypted_cliente.save()
        
        # Criar consentimento
        ConsentRecord.objects.create(
            tenant=self.tenant,
            data_subject_type='cliente',
            data_subject_id='2',
            purpose='Teste',
            consent_given=True
        )
        
        # Verificar que os dados existem
        self.assertTrue(
            EncryptedClienteData.objects.filter(
                tenant=self.tenant, cliente_id=2
            ).exists()
        )
        self.assertTrue(
            ConsentRecord.objects.filter(
                tenant=self.tenant, data_subject_id='2', consent_given=True
            ).exists()
        )
        
        # Excluir dados
        rights_manager = LGPDDataSubjectRights(self.tenant)
        success = rights_manager.delete_personal_data('cliente', '2')
        
        self.assertTrue(success)
        
        # Verificar que os dados foram excluídos
        self.assertFalse(
            EncryptedClienteData.objects.filter(
                tenant=self.tenant, cliente_id=2
            ).exists()
        )
        
        # Verificar que o consentimento foi revogado
        consent = ConsentRecord.objects.get(
            tenant=self.tenant, data_subject_id='2'
        )
        self.assertFalse(consent.consent_given)
        self.assertIsNotNone(consent.revoked_at)
        
        print("✓ Teste de exclusão de dados passou")
    
    def test_consent_update(self):
        """Testa atualização de consentimento"""
        rights_manager = LGPDDataSubjectRights(self.tenant)
        
        # Criar consentimento inicial
        success = rights_manager.update_consent(
            data_subject_type='cliente',
            data_subject_id='3',
            data_categories=['nome', 'email'],
            processing_activities=['armazenamento'],
            purpose='Prestação de serviços',
            consent_given=True
        )
        
        self.assertTrue(success)
        
        # Verificar consentimento criado
        consent = ConsentRecord.objects.get(
            tenant=self.tenant,
            data_subject_type='cliente',
            data_subject_id='3'
        )
        
        self.assertTrue(consent.consent_given)
        self.assertEqual(consent.data_categories, ['nome', 'email'])
        
        # Atualizar consentimento (adicionar mais categorias)
        success = rights_manager.update_consent(
            data_subject_type='cliente',
            data_subject_id='3',
            data_categories=['nome', 'email', 'telefone'],
            processing_activities=['armazenamento', 'consulta'],
            purpose='Prestação de serviços',
            consent_given=True
        )
        
        self.assertTrue(success)
        
        # Verificar atualização
        consent.refresh_from_db()
        self.assertEqual(consent.data_categories, ['nome', 'email', 'telefone'])
        self.assertEqual(consent.processing_activities, ['armazenamento', 'consulta'])
        
        # Revogar consentimento
        success = rights_manager.update_consent(
            data_subject_type='cliente',
            data_subject_id='3',
            data_categories=[],
            processing_activities=[],
            purpose='Prestação de serviços',
            consent_given=False
        )
        
        self.assertTrue(success)
        
        # Verificar revogação
        consent.refresh_from_db()
        self.assertFalse(consent.consent_given)
        self.assertIsNotNone(consent.revoked_at)
        
        print("✓ Teste de atualização de consentimento passou")


def run_tests():
    """Executa todos os testes"""
    print("=== EXECUTANDO TESTES DE CONFORMIDADE LGPD ===\n")
    
    test = LGPDComplianceTest()
    test.setUp()
    
    try:
        test.test_lgpd_validator_personal_data_detection()
        test.test_lgpd_validator_sensitive_data_detection()
        test.test_consent_management()
        test.test_data_processing_validation()
        test.test_lgpd_report_generator()
        test.test_data_subject_rights_export()
        test.test_data_subject_rights_deletion()
        test.test_consent_update()
        
        print("\n=== TODOS OS TESTES DE LGPD PASSARAM COM SUCESSO! ===")
        return True
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE LGPD: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_tests()
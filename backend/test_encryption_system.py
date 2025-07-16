"""
Testes para o sistema de criptografia multitenant.
"""

import os
import django
from django.test import TestCase
from django.core.exceptions import ValidationError

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from tenants.models import Tenant
from tenants.encrypted_models import EncryptedClienteData, EncryptedAnimalData, ConsentRecord
from tenants.encryption import encryption_manager, LGPDComplianceManager
from tenants.utils import set_current_tenant


class EncryptionSystemTest(TestCase):
    """Testes para o sistema de criptografia"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Limpar dados existentes
        Tenant.objects.filter(subdomain="teste").delete()
        
        self.tenant = Tenant.objects.create(
            name="Petshop Teste",
            subdomain="teste",
            schema_name="tenant_teste"
        )
    
    def test_tenant_encryption_manager(self):
        """Testa o gerenciador de criptografia por tenant"""
        # Dados de teste
        original_data = "Dados sensíveis do cliente"
        tenant_id = str(self.tenant.id)
        
        # Criptografar
        encrypted_data = encryption_manager.encrypt(original_data, tenant_id)
        self.assertIsNotNone(encrypted_data)
        self.assertNotEqual(encrypted_data, original_data)
        
        # Descriptografar
        decrypted_data = encryption_manager.decrypt(encrypted_data, tenant_id)
        self.assertEqual(decrypted_data, original_data)
        
        print("✓ Teste de criptografia/descriptografia básica passou")
    
    def test_encrypted_cliente_data(self):
        """Testa o modelo de dados criptografados de cliente"""
        # Definir contexto do tenant
        set_current_tenant(self.tenant)
        
        # Criar dados criptografados
        encrypted_cliente = EncryptedClienteData.objects.create(
            tenant=self.tenant,
            cliente_id=1,
            consent_given_at=django.utils.timezone.now(),
            consent_given_by="admin",
            consent_type="explicit"
        )
        
        # Definir dados sensíveis
        encrypted_cliente.cpf = "123.456.789-00"
        encrypted_cliente.rg = "12.345.678-9"
        encrypted_cliente.endereco_completo = "Rua Teste, 123 - Bairro Teste"
        encrypted_cliente.observacoes_pessoais = "Cliente VIP"
        encrypted_cliente.dados_bancarios = "Banco: 001, Agência: 1234, Conta: 56789"
        
        encrypted_cliente.save()
        
        # Verificar se os dados foram criptografados
        self.assertIsNotNone(encrypted_cliente.cpf_encrypted)
        self.assertIsNotNone(encrypted_cliente.rg_encrypted)
        self.assertIsNotNone(encrypted_cliente.endereco_completo_encrypted)
        
        # Verificar se os dados podem ser descriptografados
        self.assertEqual(encrypted_cliente.cpf, "123.456.789-00")
        self.assertEqual(encrypted_cliente.rg, "12.345.678-9")
        self.assertEqual(encrypted_cliente.endereco_completo, "Rua Teste, 123 - Bairro Teste")
        
        print("✓ Teste de modelo de dados criptografados de cliente passou")
    
    def test_encrypted_animal_data(self):
        """Testa o modelo de dados criptografados de animal"""
        # Definir contexto do tenant
        set_current_tenant(self.tenant)
        
        # Criar dados criptografados
        encrypted_animal = EncryptedAnimalData.objects.create(
            tenant=self.tenant,
            animal_id=1,
            consent_given_at=django.utils.timezone.now(),
            consent_given_by="veterinario",
            veterinario_responsavel="Dr. João"
        )
        
        # Definir dados médicos sensíveis
        encrypted_animal.historico_medico = "Histórico médico completo do animal"
        encrypted_animal.observacoes_veterinario = "Animal com alergia a ração X"
        encrypted_animal.medicamentos_atuais = "Medicamento A - 2x ao dia"
        encrypted_animal.alergias = "Alergia a frango"
        encrypted_animal.condicoes_especiais = "Diabetes controlada"
        
        encrypted_animal.save()
        
        # Verificar se os dados foram criptografados
        self.assertIsNotNone(encrypted_animal.historico_medico_encrypted)
        self.assertIsNotNone(encrypted_animal.observacoes_veterinario_encrypted)
        
        # Verificar se os dados podem ser descriptografados
        self.assertEqual(encrypted_animal.historico_medico, "Histórico médico completo do animal")
        self.assertEqual(encrypted_animal.observacoes_veterinario, "Animal com alergia a ração X")
        
        print("✓ Teste de modelo de dados criptografados de animal passou")
    
    def test_lgpd_compliance(self):
        """Testa funcionalidades de conformidade LGPD"""
        # Testar identificação de campos sensíveis
        self.assertTrue(LGPDComplianceManager.is_sensitive_field('email'))
        self.assertTrue(LGPDComplianceManager.is_sensitive_field('telefone'))
        self.assertTrue(LGPDComplianceManager.is_sensitive_field('endereco'))
        self.assertFalse(LGPDComplianceManager.is_sensitive_field('nome'))
        
        # Testar campos que requerem consentimento explícito
        self.assertTrue(LGPDComplianceManager.requires_explicit_consent('observacoes_medicas'))
        self.assertTrue(LGPDComplianceManager.requires_explicit_consent('dados_bancarios'))
        self.assertFalse(LGPDComplianceManager.requires_explicit_consent('email'))
        
        print("✓ Teste de conformidade LGPD passou")
    
    def test_consent_record(self):
        """Testa o sistema de registro de consentimento"""
        # Definir contexto do tenant
        set_current_tenant(self.tenant)
        
        # Criar registro de consentimento
        consent = ConsentRecord.objects.create(
            tenant=self.tenant,
            data_subject_type='cliente',
            data_subject_id='1',
            purpose='Processamento de dados para prestação de serviços veterinários',
            data_categories=['nome', 'email', 'telefone', 'endereco'],
            processing_activities=['armazenamento', 'consulta', 'atualizacao'],
            consent_given=True,
            consent_type='explicit',
            given_at=django.utils.timezone.now(),
            given_by='cliente'
        )
        
        self.assertTrue(consent.consent_given)
        self.assertEqual(consent.consent_type, 'explicit')
        
        # Testar revogação de consentimento
        consent.revoke_consent('cliente')
        self.assertFalse(consent.consent_given)
        self.assertIsNotNone(consent.revoked_at)
        
        print("✓ Teste de registro de consentimento passou")
    
    def test_tenant_isolation(self):
        """Testa o isolamento de dados entre tenants"""
        # Limpar dados existentes
        Tenant.objects.filter(subdomain="teste2").delete()
        EncryptedClienteData.objects.filter(cliente_id__in=[10, 11]).delete()
        
        # Criar segundo tenant
        tenant2 = Tenant.objects.create(
            name="Petshop Teste 2",
            subdomain="teste2",
            schema_name="tenant_teste2"
        )
        
        # Criar dados para o primeiro tenant
        set_current_tenant(self.tenant)
        data1 = EncryptedClienteData.objects.create(
            tenant=self.tenant,
            cliente_id=10,
            consent_given_at=django.utils.timezone.now()
        )
        data1.cpf = "111.111.111-11"
        data1.save()
        
        # Criar dados para o segundo tenant
        set_current_tenant(tenant2)
        data2 = EncryptedClienteData.objects.create(
            tenant=tenant2,
            cliente_id=11,
            consent_given_at=django.utils.timezone.now()
        )
        data2.cpf = "222.222.222-22"
        data2.save()
        
        # Limpar contexto para consulta global
        set_current_tenant(None)
        
        # Verificar isolamento usando o manager base (sem filtro de tenant)
        from django.db import models
        tenant1_data = EncryptedClienteData._base_manager.filter(tenant=self.tenant)
        tenant2_data = EncryptedClienteData._base_manager.filter(tenant=tenant2)
        
        self.assertEqual(tenant1_data.count(), 1)
        self.assertEqual(tenant2_data.count(), 1)
        
        # Definir contexto para descriptografar
        set_current_tenant(self.tenant)
        data1_obj = tenant1_data.first()
        self.assertEqual(data1_obj.cpf, "111.111.111-11")
        
        set_current_tenant(tenant2)
        data2_obj = tenant2_data.first()
        self.assertEqual(data2_obj.cpf, "222.222.222-22")
        
        print("✓ Teste de isolamento entre tenants passou")
    
    def test_encryption_with_different_tenants(self):
        """Testa se a criptografia é diferente para tenants diferentes"""
        # Limpar dados existentes
        Tenant.objects.filter(subdomain="teste3").delete()
        
        # Criar segundo tenant
        tenant2 = Tenant.objects.create(
            name="Petshop Teste 3",
            subdomain="teste3",
            schema_name="tenant_teste3"
        )
        
        # Mesmo dado, tenants diferentes
        same_data = "Dados sensíveis"
        
        encrypted1 = encryption_manager.encrypt(same_data, str(self.tenant.id))
        encrypted2 = encryption_manager.encrypt(same_data, str(tenant2.id))
        
        # Dados criptografados devem ser diferentes
        self.assertNotEqual(encrypted1, encrypted2)
        
        # Mas quando descriptografados com a chave correta, devem ser iguais
        decrypted1 = encryption_manager.decrypt(encrypted1, str(self.tenant.id))
        decrypted2 = encryption_manager.decrypt(encrypted2, str(tenant2.id))
        
        self.assertEqual(decrypted1, same_data)
        self.assertEqual(decrypted2, same_data)
        self.assertEqual(decrypted1, decrypted2)
        
        print("✓ Teste de criptografia diferente por tenant passou")


def run_tests():
    """Executa todos os testes"""
    print("=== EXECUTANDO TESTES DO SISTEMA DE CRIPTOGRAFIA ===\n")
    
    test = EncryptionSystemTest()
    test.setUp()
    
    try:
        test.test_tenant_encryption_manager()
        test.test_encrypted_cliente_data()
        test.test_encrypted_animal_data()
        test.test_lgpd_compliance()
        test.test_consent_record()
        test.test_tenant_isolation()
        test.test_encryption_with_different_tenants()
        
        print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")
        return True
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_tests()
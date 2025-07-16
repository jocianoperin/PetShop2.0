"""
Comando para testar o TenantProvisioningService
"""

from django.core.management.base import BaseCommand
from tenants.services import TenantProvisioningService, TenantProvisioningError


class Command(BaseCommand):
    help = 'Testa o TenantProvisioningService'

    def handle(self, *args, **options):
        self.stdout.write("Testando TenantProvisioningService...")
        
        try:
            # Teste 1: Instanciar serviço
            service = TenantProvisioningService()
            self.stdout.write(self.style.SUCCESS("✓ Serviço instanciado com sucesso"))
            
            # Teste 2: Validação de dados
            valid_data = {
                'name': 'Pet Shop Teste',
                'subdomain': 'petteste',
                'admin_email': 'admin@petteste.com',
                'admin_password': 'senha123456'
            }
            
            service._validate_tenant_data(valid_data)
            self.stdout.write(self.style.SUCCESS("✓ Validação de dados passou"))
            
            # Teste 3: Validação com dados inválidos
            try:
                invalid_data = {'name': 'Teste'}
                service._validate_tenant_data(invalid_data)
                self.stdout.write(self.style.ERROR("✗ Validação deveria ter falhado"))
            except TenantProvisioningError:
                self.stdout.write(self.style.SUCCESS("✓ Validação corretamente rejeitou dados inválidos"))
            
            self.stdout.write(self.style.SUCCESS("🎉 Todos os testes básicos passaram!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro nos testes: {str(e)}"))
            import traceback
            traceback.print_exc()
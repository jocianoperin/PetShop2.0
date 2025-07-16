"""
Comando Django para provisionamento automático de tenants.
Utiliza o TenantProvisioningService para criar tenants completos.
"""

from django.core.management.base import BaseCommand, CommandError
from tenants.services import tenant_provisioning_service, TenantProvisioningError
import json


class Command(BaseCommand):
    """
    Comando para provisionamento automático de tenants.
    
    Usage:
        python manage.py provision_tenant --name "Pet Shop ABC" --subdomain "petabc" --admin-email "admin@petabc.com" --admin-password "senha123"
        python manage.py provision_tenant --json-file tenant_data.json
        python manage.py provision_tenant --validate-tenant <tenant_id_or_subdomain>
    """
    
    help = 'Provisiona um novo tenant com configuração completa'

    def add_arguments(self, parser):
        # Argumentos individuais
        parser.add_argument(
            '--name',
            type=str,
            help='Nome do petshop'
        )
        parser.add_argument(
            '--subdomain',
            type=str,
            help='Subdomínio desejado'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            help='Email do administrador'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            help='Senha do administrador'
        )
        parser.add_argument(
            '--admin-first-name',
            type=str,
            help='Primeiro nome do administrador (opcional)'
        )
        parser.add_argument(
            '--admin-last-name',
            type=str,
            help='Último nome do administrador (opcional)'
        )
        parser.add_argument(
            '--plan-type',
            type=str,
            choices=['basic', 'premium', 'enterprise'],
            default='basic',
            help='Tipo do plano (padrão: basic)'
        )
        parser.add_argument(
            '--max-users',
            type=int,
            default=10,
            help='Máximo de usuários (padrão: 10)'
        )
        parser.add_argument(
            '--max-animals',
            type=int,
            default=1000,
            help='Máximo de animais (padrão: 1000)'
        )
        
        # Arquivo JSON
        parser.add_argument(
            '--json-file',
            type=str,
            help='Arquivo JSON com dados do tenant'
        )
        
        # Validação
        parser.add_argument(
            '--validate-tenant',
            type=str,
            help='Valida provisionamento de tenant existente (ID ou subdomínio)'
        )
        
        # Status
        parser.add_argument(
            '--status',
            type=str,
            help='Obtém status de provisionamento de tenant (ID ou subdomínio)'
        )

    def handle(self, *args, **options):
        if options['validate_tenant']:
            self.validate_tenant(options['validate_tenant'])
        elif options['status']:
            self.show_tenant_status(options['status'])
        elif options['json_file']:
            self.provision_from_json(options['json_file'])
        else:
            self.provision_from_args(options)

    def provision_from_args(self, options):
        """Provisiona tenant usando argumentos da linha de comando"""
        # Validar argumentos obrigatórios
        required_args = ['name', 'subdomain', 'admin_email', 'admin_password']
        for arg in required_args:
            if not options.get(arg.replace('-', '_')):
                raise CommandError(f'Argumento obrigatório ausente: --{arg}')
        
        # Preparar dados do tenant
        tenant_data = {
            'name': options['name'],
            'subdomain': options['subdomain'],
            'admin_email': options['admin_email'],
            'admin_password': options['admin_password'],
            'plan_type': options['plan_type'],
            'max_users': options['max_users'],
            'max_animals': options['max_animals']
        }
        
        # Adicionar campos opcionais se fornecidos
        if options.get('admin_first_name'):
            tenant_data['admin_first_name'] = options['admin_first_name']
        if options.get('admin_last_name'):
            tenant_data['admin_last_name'] = options['admin_last_name']
        
        self.provision_tenant(tenant_data)

    def provision_from_json(self, json_file_path):
        """Provisiona tenant usando arquivo JSON"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                tenant_data = json.load(f)
            
            self.provision_tenant(tenant_data)
            
        except FileNotFoundError:
            raise CommandError(f'Arquivo não encontrado: {json_file_path}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Erro ao ler JSON: {str(e)}')

    def provision_tenant(self, tenant_data):
        """Executa o provisionamento do tenant"""
        self.stdout.write(
            self.style.HTTP_INFO(f"Iniciando provisionamento do tenant: {tenant_data['name']}")
        )
        
        try:
            tenant = tenant_provisioning_service.create_tenant(tenant_data)
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Tenant provisionado com sucesso!")
            )
            self.stdout.write(f"  ID: {tenant.id}")
            self.stdout.write(f"  Nome: {tenant.name}")
            self.stdout.write(f"  Subdomínio: {tenant.subdomain}")
            self.stdout.write(f"  Schema: {tenant.schema_name}")
            self.stdout.write(f"  Plano: {tenant.plan_type}")
            self.stdout.write(f"  Criado em: {tenant.created_at}")
            
            # Executar validação automática
            self.stdout.write(self.style.HTTP_INFO("\nValidando provisionamento..."))
            validation_result = tenant_provisioning_service.validate_tenant_provisioning(tenant)
            
            if validation_result['valid']:
                self.stdout.write(self.style.SUCCESS("✓ Validação passou - tenant está funcionando corretamente"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Validação encontrou problemas:"))
                for error in validation_result['errors']:
                    self.stdout.write(f"  - {error}")
            
            if validation_result['warnings']:
                self.stdout.write(self.style.WARNING("Avisos:"))
                for warning in validation_result['warnings']:
                    self.stdout.write(f"  - {warning}")
            
            # Mostrar estatísticas
            checks = validation_result['checks']
            self.stdout.write(f"\nEstatísticas:")
            self.stdout.write(f"  Usuários admin: {1 if checks.get('has_admin_user') else 0}")
            self.stdout.write(f"  Configurações: {checks.get('configuration_count', 0)}")
            self.stdout.write(f"  Serviços iniciais: {checks.get('initial_services', 0)}")
            self.stdout.write(f"  Produtos iniciais: {checks.get('initial_products', 0)}")
            
        except TenantProvisioningError as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro no provisionamento: {str(e)}"))
            
            if e.rollback_info:
                self.stdout.write("Status do rollback:")
                for step, completed in e.rollback_info.items():
                    status = "✓" if completed else "✗"
                    self.stdout.write(f"  {status} {step}")
            
            raise CommandError("Provisionamento falhou")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro inesperado: {str(e)}"))
            raise CommandError("Provisionamento falhou com erro inesperado")

    def validate_tenant(self, tenant_identifier):
        """Valida um tenant existente"""
        self.stdout.write(
            self.style.HTTP_INFO(f"Validando tenant: {tenant_identifier}")
        )
        
        try:
            from tenants.models import Tenant
            
            # Buscar tenant
            if len(tenant_identifier) == 36:  # UUID
                tenant = Tenant.objects.get(id=tenant_identifier)
            else:  # Subdomain
                tenant = Tenant.objects.get(subdomain=tenant_identifier)
            
            # Executar validação
            validation_result = tenant_provisioning_service.validate_tenant_provisioning(tenant)
            
            self.stdout.write(f"Tenant: {tenant.name} ({tenant.subdomain})")
            
            if validation_result['valid']:
                self.stdout.write(self.style.SUCCESS("✓ Tenant está funcionando corretamente"))
            else:
                self.stdout.write(self.style.ERROR("✗ Tenant tem problemas:"))
                for error in validation_result['errors']:
                    self.stdout.write(f"  - {error}")
            
            if validation_result['warnings']:
                self.stdout.write(self.style.WARNING("Avisos:"))
                for warning in validation_result['warnings']:
                    self.stdout.write(f"  - {warning}")
            
            # Mostrar detalhes dos checks
            self.stdout.write("\nDetalhes da validação:")
            checks = validation_result['checks']
            for check_name, check_result in checks.items():
                status = "✓" if check_result else "✗"
                self.stdout.write(f"  {status} {check_name}: {check_result}")
            
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant não encontrado: {tenant_identifier}')
        except Exception as e:
            raise CommandError(f'Erro na validação: {str(e)}')

    def show_tenant_status(self, tenant_identifier):
        """Mostra status completo de um tenant"""
        self.stdout.write(
            self.style.HTTP_INFO(f"Obtendo status do tenant: {tenant_identifier}")
        )
        
        status = tenant_provisioning_service.get_provisioning_status(tenant_identifier)
        
        if 'error' in status:
            raise CommandError(status['error'])
        
        # Mostrar informações do tenant
        tenant_info = status['tenant']
        self.stdout.write(f"\nInformações do Tenant:")
        self.stdout.write(f"  ID: {tenant_info['id']}")
        self.stdout.write(f"  Nome: {tenant_info['name']}")
        self.stdout.write(f"  Subdomínio: {tenant_info['subdomain']}")
        self.stdout.write(f"  Schema: {tenant_info['schema_name']}")
        self.stdout.write(f"  Plano: {tenant_info['plan_type']}")
        self.stdout.write(f"  Ativo: {'Sim' if tenant_info['is_active'] else 'Não'}")
        self.stdout.write(f"  Criado em: {tenant_info['created_at']}")
        
        # Status de provisionamento
        prov_status = status['provisioning_status']
        if prov_status == 'complete':
            self.stdout.write(self.style.SUCCESS(f"\nStatus: ✓ Provisionamento completo"))
        else:
            self.stdout.write(self.style.WARNING(f"\nStatus: ⚠ Provisionamento incompleto"))
        
        # Validação
        validation = status['validation']
        if validation['errors']:
            self.stdout.write(self.style.ERROR("Erros encontrados:"))
            for error in validation['errors']:
                self.stdout.write(f"  - {error}")
        
        if validation['warnings']:
            self.stdout.write(self.style.WARNING("Avisos:"))
            for warning in validation['warnings']:
                self.stdout.write(f"  - {warning}")
        
        # Checks detalhados
        self.stdout.write("\nChecks de validação:")
        for check_name, check_result in validation['checks'].items():
            status_icon = "✓" if check_result else "✗"
            self.stdout.write(f"  {status_icon} {check_name}: {check_result}")
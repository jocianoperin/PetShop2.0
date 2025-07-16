"""
Serviços para provisionamento automático de tenants.
Implementa criação completa de novos tenants com validações, rollback e dados iniciais.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from django.db import transaction, connection
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from contextlib import contextmanager

from .models import Tenant, TenantUser, TenantConfiguration
from .utils import (
    tenant_context, 
    create_tenant_schema, 
    drop_tenant_schema,
    execute_in_tenant_schema,
    _is_postgresql
)
from .fixtures import tenant_fixture_manager


logger = logging.getLogger('tenants.provisioning')


class TenantProvisioningError(Exception):
    """Exceção específica para erros de provisionamento de tenant"""
    def __init__(self, message: str, tenant_data: Dict = None, rollback_info: Dict = None):
        super().__init__(message)
        self.tenant_data = tenant_data
        self.rollback_info = rollback_info


class TenantProvisioningService:
    """
    Serviço para provisionamento automático de tenants.
    
    Responsabilidades:
    - Criar tenant com validações
    - Criar schema de banco de dados
    - Executar migrações no novo schema
    - Inserir dados iniciais
    - Criar usuário administrador
    - Sistema de rollback para falhas
    """
    
    def __init__(self):
        self.logger = logger
    
    def create_tenant(self, tenant_data: Dict[str, Any]) -> Tenant:
        """
        Cria um novo tenant com provisionamento completo.
        
        Args:
            tenant_data: Dicionário com dados do tenant
                - name: Nome do petshop
                - subdomain: Subdomínio desejado
                - admin_email: Email do administrador
                - admin_password: Senha do administrador
                - admin_first_name: Primeiro nome do admin (opcional)
                - admin_last_name: Último nome do admin (opcional)
                - plan_type: Tipo do plano (opcional, padrão: 'basic')
                - max_users: Máximo de usuários (opcional)
                - max_animals: Máximo de animais (opcional)
        
        Returns:
            Tenant: Instância do tenant criado
            
        Raises:
            TenantProvisioningError: Em caso de erro no provisionamento
        """
        rollback_info = {
            'tenant_created': False,
            'schema_created': False,
            'migrations_applied': False,
            'admin_user_created': False,
            'initial_data_created': False
        }
        
        try:
            with transaction.atomic():
                # 1. Validar dados de entrada
                self._validate_tenant_data(tenant_data)
                
                # 2. Criar registro do tenant
                tenant = self._create_tenant_record(tenant_data)
                rollback_info['tenant_created'] = True
                self.logger.info(f"Tenant record created: {tenant.name} ({tenant.id})")
                
                # 3. Criar schema no banco de dados
                if not self._create_tenant_schema(tenant):
                    raise TenantProvisioningError(
                        f"Falha ao criar schema para tenant {tenant.name}",
                        tenant_data,
                        rollback_info
                    )
                rollback_info['schema_created'] = True
                self.logger.info(f"Schema created: {tenant.schema_name}")
                
                # 4. Executar migrações no novo schema
                self._run_tenant_migrations(tenant)
                rollback_info['migrations_applied'] = True
                self.logger.info(f"Migrations applied for tenant: {tenant.name}")
                
                # 5. Criar usuário administrador
                admin_user = self._create_admin_user(tenant, tenant_data)
                rollback_info['admin_user_created'] = True
                self.logger.info(f"Admin user created: {admin_user.email}")
                
                # 6. Inserir dados iniciais
                self._setup_initial_data(tenant, tenant_data)
                rollback_info['initial_data_created'] = True
                self.logger.info(f"Initial data setup completed for tenant: {tenant.name}")
                
                # 7. Configurações padrão
                self._setup_default_configurations(tenant)
                self.logger.info(f"Default configurations setup for tenant: {tenant.name}")
                
                self.logger.info(f"Tenant provisioning completed successfully: {tenant.name}")
                return tenant
                
        except Exception as e:
            self.logger.error(f"Tenant provisioning failed: {str(e)}", exc_info=True)
            
            # Executar rollback
            try:
                self._rollback_tenant_creation(tenant_data, rollback_info)
            except Exception as rollback_error:
                self.logger.error(f"Rollback failed: {str(rollback_error)}", exc_info=True)
            
            # Re-raise como TenantProvisioningError
            if isinstance(e, TenantProvisioningError):
                raise
            else:
                raise TenantProvisioningError(
                    f"Erro no provisionamento do tenant: {str(e)}",
                    tenant_data,
                    rollback_info
                ) from e
    
    def _validate_tenant_data(self, tenant_data: Dict[str, Any]) -> None:
        """Valida os dados de entrada para criação do tenant"""
        required_fields = ['name', 'subdomain', 'admin_email', 'admin_password']
        
        for field in required_fields:
            if not tenant_data.get(field):
                raise TenantProvisioningError(f"Campo obrigatório ausente: {field}")
        
        # Validar formato do subdomínio
        subdomain = tenant_data['subdomain'].lower().strip()
        if not subdomain.replace('-', '').replace('_', '').isalnum():
            raise TenantProvisioningError("Subdomínio deve conter apenas letras, números e hífens")
        
        # Verificar se subdomínio já existe
        if Tenant.objects.filter(subdomain=subdomain).exists():
            raise TenantProvisioningError(f"Subdomínio '{subdomain}' já está em uso")
        
        # Validar email do administrador
        admin_email = tenant_data['admin_email'].lower().strip()
        if TenantUser.objects.filter(email=admin_email).exists():
            raise TenantProvisioningError(f"Email '{admin_email}' já está em uso")
        
        # Validar senha
        password = tenant_data['admin_password']
        if len(password) < 8:
            raise TenantProvisioningError("Senha deve ter pelo menos 8 caracteres")
    
    def _create_tenant_record(self, tenant_data: Dict[str, Any]) -> Tenant:
        """Cria o registro do tenant no banco de dados"""
        subdomain = tenant_data['subdomain'].lower().strip()
        schema_name = f"tenant_{subdomain.replace('-', '_')}"
        
        # Garantir que o schema_name seja único
        counter = 1
        original_schema_name = schema_name
        while Tenant.objects.filter(schema_name=schema_name).exists():
            schema_name = f"{original_schema_name}_{counter}"
            counter += 1
        
        tenant = Tenant.objects.create(
            name=tenant_data['name'].strip(),
            subdomain=subdomain,
            schema_name=schema_name,
            plan_type=tenant_data.get('plan_type', 'basic'),
            max_users=tenant_data.get('max_users', 10),
            max_animals=tenant_data.get('max_animals', 1000)
        )
        
        return tenant
    
    def _create_tenant_schema(self, tenant: Tenant) -> bool:
        """Cria o schema no banco de dados para o tenant"""
        try:
            if _is_postgresql():
                with connection.cursor() as cursor:
                    # Verificar se schema já existe
                    cursor.execute("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name = %s
                    """, [tenant.schema_name])
                    
                    if cursor.fetchone():
                        self.logger.warning(f"Schema {tenant.schema_name} já existe")
                        return True
                    
                    # Criar schema
                    cursor.execute(f"CREATE SCHEMA {tenant.schema_name}")
                    
                    # Definir permissões
                    cursor.execute(f"GRANT USAGE ON SCHEMA {tenant.schema_name} TO current_user")
                    cursor.execute(f"GRANT CREATE ON SCHEMA {tenant.schema_name} TO current_user")
                    
                    self.logger.info(f"PostgreSQL schema created: {tenant.schema_name}")
            else:
                # Para SQLite, não há schemas reais
                self.logger.info(f"SQLite - logical schema created: {tenant.schema_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create schema {tenant.schema_name}: {str(e)}")
            return False
    
    def _run_tenant_migrations(self, tenant: Tenant) -> None:
        """Executa migrações no schema do tenant"""
        try:
            if _is_postgresql():
                # Para PostgreSQL, definir o search_path para o schema do tenant
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
            
            # Executar migrações no contexto do tenant
            with tenant_context(tenant):
                # Migrar apenas o app 'api' que contém os modelos de negócio
                call_command('migrate', 'api', verbosity=0, interactive=False)
                
                # Migrar outros apps se necessário
                call_command('migrate', verbosity=0, interactive=False)
                
        except Exception as e:
            raise TenantProvisioningError(f"Falha ao executar migrações: {str(e)}")
    
    def _create_admin_user(self, tenant: Tenant, tenant_data: Dict[str, Any]) -> TenantUser:
        """Cria o usuário administrador do tenant"""
        from django.contrib.auth.hashers import make_password
        
        admin_user = TenantUser.objects.create(
            tenant=tenant,
            email=tenant_data['admin_email'].lower().strip(),
            password_hash=make_password(tenant_data['admin_password']),
            first_name=tenant_data.get('admin_first_name', '').strip(),
            last_name=tenant_data.get('admin_last_name', '').strip(),
            role='admin',
            is_active=True
        )
        
        return admin_user
    
    def _setup_initial_data(self, tenant: Tenant, tenant_data: Dict[str, Any]) -> None:
        """Configura dados iniciais para o tenant usando o sistema de fixtures"""
        try:
            # Aplicar fixtures padrão usando o TenantFixtureManager
            fixture_results = tenant_fixture_manager.apply_fixtures(
                tenant, 
                fixture_types=['services', 'products']
            )
            
            total_items = sum(fixture_results.values())
            self.logger.info(f"Initial data created via fixtures: {fixture_results} (total: {total_items} items)")
            
        except Exception as e:
            self.logger.error(f"Error applying fixtures for tenant {tenant.name}: {str(e)}")
            # Fallback para dados básicos se fixtures falharem
            self._setup_basic_initial_data(tenant)
    
    def _setup_basic_initial_data(self, tenant: Tenant) -> None:
        """Fallback para dados iniciais básicos se fixtures falharem"""
        with tenant_context(tenant):
            from api.models import Servico, Produto
            from datetime import timedelta
            
            # Criar apenas alguns serviços básicos
            basic_services = [
                {
                    'nome': 'Banho e Tosa',
                    'descricao': 'Serviço completo de banho e tosa',
                    'preco': 50.00,
                    'duracao_estimada': timedelta(hours=1, minutes=30),
                    'ativo': True
                },
                {
                    'nome': 'Consulta Veterinária',
                    'descricao': 'Consulta veterinária geral',
                    'preco': 80.00,
                    'duracao_estimada': timedelta(minutes=30),
                    'ativo': True
                }
            ]
            
            for service_data in basic_services:
                if not Servico.objects.filter(nome=service_data['nome']).exists():
                    Servico.objects.create(**service_data)
            
            # Criar apenas alguns produtos básicos
            basic_products = [
                {
                    'nome': 'Ração Premium',
                    'descricao': 'Ração premium para cães',
                    'categoria': 'racao',
                    'preco': 120.00,
                    'estoque': 10,
                    'estoque_minimo': 3,
                    'ativo': True
                },
                {
                    'nome': 'Shampoo Neutro',
                    'descricao': 'Shampoo neutro para pets',
                    'categoria': 'higiene',
                    'preco': 25.00,
                    'estoque': 20,
                    'estoque_minimo': 5,
                    'ativo': True
                }
            ]
            
            for product_data in basic_products:
                if not Produto.objects.filter(nome=product_data['nome']).exists():
                    Produto.objects.create(**product_data)
            
            self.logger.info("Basic initial data created as fallback")
    
    def _setup_default_configurations(self, tenant: Tenant) -> None:
        """Configura configurações padrão para o tenant usando o sistema de fixtures"""
        try:
            # Aplicar fixtures de configurações usando o TenantFixtureManager
            fixture_results = tenant_fixture_manager.apply_fixtures(
                tenant, 
                fixture_types=['configurations']
            )
            
            config_count = fixture_results.get('configurations', 0)
            self.logger.info(f"Default configurations created via fixtures: {config_count} configs")
            
        except Exception as e:
            self.logger.error(f"Error applying configuration fixtures for tenant {tenant.name}: {str(e)}")
            # Fallback para configurações básicas se fixtures falharem
            self._setup_basic_configurations(tenant)
    
    def _setup_basic_configurations(self, tenant: Tenant) -> None:
        """Fallback para configurações básicas se fixtures falharem"""
        basic_configs = [
            {
                'key': 'business_hours_start',
                'value': '08:00',
                'type': 'string',
                'sensitive': False
            },
            {
                'key': 'business_hours_end',
                'value': '18:00',
                'type': 'string',
                'sensitive': False
            },
            {
                'key': 'currency',
                'value': 'BRL',
                'type': 'string',
                'sensitive': False
            },
            {
                'key': 'timezone',
                'value': 'America/Sao_Paulo',
                'type': 'string',
                'sensitive': False
            }
        ]
        
        for config in basic_configs:
            TenantConfiguration.set_config(
                tenant=tenant,
                key=config['key'],
                value=config['value'],
                config_type=config['type'],
                is_sensitive=config['sensitive']
            )
        
        self.logger.info(f"Basic configurations created as fallback: {len(basic_configs)} configs")
    
    def _rollback_tenant_creation(self, tenant_data: Dict[str, Any], rollback_info: Dict[str, bool]) -> None:
        """Executa rollback em caso de falha no provisionamento"""
        self.logger.info("Starting tenant creation rollback...")
        
        subdomain = tenant_data.get('subdomain', '').lower().strip()
        
        try:
            # Buscar o tenant se foi criado
            tenant = None
            if rollback_info.get('tenant_created'):
                try:
                    tenant = Tenant.objects.get(subdomain=subdomain)
                except Tenant.DoesNotExist:
                    pass
            
            # Remover dados iniciais (não é necessário, será removido com o schema)
            
            # Remover usuário admin
            if rollback_info.get('admin_user_created') and tenant:
                TenantUser.objects.filter(tenant=tenant, role='admin').delete()
                self.logger.info("Admin user removed during rollback")
            
            # Remover configurações
            if tenant:
                TenantConfiguration.objects.filter(tenant=tenant).delete()
                self.logger.info("Tenant configurations removed during rollback")
            
            # Remover schema do banco
            if rollback_info.get('schema_created') and tenant:
                if _is_postgresql():
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(f"DROP SCHEMA IF EXISTS {tenant.schema_name} CASCADE")
                        self.logger.info(f"Schema {tenant.schema_name} dropped during rollback")
                    except Exception as e:
                        self.logger.error(f"Failed to drop schema during rollback: {str(e)}")
            
            # Remover registro do tenant
            if rollback_info.get('tenant_created') and tenant:
                tenant.delete()
                self.logger.info("Tenant record removed during rollback")
            
            self.logger.info("Tenant creation rollback completed")
            
        except Exception as e:
            self.logger.error(f"Error during rollback: {str(e)}", exc_info=True)
            raise TenantProvisioningError(f"Falha no rollback: {str(e)}")
    
    def validate_tenant_provisioning(self, tenant: Tenant) -> Dict[str, Any]:
        """
        Valida se um tenant foi provisionado corretamente.
        
        Args:
            tenant: Instância do tenant para validar
            
        Returns:
            Dict com resultado da validação
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        try:
            # 1. Verificar se tenant existe e está ativo
            if not tenant.is_active:
                validation_result['errors'].append("Tenant não está ativo")
                validation_result['valid'] = False
            validation_result['checks']['tenant_active'] = tenant.is_active
            
            # 2. Verificar se schema existe (apenas PostgreSQL)
            schema_exists = True
            if _is_postgresql():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name = %s
                    """, [tenant.schema_name])
                    schema_exists = cursor.fetchone() is not None
            
            if not schema_exists:
                validation_result['errors'].append(f"Schema {tenant.schema_name} não existe")
                validation_result['valid'] = False
            validation_result['checks']['schema_exists'] = schema_exists
            
            # 3. Verificar se usuário admin existe
            admin_users = TenantUser.objects.filter(tenant=tenant, role='admin', is_active=True)
            has_admin = admin_users.exists()
            if not has_admin:
                validation_result['errors'].append("Nenhum usuário administrador ativo encontrado")
                validation_result['valid'] = False
            validation_result['checks']['has_admin_user'] = has_admin
            
            # 4. Verificar se tabelas existem no schema
            with tenant_context(tenant):
                from api.models import Cliente, Animal, Servico, Produto
                
                tables_exist = True
                try:
                    # Tentar fazer uma query simples em cada modelo
                    Cliente.objects.count()
                    Animal.objects.count()
                    Servico.objects.count()
                    Produto.objects.count()
                except Exception:
                    tables_exist = False
                    validation_result['errors'].append("Tabelas do tenant não estão acessíveis")
                    validation_result['valid'] = False
                
                validation_result['checks']['tables_accessible'] = tables_exist
            
            # 5. Verificar configurações padrão
            config_count = TenantConfiguration.objects.filter(tenant=tenant).count()
            has_configs = config_count > 0
            if not has_configs:
                validation_result['warnings'].append("Nenhuma configuração padrão encontrada")
            validation_result['checks']['has_configurations'] = has_configs
            validation_result['checks']['configuration_count'] = config_count
            
            # 6. Verificar dados iniciais
            with tenant_context(tenant):
                from api.models import Servico, Produto
                
                service_count = Servico.objects.count()
                product_count = Produto.objects.count()
                
                if service_count == 0:
                    validation_result['warnings'].append("Nenhum serviço padrão encontrado")
                if product_count == 0:
                    validation_result['warnings'].append("Nenhum produto padrão encontrado")
                
                validation_result['checks']['initial_services'] = service_count
                validation_result['checks']['initial_products'] = product_count
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Erro durante validação: {str(e)}")
            self.logger.error(f"Validation error for tenant {tenant.name}: {str(e)}", exc_info=True)
        
        return validation_result
    
    def get_provisioning_status(self, tenant_identifier: str) -> Dict[str, Any]:
        """
        Obtém o status de provisionamento de um tenant.
        
        Args:
            tenant_identifier: ID ou subdomínio do tenant
            
        Returns:
            Dict com status do provisionamento
        """
        try:
            # Buscar tenant
            if len(tenant_identifier) == 36:  # UUID
                tenant = Tenant.objects.get(id=tenant_identifier)
            else:  # Subdomain
                tenant = Tenant.objects.get(subdomain=tenant_identifier)
            
            # Executar validação
            validation_result = self.validate_tenant_provisioning(tenant)
            
            return {
                'tenant': {
                    'id': str(tenant.id),
                    'name': tenant.name,
                    'subdomain': tenant.subdomain,
                    'schema_name': tenant.schema_name,
                    'created_at': tenant.created_at.isoformat(),
                    'is_active': tenant.is_active,
                    'plan_type': tenant.plan_type
                },
                'provisioning_status': 'complete' if validation_result['valid'] else 'incomplete',
                'validation': validation_result
            }
            
        except Tenant.DoesNotExist:
            return {
                'error': 'Tenant não encontrado',
                'tenant_identifier': tenant_identifier
            }
        except Exception as e:
            self.logger.error(f"Error getting provisioning status: {str(e)}", exc_info=True)
            return {
                'error': f'Erro ao obter status: {str(e)}',
                'tenant_identifier': tenant_identifier
            }


# Instância global do serviço
tenant_provisioning_service = TenantProvisioningService()
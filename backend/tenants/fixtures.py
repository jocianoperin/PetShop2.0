"""
Sistema de fixtures para dados iniciais de tenants.
Permite configuração flexível de dados padrão para novos tenants.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError

from .utils import tenant_context


logger = logging.getLogger('tenants.fixtures')


class TenantFixtureError(Exception):
    """Exceção para erros no sistema de fixtures"""
    pass


class TenantFixtureManager:
    """
    Gerenciador de fixtures para dados iniciais de tenants.
    
    Permite definir e aplicar conjuntos de dados padrão para novos tenants,
    incluindo serviços, produtos, configurações e outros dados necessários.
    """
    
    def __init__(self):
        self.logger = logger
        self._fixtures = {}
        self._load_default_fixtures()
    
    def _load_default_fixtures(self):
        """Carrega fixtures padrão do sistema"""
        self._fixtures = {
            'services': self._get_default_services(),
            'products': self._get_default_products(),
            'configurations': self._get_default_configurations(),
            'categories': self._get_default_categories()
        }
    
    def _get_default_services(self) -> List[Dict[str, Any]]:
        """Define serviços padrão para novos tenants"""
        return [
            {
                'nome': 'Banho e Tosa Completo',
                'descricao': 'Serviço completo de banho, tosa, corte de unhas e limpeza de ouvidos',
                'preco': 50.00,
                'duracao_estimada': timedelta(hours=1, minutes=30),
                'ativo': True,
                'categoria': 'higiene'
            },
            {
                'nome': 'Banho Simples',
                'descricao': 'Banho com shampoo neutro e secagem',
                'preco': 25.00,
                'duracao_estimada': timedelta(minutes=45),
                'ativo': True,
                'categoria': 'higiene'
            },
            {
                'nome': 'Tosa Higiênica',
                'descricao': 'Tosa das áreas íntimas e patas',
                'preco': 20.00,
                'duracao_estimada': timedelta(minutes=30),
                'ativo': True,
                'categoria': 'higiene'
            },
            {
                'nome': 'Consulta Veterinária',
                'descricao': 'Consulta veterinária geral com exame clínico',
                'preco': 80.00,
                'duracao_estimada': timedelta(minutes=30),
                'ativo': True,
                'categoria': 'veterinaria'
            },
            {
                'nome': 'Vacinação V8',
                'descricao': 'Aplicação de vacina V8 (óctupla canina)',
                'preco': 35.00,
                'duracao_estimada': timedelta(minutes=15),
                'ativo': True,
                'categoria': 'veterinaria'
            },
            {
                'nome': 'Vacinação V10',
                'descricao': 'Aplicação de vacina V10 (décupla canina)',
                'preco': 40.00,
                'duracao_estimada': timedelta(minutes=15),
                'ativo': True,
                'categoria': 'veterinaria'
            },
            {
                'nome': 'Vacinação Antirrábica',
                'descricao': 'Aplicação de vacina antirrábica',
                'preco': 30.00,
                'duracao_estimada': timedelta(minutes=10),
                'ativo': True,
                'categoria': 'veterinaria'
            },
            {
                'nome': 'Corte de Unhas',
                'descricao': 'Corte e limpeza das unhas',
                'preco': 15.00,
                'duracao_estimada': timedelta(minutes=15),
                'ativo': True,
                'categoria': 'higiene'
            },
            {
                'nome': 'Limpeza de Ouvidos',
                'descricao': 'Limpeza e higienização dos ouvidos',
                'preco': 12.00,
                'duracao_estimada': timedelta(minutes=10),
                'ativo': True,
                'categoria': 'higiene'
            },
            {
                'nome': 'Hospedagem Diária',
                'descricao': 'Hospedagem de animais por dia (inclui alimentação)',
                'preco': 45.00,
                'duracao_estimada': timedelta(hours=24),
                'ativo': True,
                'categoria': 'hospedagem'
            }
        ]
    
    def _get_default_products(self) -> List[Dict[str, Any]]:
        """Define produtos padrão para novos tenants"""
        return [
            # Rações
            {
                'nome': 'Ração Premium Cães Adultos 15kg',
                'descricao': 'Ração super premium para cães adultos de porte médio e grande',
                'categoria': 'racao',
                'preco': 120.00,
                'estoque': 10,
                'estoque_minimo': 3,
                'ativo': True,
                'marca': 'Premium Pet'
            },
            {
                'nome': 'Ração Premium Cães Filhotes 3kg',
                'descricao': 'Ração super premium para filhotes até 12 meses',
                'categoria': 'racao',
                'preco': 45.00,
                'estoque': 15,
                'estoque_minimo': 5,
                'ativo': True,
                'marca': 'Premium Pet'
            },
            {
                'nome': 'Ração Premium Gatos Adultos 3kg',
                'descricao': 'Ração super premium para gatos adultos',
                'categoria': 'racao',
                'preco': 55.00,
                'estoque': 12,
                'estoque_minimo': 4,
                'ativo': True,
                'marca': 'Premium Pet'
            },
            
            # Produtos de Higiene
            {
                'nome': 'Shampoo Neutro 500ml',
                'descricao': 'Shampoo neutro para cães e gatos de todos os tipos de pelo',
                'categoria': 'higiene',
                'preco': 25.00,
                'estoque': 20,
                'estoque_minimo': 5,
                'ativo': True,
                'marca': 'Pet Clean'
            },
            {
                'nome': 'Condicionador Hidratante 500ml',
                'descricao': 'Condicionador hidratante para pelos ressecados',
                'categoria': 'higiene',
                'preco': 30.00,
                'estoque': 15,
                'estoque_minimo': 4,
                'ativo': True,
                'marca': 'Pet Clean'
            },
            {
                'nome': 'Shampoo Antipulgas 500ml',
                'descricao': 'Shampoo com ação antipulgas e carrapatos',
                'categoria': 'higiene',
                'preco': 35.00,
                'estoque': 10,
                'estoque_minimo': 3,
                'ativo': True,
                'marca': 'Pet Clean'
            },
            
            # Brinquedos
            {
                'nome': 'Brinquedo Mordedor Osso',
                'descricao': 'Brinquedo mordedor em formato de osso para cães',
                'categoria': 'brinquedo',
                'preco': 18.00,
                'estoque': 25,
                'estoque_minimo': 8,
                'ativo': True,
                'marca': 'Pet Fun'
            },
            {
                'nome': 'Bolinha de Tênis',
                'descricao': 'Bolinha de tênis para cães brincarem',
                'categoria': 'brinquedo',
                'preco': 8.00,
                'estoque': 30,
                'estoque_minimo': 10,
                'ativo': True,
                'marca': 'Pet Fun'
            },
            {
                'nome': 'Varinha com Penas',
                'descricao': 'Brinquedo varinha com penas para gatos',
                'categoria': 'brinquedo',
                'preco': 15.00,
                'estoque': 20,
                'estoque_minimo': 6,
                'ativo': True,
                'marca': 'Pet Fun'
            },
            
            # Acessórios
            {
                'nome': 'Coleira Ajustável Pequena',
                'descricao': 'Coleira ajustável para cães de pequeno porte',
                'categoria': 'acessorio',
                'preco': 25.00,
                'estoque': 15,
                'estoque_minimo': 5,
                'ativo': True,
                'marca': 'Pet Style'
            },
            {
                'nome': 'Coleira Ajustável Média',
                'descricao': 'Coleira ajustável para cães de médio porte',
                'categoria': 'acessorio',
                'preco': 35.00,
                'estoque': 12,
                'estoque_minimo': 4,
                'ativo': True,
                'marca': 'Pet Style'
            },
            {
                'nome': 'Guia Retrátil 5m',
                'descricao': 'Guia retrátil de 5 metros para passeios',
                'categoria': 'acessorio',
                'preco': 45.00,
                'estoque': 8,
                'estoque_minimo': 2,
                'ativo': True,
                'marca': 'Pet Style'
            },
            
            # Medicamentos básicos
            {
                'nome': 'Vermífugo Cães 10ml',
                'descricao': 'Vermífugo líquido para cães até 10kg',
                'categoria': 'medicamento',
                'preco': 22.00,
                'estoque': 12,
                'estoque_minimo': 4,
                'ativo': True,
                'marca': 'Pet Health'
            },
            {
                'nome': 'Antipulgas Spray 250ml',
                'descricao': 'Spray antipulgas e carrapatos para ambiente',
                'categoria': 'medicamento',
                'preco': 28.00,
                'estoque': 10,
                'estoque_minimo': 3,
                'ativo': True,
                'marca': 'Pet Health'
            }
        ]
    
    def _get_default_configurations(self) -> List[Dict[str, Any]]:
        """Define configurações padrão para novos tenants"""
        return [
            # Horários de funcionamento
            {
                'key': 'business_hours_start',
                'value': '08:00',
                'type': 'string',
                'sensitive': False,
                'description': 'Horário de abertura do estabelecimento'
            },
            {
                'key': 'business_hours_end',
                'value': '18:00',
                'type': 'string',
                'sensitive': False,
                'description': 'Horário de fechamento do estabelecimento'
            },
            {
                'key': 'lunch_break_start',
                'value': '12:00',
                'type': 'string',
                'sensitive': False,
                'description': 'Início do horário de almoço'
            },
            {
                'key': 'lunch_break_end',
                'value': '13:00',
                'type': 'string',
                'sensitive': False,
                'description': 'Fim do horário de almoço'
            },
            
            # Configurações de agendamento
            {
                'key': 'appointment_duration_default',
                'value': '30',
                'type': 'integer',
                'sensitive': False,
                'description': 'Duração padrão de agendamentos em minutos'
            },
            {
                'key': 'appointment_interval',
                'value': '15',
                'type': 'integer',
                'sensitive': False,
                'description': 'Intervalo mínimo entre agendamentos em minutos'
            },
            {
                'key': 'max_appointments_per_day',
                'value': '50',
                'type': 'integer',
                'sensitive': False,
                'description': 'Máximo de agendamentos por dia'
            },
            {
                'key': 'advance_booking_days',
                'value': '30',
                'type': 'integer',
                'sensitive': False,
                'description': 'Quantos dias de antecedência permitir agendamentos'
            },
            
            # Notificações
            {
                'key': 'notification_email_enabled',
                'value': 'true',
                'type': 'boolean',
                'sensitive': False,
                'description': 'Habilitar notificações por email'
            },
            {
                'key': 'notification_sms_enabled',
                'value': 'false',
                'type': 'boolean',
                'sensitive': False,
                'description': 'Habilitar notificações por SMS'
            },
            {
                'key': 'reminder_hours_before',
                'value': '24',
                'type': 'integer',
                'sensitive': False,
                'description': 'Horas de antecedência para lembrete de agendamento'
            },
            
            # Estoque
            {
                'key': 'low_stock_alert_enabled',
                'value': 'true',
                'type': 'boolean',
                'sensitive': False,
                'description': 'Habilitar alertas de estoque baixo'
            },
            {
                'key': 'auto_reorder_enabled',
                'value': 'false',
                'type': 'boolean',
                'sensitive': False,
                'description': 'Habilitar reposição automática de estoque'
            },
            
            # Financeiro
            {
                'key': 'currency',
                'value': 'BRL',
                'type': 'string',
                'sensitive': False,
                'description': 'Moeda utilizada'
            },
            {
                'key': 'tax_rate',
                'value': '0.00',
                'type': 'float',
                'sensitive': False,
                'description': 'Taxa de imposto padrão (%)'
            },
            {
                'key': 'payment_methods',
                'value': '["dinheiro", "cartao_debito", "cartao_credito", "pix"]',
                'type': 'json',
                'sensitive': False,
                'description': 'Métodos de pagamento aceitos'
            },
            
            # Sistema
            {
                'key': 'timezone',
                'value': 'America/Sao_Paulo',
                'type': 'string',
                'sensitive': False,
                'description': 'Fuso horário do estabelecimento'
            },
            {
                'key': 'date_format',
                'value': 'dd/mm/yyyy',
                'type': 'string',
                'sensitive': False,
                'description': 'Formato de data preferido'
            },
            {
                'key': 'language',
                'value': 'pt-BR',
                'type': 'string',
                'sensitive': False,
                'description': 'Idioma do sistema'
            },
            
            # Personalização
            {
                'key': 'business_name',
                'value': '',
                'type': 'string',
                'sensitive': False,
                'description': 'Nome fantasia do estabelecimento'
            },
            {
                'key': 'business_phone',
                'value': '',
                'type': 'string',
                'sensitive': False,
                'description': 'Telefone do estabelecimento'
            },
            {
                'key': 'business_email',
                'value': '',
                'type': 'string',
                'sensitive': False,
                'description': 'Email do estabelecimento'
            },
            {
                'key': 'business_address',
                'value': '',
                'type': 'string',
                'sensitive': False,
                'description': 'Endereço do estabelecimento'
            }
        ]
    
    def _get_default_categories(self) -> List[Dict[str, Any]]:
        """Define categorias padrão (se necessário para futuras extensões)"""
        return [
            {'name': 'Higiene', 'description': 'Serviços de banho, tosa e limpeza'},
            {'name': 'Veterinária', 'description': 'Consultas e procedimentos veterinários'},
            {'name': 'Hospedagem', 'description': 'Serviços de hospedagem e hotel'},
            {'name': 'Adestramento', 'description': 'Serviços de adestramento e comportamento'}
        ]
    
    def apply_fixtures(self, tenant, fixture_types: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Aplica fixtures para um tenant específico.
        
        Args:
            tenant: Instância do tenant
            fixture_types: Lista de tipos de fixtures para aplicar (None = todos)
            
        Returns:
            Dict com contadores de itens criados por tipo
        """
        if fixture_types is None:
            fixture_types = list(self._fixtures.keys())
        
        results = {}
        
        with tenant_context(tenant):
            with transaction.atomic():
                for fixture_type in fixture_types:
                    if fixture_type in self._fixtures:
                        count = self._apply_fixture_type(tenant, fixture_type)
                        results[fixture_type] = count
                        self.logger.info(f"Applied {count} {fixture_type} fixtures for tenant {tenant.name}")
                    else:
                        self.logger.warning(f"Unknown fixture type: {fixture_type}")
        
        return results
    
    def _apply_fixture_type(self, tenant, fixture_type: str) -> int:
        """Aplica um tipo específico de fixture"""
        fixtures = self._fixtures[fixture_type]
        count = 0
        
        if fixture_type == 'services':
            count = self._apply_services(fixtures)
        elif fixture_type == 'products':
            count = self._apply_products(fixtures)
        elif fixture_type == 'configurations':
            count = self._apply_configurations(tenant, fixtures)
        elif fixture_type == 'categories':
            count = self._apply_categories(fixtures)
        
        return count
    
    def _apply_services(self, services: List[Dict[str, Any]]) -> int:
        """Aplica fixtures de serviços"""
        from api.models import Servico
        
        count = 0
        for service_data in services:
            try:
                # Verificar se serviço já existe
                if not Servico.objects.filter(nome=service_data['nome']).exists():
                    Servico.objects.create(**service_data)
                    count += 1
            except Exception as e:
                self.logger.error(f"Error creating service {service_data['nome']}: {str(e)}")
        
        return count
    
    def _apply_products(self, products: List[Dict[str, Any]]) -> int:
        """Aplica fixtures de produtos"""
        from api.models import Produto
        
        count = 0
        for product_data in products:
            try:
                # Verificar se produto já existe
                if not Produto.objects.filter(nome=product_data['nome']).exists():
                    # Remover campos que não existem no modelo
                    clean_data = {k: v for k, v in product_data.items() if k != 'marca'}
                    Produto.objects.create(**clean_data)
                    count += 1
            except Exception as e:
                self.logger.error(f"Error creating product {product_data['nome']}: {str(e)}")
        
        return count
    
    def _apply_configurations(self, tenant, configurations: List[Dict[str, Any]]) -> int:
        """Aplica fixtures de configurações"""
        from .models import TenantConfiguration
        
        count = 0
        for config_data in configurations:
            try:
                # Verificar se configuração já existe
                if not TenantConfiguration.objects.filter(
                    tenant=tenant, 
                    config_key=config_data['key']
                ).exists():
                    TenantConfiguration.set_config(
                        tenant=tenant,
                        key=config_data['key'],
                        value=config_data['value'],
                        config_type=config_data['type'],
                        is_sensitive=config_data['sensitive']
                    )
                    count += 1
            except Exception as e:
                self.logger.error(f"Error creating configuration {config_data['key']}: {str(e)}")
        
        return count
    
    def _apply_categories(self, categories: List[Dict[str, Any]]) -> int:
        """Aplica fixtures de categorias (placeholder para futuras extensões)"""
        # Por enquanto, as categorias são hardcoded nos modelos
        # Esta função pode ser expandida no futuro se criarmos um modelo de Category
        return len(categories)
    
    def add_custom_fixture(self, fixture_type: str, fixtures: List[Dict[str, Any]]):
        """
        Adiciona fixtures customizados ao gerenciador.
        
        Args:
            fixture_type: Tipo do fixture
            fixtures: Lista de fixtures para adicionar
        """
        if fixture_type not in self._fixtures:
            self._fixtures[fixture_type] = []
        
        self._fixtures[fixture_type].extend(fixtures)
        self.logger.info(f"Added {len(fixtures)} custom {fixture_type} fixtures")
    
    def get_available_fixtures(self) -> Dict[str, int]:
        """
        Retorna informações sobre fixtures disponíveis.
        
        Returns:
            Dict com tipos de fixtures e quantidades
        """
        return {
            fixture_type: len(fixtures) 
            for fixture_type, fixtures in self._fixtures.items()
        }
    
    def validate_fixtures(self) -> Dict[str, List[str]]:
        """
        Valida todos os fixtures carregados.
        
        Returns:
            Dict com erros encontrados por tipo de fixture
        """
        errors = {}
        
        for fixture_type, fixtures in self._fixtures.items():
            type_errors = []
            
            if fixture_type == 'services':
                type_errors = self._validate_services(fixtures)
            elif fixture_type == 'products':
                type_errors = self._validate_products(fixtures)
            elif fixture_type == 'configurations':
                type_errors = self._validate_configurations(fixtures)
            
            if type_errors:
                errors[fixture_type] = type_errors
        
        return errors
    
    def _validate_services(self, services: List[Dict[str, Any]]) -> List[str]:
        """Valida fixtures de serviços"""
        errors = []
        required_fields = ['nome', 'descricao', 'preco', 'duracao_estimada']
        
        for i, service in enumerate(services):
            for field in required_fields:
                if field not in service:
                    errors.append(f"Service {i}: missing field '{field}'")
            
            if 'preco' in service and service['preco'] <= 0:
                errors.append(f"Service {i}: price must be positive")
        
        return errors
    
    def _validate_products(self, products: List[Dict[str, Any]]) -> List[str]:
        """Valida fixtures de produtos"""
        errors = []
        required_fields = ['nome', 'descricao', 'categoria', 'preco']
        
        for i, product in enumerate(products):
            for field in required_fields:
                if field not in product:
                    errors.append(f"Product {i}: missing field '{field}'")
            
            if 'preco' in product and product['preco'] <= 0:
                errors.append(f"Product {i}: price must be positive")
            
            if 'estoque' in product and product['estoque'] < 0:
                errors.append(f"Product {i}: stock cannot be negative")
        
        return errors
    
    def _validate_configurations(self, configurations: List[Dict[str, Any]]) -> List[str]:
        """Valida fixtures de configurações"""
        errors = []
        required_fields = ['key', 'value', 'type']
        
        for i, config in enumerate(configurations):
            for field in required_fields:
                if field not in config:
                    errors.append(f"Configuration {i}: missing field '{field}'")
        
        return errors


# Instância global do gerenciador de fixtures
tenant_fixture_manager = TenantFixtureManager()
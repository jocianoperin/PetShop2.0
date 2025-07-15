# Design - Sistema SaaS Multitenant para Gestão de Petshop

## Visão Geral

O sistema será transformado em uma arquitetura SaaS multitenant utilizando a estratégia "Schema por Tenant" para garantir isolamento forte de dados. A solução manterá a stack atual (Django + Next.js) com extensões para suporte multitenant, provisionamento automático e escalabilidade horizontal.

## Arquitetura

### Arquitetura de Alto Nível (C4 - Nível 2)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 Load Balancer                                   │
│                (nginx/ALB)                                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Frontend Cluster                                 │
│              (Next.js - Multiple Instances)                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Backend Cluster                                  │
│              (Django API - Multiple Instances)                  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Tenant Service  │  │ Auth Service    │  │ Provision Svc   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Database Cluster                                 │
│                (PostgreSQL)                                     │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ tenant_1_schema │  │ tenant_2_schema │  │ tenant_n_schema │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              shared_schema                                  │ │
│  │        (tenants, users, configurations)                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Arquitetura de Componentes (C4 - Nível 3)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Django Backend                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Middleware Layer                            │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   CORS      │ │    Auth     │ │   Tenant Resolution     │ │ │
│  │  │ Middleware  │ │ Middleware  │ │     Middleware          │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   API Layer                                 │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Tenant    │ │   Auth      │ │      Business           │ │ │
│  │  │   Views     │ │   Views     │ │      Views              │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Service Layer                               │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Tenant    │ │ Provisioning│ │    Business Logic       │ │ │
│  │  │  Service    │ │   Service   │ │     Services            │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  Data Layer                                 │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Tenant    │ │   Schema    │ │      ORM Models         │ │ │
│  │  │  Manager    │ │  Manager    │ │     (per tenant)        │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes e Interfaces

### 1. Tenant Resolution Middleware

**Responsabilidade:** Identificar o tenant atual baseado no request
**Interface:**
```python
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        tenant = self.resolve_tenant(request)
        request.tenant = tenant
        return self.get_response(request)
    
    def resolve_tenant(self, request) -> Tenant:
        # Resolve via subdomain, header ou token JWT
        pass
```

### 2. Tenant Manager

**Responsabilidade:** Gerenciar conexões de banco por tenant
**Interface:**
```python
class TenantManager:
    def get_connection(self, tenant_id: str) -> DatabaseConnection
    def create_schema(self, tenant_id: str) -> bool
    def migrate_schema(self, tenant_id: str) -> bool
    def backup_tenant(self, tenant_id: str) -> str
```

### 3. Provisioning Service

**Responsabilidade:** Criar novos tenants automaticamente
**Interface:**
```python
class ProvisioningService:
    def create_tenant(self, tenant_data: dict) -> Tenant
    def setup_schema(self, tenant: Tenant) -> bool
    def initialize_data(self, tenant: Tenant) -> bool
    def rollback_tenant(self, tenant: Tenant) -> bool
```

### 4. Tenant-Aware Models

**Responsabilidade:** Modelos que automaticamente filtram por tenant
**Interface:**
```python
class TenantAwareModel(models.Model):
    class Meta:
        abstract = True
    
    objects = TenantAwareManager()
    
    def save(self, *args, **kwargs):
        # Automaticamente associa ao tenant atual
        pass
```

## Modelo de Dados

### Schema Compartilhado (shared_schema)

```sql
-- Tabela de Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(63) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    plan_type VARCHAR(50) DEFAULT 'basic',
    max_users INTEGER DEFAULT 10,
    max_animals INTEGER DEFAULT 1000
);

-- Tabela de Usuários (compartilhada)
CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Configurações por Tenant
CREATE TABLE tenant_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, config_key)
);
```

### Schema por Tenant (tenant_xxx_schema)

Cada tenant terá seu próprio schema com as tabelas existentes:

```sql
-- Estrutura replicada para cada tenant
CREATE SCHEMA tenant_abc123;

-- Tabelas específicas do tenant (baseadas no modelo atual)
CREATE TABLE tenant_abc123.api_cliente (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telefone VARCHAR(20),
    endereco TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tenant_abc123.api_animal (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    especie VARCHAR(100),
    raca VARCHAR(100),
    peso DECIMAL(5,2),
    idade INTEGER,
    cliente_id INTEGER REFERENCES tenant_abc123.api_cliente(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Demais tabelas seguem o mesmo padrão...
```

### Diagrama ER Multitenant

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    tenants      │    │  tenant_users   │    │tenant_configs   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄──┤ tenant_id (FK)  │    │ tenant_id (FK)  │◄──┐
│ name            │    │ email           │    │ config_key      │   │
│ subdomain       │    │ password_hash   │    │ config_value    │   │
│ schema_name     │    │ first_name      │    └─────────────────┘   │
│ created_at      │    │ last_name       │                        │
│ is_active       │    │ role            │                        │
│ plan_type       │    │ is_active       │                        │
└─────────────────┘    └─────────────────┘                        │
                                                                  │
        │                                                         │
        │ (Schema per tenant)                                     │
        ▼                                                         │
┌─────────────────────────────────────────────────────────────────┼─┐
│                    tenant_xxx_schema                            │ │
│                                                                 │ │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │ │
│  │  api_cliente    │    │   api_animal    │    │ api_servico  │ │ │
│  ├─────────────────┤    ├─────────────────┤    ├──────────────┤ │ │
│  │ id (PK)         │◄──┤ cliente_id (FK) │    │ id (PK)      │ │ │
│  │ nome            │    │ nome            │    │ nome         │ │ │
│  │ email           │    │ especie         │    │ preco        │ │ │
│  │ telefone        │    │ raca            │    │ duracao      │ │ │
│  │ endereco        │    │ peso            │    └──────────────┘ │ │
│  └─────────────────┘    │ idade           │                     │ │
│                         └─────────────────┘                     │ │
└─────────────────────────────────────────────────────────────────┘ │
                                                                    │
                                                                    │
```

## Estratégia Multitenant

### Schema por Tenant

**Implementação:**
- Cada tenant possui um schema PostgreSQL dedicado
- Isolamento forte de dados por design
- Facilita backup/restore individual
- Permite customizações específicas

**Vantagens:**
- Isolamento completo de dados
- Facilita compliance (LGPD)
- Backup/restore granular
- Customizações por tenant

**Desvantagens:**
- Maior complexidade de gerenciamento
- Overhead de conexões
- Migrações mais complexas

### Isolamento de Dados

**Middleware de Resolução:**
```python
class TenantMiddleware:
    def resolve_tenant(self, request):
        # Método 1: Subdomain
        host = request.get_host()
        subdomain = host.split('.')[0]
        
        # Método 2: Header personalizado
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # Método 3: JWT Token
        token = request.headers.get('Authorization')
        tenant_id = self.extract_tenant_from_jwt(token)
        
        return Tenant.objects.get(subdomain=subdomain)
```

**Database Router:**
```python
class TenantDatabaseRouter:
    def db_for_read(self, model, **hints):
        if hasattr(model._meta, 'tenant_schema'):
            return f"tenant_{get_current_tenant().schema_name}"
        return 'default'
    
    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
```

### Provisionamento Automático

**Fluxo de Criação de Tenant:**

```
1. Usuário preenche formulário de cadastro
2. Sistema valida dados e disponibilidade
3. Cria registro na tabela 'tenants'
4. Gera schema_name único
5. Cria schema no PostgreSQL
6. Executa migrações no novo schema
7. Insere dados iniciais padrão
8. Cria usuário administrador do tenant
9. Envia email de confirmação
10. Redireciona para dashboard
```

**Implementação do Provisionamento:**
```python
class TenantProvisioningService:
    def create_tenant(self, registration_data):
        with transaction.atomic():
            # 1. Criar tenant
            tenant = Tenant.objects.create(
                name=registration_data['company_name'],
                subdomain=registration_data['subdomain'],
                schema_name=f"tenant_{uuid.uuid4().hex[:8]}"
            )
            
            # 2. Criar schema
            self.create_schema(tenant.schema_name)
            
            # 3. Executar migrações
            self.run_migrations(tenant.schema_name)
            
            # 4. Dados iniciais
            self.setup_initial_data(tenant)
            
            # 5. Usuário admin
            self.create_admin_user(tenant, registration_data)
            
            return tenant
```

## Tratamento de Erros

### Estratégias de Error Handling

**1. Tenant Not Found:**
```python
class TenantNotFoundError(Exception):
    def __init__(self, identifier):
        self.identifier = identifier
        super().__init__(f"Tenant not found: {identifier}")

# Middleware handling
def process_exception(self, request, exception):
    if isinstance(exception, TenantNotFoundError):
        return JsonResponse({
            'error': 'Tenant not found',
            'code': 'TENANT_NOT_FOUND'
        }, status=404)
```

**2. Schema Connection Errors:**
```python
class SchemaConnectionError(Exception):
    pass

# Service handling
def get_tenant_connection(self, tenant):
    try:
        return connections[f"tenant_{tenant.schema_name}"]
    except KeyError:
        raise SchemaConnectionError(f"Schema {tenant.schema_name} not accessible")
```

**3. Provisioning Failures:**
```python
def create_tenant_with_rollback(self, data):
    savepoint = transaction.savepoint()
    try:
        tenant = self.create_tenant(data)
        transaction.savepoint_commit(savepoint)
        return tenant
    except Exception as e:
        transaction.savepoint_rollback(savepoint)
        self.cleanup_failed_tenant(data.get('schema_name'))
        raise ProvisioningError(f"Failed to create tenant: {str(e)}")
```

## Estratégia de Testes

### Testes Unitários
- Testes isolados por componente
- Mocks para dependências externas
- Cobertura mínima de 80%

### Testes de Integração
- Testes de fluxo completo multitenant
- Validação de isolamento de dados
- Testes de provisionamento

### Testes de Carga
- Simulação de múltiplos tenants
- Testes de escalabilidade horizontal
- Benchmarks de performance

### Testes de Segurança
- Validação de isolamento entre tenants
- Testes de autorização
- Auditoria de logs de acesso

**Estrutura de Testes:**
```python
class MultitenantTestCase(TestCase):
    def setUp(self):
        self.tenant1 = self.create_test_tenant('tenant1')
        self.tenant2 = self.create_test_tenant('tenant2')
    
    def test_data_isolation(self):
        # Criar dados no tenant1
        with tenant_context(self.tenant1):
            cliente1 = Cliente.objects.create(nome='Cliente Tenant 1')
        
        # Verificar isolamento no tenant2
        with tenant_context(self.tenant2):
            self.assertEqual(Cliente.objects.count(), 0)
```

## Padrões de Design

### 1. Tenant Context Pattern
```python
@contextmanager
def tenant_context(tenant):
    old_tenant = getattr(local_storage, 'current_tenant', None)
    local_storage.current_tenant = tenant
    try:
        yield tenant
    finally:
        local_storage.current_tenant = old_tenant
```

### 2. Repository Pattern com Tenant
```python
class TenantAwareRepository:
    def __init__(self, tenant):
        self.tenant = tenant
    
    def find_all(self):
        with tenant_context(self.tenant):
            return self.model.objects.all()
```

### 3. Factory Pattern para Serviços
```python
class TenantServiceFactory:
    @staticmethod
    def create_service(service_type, tenant):
        services = {
            'cliente': ClienteService,
            'animal': AnimalService,
            'agendamento': AgendamentoService
        }
        return services[service_type](tenant)
```

Este design fornece uma base sólida para a implementação do sistema SaaS multitenant, mantendo a arquitetura atual enquanto adiciona as capacidades necessárias para suporte a múltiplos tenants com isolamento seguro de dados.
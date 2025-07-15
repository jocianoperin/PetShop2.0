# Sistema Multitenant - Petshop SaaS

Este módulo implementa a infraestrutura multitenant para o sistema de gestão de petshop, permitindo que múltiplos petshops operem de forma independente na mesma aplicação.

## Arquitetura

O sistema utiliza a estratégia "Schema por Tenant" para PostgreSQL e isolamento lógico para SQLite (desenvolvimento).

### Componentes Principais

1. **Modelos**
   - `Tenant`: Representa um petshop (tenant)
   - `TenantUser`: Usuários específicos de cada tenant
   - `TenantConfiguration`: Configurações personalizadas por tenant

2. **Middleware**
   - `TenantMiddleware`: Resolve o tenant atual baseado em subdomínio, header ou parâmetro
   - `TenantSchemaMiddleware`: Garante que o schema correto está sendo usado

3. **Utilitários**
   - `tenant_context()`: Context manager para operações em tenant específico
   - `get_current_tenant()`: Obtém o tenant atual
   - Funções para gerenciamento de schemas

4. **Database Router**
   - `TenantDatabaseRouter`: Roteia operações de banco para o schema correto

## Configuração

### 1. Configuração do Banco de Dados

Para **desenvolvimento** (SQLite):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Para **produção** (PostgreSQL):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'petshop_multitenant',
        'USER': 'petshop_user',
        'PASSWORD': 'sua_senha',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=public'
        },
    }
}
```

### 2. Middleware

Adicione os middlewares na ordem correta:

```python
MIDDLEWARE = [
    # ... outros middlewares
    'tenants.middleware.TenantMiddleware',
    'tenants.middleware.TenantSchemaMiddleware',
    # ... outros middlewares
]
```

### 3. Database Router

```python
DATABASE_ROUTERS = ['tenants.db_router.TenantDatabaseRouter']
```

## Uso

### Criando um Tenant

```python
from tenants.models import Tenant

tenant = Tenant.objects.create(
    name="Petshop ABC",
    subdomain="abc",
    plan_type="basic"
)
```

### Executando Operações em um Tenant

```python
from tenants.utils import tenant_context

with tenant_context(tenant):
    # Todas as operações de banco serão executadas no contexto do tenant
    clientes = Cliente.objects.all()
    animal = Animal.objects.create(nome="Rex", especie="Cão")
```

### Obtendo o Tenant Atual

```python
from tenants.utils import get_current_tenant

def minha_view(request):
    tenant = get_current_tenant()
    if tenant:
        # Lógica específica do tenant
        pass
```

### Decorador para Views

```python
from tenants.utils import tenant_required

@tenant_required
def minha_view(request):
    tenant = get_current_tenant()
    # View que requer tenant válido
```

## Resolução de Tenant

O sistema resolve o tenant atual através de:

1. **Subdomínio**: `abc.exemplo.com` → tenant com subdomain="abc"
2. **Header HTTP**: `X-Tenant-ID: uuid-do-tenant`
3. **Parâmetro de Query**: `?tenant=abc` (apenas desenvolvimento)

## Comandos de Gerenciamento

### Criar Schema para Tenant

```bash
# Para um tenant específico
python manage.py create_tenant_schema --tenant-id <uuid>
python manage.py create_tenant_schema --subdomain <subdomain>

# Para todos os tenants
python manage.py create_tenant_schema --all
```

### Executar Migrações em Tenant

```bash
# Para um tenant específico
python manage.py migrate_tenant --tenant-id <uuid>
python manage.py migrate_tenant --subdomain <subdomain>

# Para todos os tenants
python manage.py migrate_tenant --all
```

## Configurações por Tenant

```python
from tenants.models import TenantConfiguration

# Definir configuração
TenantConfiguration.set_config(tenant, "theme_color", "#007bff")

# Obter configuração
color = TenantConfiguration.get_config(tenant, "theme_color", "#ffffff")
```

## Modelos Tenant-Aware

Para tornar um modelo existente tenant-aware:

```python
from tenants.base import TenantAwareModel

class MeuModelo(TenantAwareModel):
    nome = models.CharField(max_length=100)
    # ... outros campos
```

Ou usando decorator:

```python
from tenants.base import tenant_aware_model

@tenant_aware_model
class MeuModelo(models.Model):
    nome = models.CharField(max_length=100)
```

## Segurança

- Isolamento automático de dados por tenant
- Validações para prevenir acesso cruzado entre tenants
- Logs de auditoria com identificação de tenant
- Middleware de segurança para validar contexto de tenant

## Desenvolvimento vs Produção

### SQLite (Desenvolvimento)
- Isolamento lógico através de middleware
- Sem schemas reais
- Ideal para desenvolvimento e testes

### PostgreSQL (Produção)
- Schemas reais por tenant
- Isolamento físico de dados
- Melhor performance e segurança

## Testes

Execute os testes da infraestrutura:

```bash
python backend/test_multitenant.py
```

## Monitoramento

O sistema inclui:
- Logs específicos por tenant
- Métricas de performance
- Auditoria de operações
- Dashboard administrativo

## Próximos Passos

1. Implementar provisionamento automático
2. Adicionar APIs de registro de tenant
3. Criar sistema de migração de dados
4. Implementar backup/restore por tenant
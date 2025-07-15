from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Tenant, TenantUser, TenantConfiguration


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin para gerenciamento de Tenants"""
    
    list_display = [
        'name', 'subdomain', 'schema_name', 'plan_type', 
        'is_active', 'user_count', 'created_at'
    ]
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'schema_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'schema_info']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'subdomain', 'schema_name')
        }),
        ('Configurações do Plano', {
            'fields': ('plan_type', 'max_users', 'max_animals')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at', 'schema_info'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        """Retorna o número de usuários do tenant"""
        return obj.users.count()
    user_count.short_description = 'Usuários'
    
    def schema_info(self, obj):
        """Mostra informações do schema do tenant"""
        from .utils import list_tenant_tables, get_tenant_database_size
        
        tables = list_tenant_tables(obj)
        size = get_tenant_database_size(obj)
        
        info = f"""
        <strong>Schema:</strong> {obj.schema_name}<br>
        <strong>Tabelas:</strong> {len(tables)}<br>
        <strong>Tamanho:</strong> {size or 'N/A'} bytes<br>
        """
        
        if tables:
            info += f"<strong>Lista de Tabelas:</strong><br>"
            info += "<br>".join([f"• {table}" for table in tables[:10]])
            if len(tables) > 10:
                info += f"<br>... e mais {len(tables) - 10} tabelas"
        
        return mark_safe(info)
    schema_info.short_description = 'Informações do Schema'
    
    actions = ['activate_tenants', 'deactivate_tenants', 'create_schemas']
    
    def activate_tenants(self, request, queryset):
        """Ativa tenants selecionados"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tenant(s) ativado(s) com sucesso.')
    activate_tenants.short_description = 'Ativar tenants selecionados'
    
    def deactivate_tenants(self, request, queryset):
        """Desativa tenants selecionados"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tenant(s) desativado(s) com sucesso.')
    deactivate_tenants.short_description = 'Desativar tenants selecionados'
    
    def create_schemas(self, request, queryset):
        """Cria schemas para tenants selecionados"""
        from .utils import create_tenant_schema
        
        created = 0
        for tenant in queryset:
            if create_tenant_schema(tenant):
                created += 1
        
        self.message_user(request, f'Schema criado para {created} tenant(s).')
    create_schemas.short_description = 'Criar schemas para tenants selecionados'


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    """Admin para gerenciamento de Usuários por Tenant"""
    
    list_display = [
        'email', 'tenant_name', 'full_name', 'role', 
        'is_active', 'created_at', 'last_login'
    ]
    list_filter = ['role', 'is_active', 'tenant__plan_type', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'last_login']
    
    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('id', 'email', 'first_name', 'last_name')
        }),
        ('Tenant e Permissões', {
            'fields': ('tenant', 'role')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        """Retorna o nome do tenant"""
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'
    
    def get_queryset(self, request):
        """Otimiza queries incluindo dados do tenant"""
        return super().get_queryset(request).select_related('tenant')


class TenantConfigurationInline(admin.TabularInline):
    """Inline para configurações do tenant"""
    model = TenantConfiguration
    extra = 0
    fields = ['config_key', 'config_value']


@admin.register(TenantConfiguration)
class TenantConfigurationAdmin(admin.ModelAdmin):
    """Admin para configurações por tenant"""
    
    list_display = ['tenant_name', 'config_key', 'config_value_preview', 'updated_at']
    list_filter = ['tenant__plan_type', 'config_key', 'updated_at']
    search_fields = ['tenant__name', 'config_key', 'config_value']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Configuração', {
            'fields': ('tenant', 'config_key', 'config_value')
        }),
        ('Informações do Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        """Retorna o nome do tenant"""
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'
    
    def config_value_preview(self, obj):
        """Mostra preview do valor da configuração"""
        value = obj.config_value
        if len(value) > 50:
            return f"{value[:50]}..."
        return value
    config_value_preview.short_description = 'Valor'
    
    def get_queryset(self, request):
        """Otimiza queries incluindo dados do tenant"""
        return super().get_queryset(request).select_related('tenant')


# Adiciona configurações inline ao TenantAdmin
TenantAdmin.inlines = [TenantConfigurationInline]


# Customização do Admin Site
admin.site.site_header = 'Petshop Multitenant - Administração'
admin.site.site_title = 'Petshop Admin'
admin.site.index_title = 'Painel de Administração Multitenant'
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Configuração da aplicação Tenants"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'
    verbose_name = 'Gerenciamento de Tenants'
    
    def ready(self):
        """Executado quando a aplicação está pronta"""
        # Importa sinais se necessário
        # from . import signals
        pass
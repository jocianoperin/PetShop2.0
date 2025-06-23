from django.contrib import admin
from .models import Cliente, Animal, Servico, Agendamento, Produto, Venda, ItemVenda


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'data_cadastro')
    list_filter = ('data_cadastro',)
    search_fields = ('nome', 'email', 'telefone')
    ordering = ('nome',)


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'especie', 'raca', 'cliente', 'data_cadastro')
    list_filter = ('especie', 'data_cadastro')
    search_fields = ('nome', 'raca', 'cliente__nome')
    ordering = ('nome',)


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'duracao_estimada', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    ordering = ('nome',)


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('animal', 'servico', 'data_hora', 'status', 'valor_final')
    list_filter = ('status', 'data_hora', 'servico')
    search_fields = ('animal__nome', 'animal__cliente__nome', 'servico__nome')
    ordering = ('-data_hora',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'estoque', 'estoque_baixo', 'ativo')
    list_filter = ('categoria', 'ativo', 'data_cadastro')
    search_fields = ('nome', 'descricao')
    ordering = ('nome',)


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data_venda', 'valor_total', 'desconto')
    list_filter = ('data_venda',)
    search_fields = ('cliente__nome',)
    ordering = ('-data_venda',)
    inlines = [ItemVendaInline]


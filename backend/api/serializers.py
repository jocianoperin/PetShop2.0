from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import Cliente, Animal, Servico, Agendamento, Produto, Venda, ItemVenda

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ('data_cadastro',)


class AnimalSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    
    class Meta:
        model = Animal
        fields = '__all__'
        read_only_fields = ('data_cadastro',)


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = '__all__'


class AgendamentoSerializer(serializers.ModelSerializer):
    animal_nome = serializers.CharField(source='animal.nome', read_only=True)
    cliente_nome = serializers.CharField(source='animal.cliente.nome', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    servico_preco = serializers.DecimalField(source='servico.preco', max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = Agendamento
        fields = '__all__'
        read_only_fields = ('data_criacao', 'data_atualizacao')


class ProdutoSerializer(serializers.ModelSerializer):
    estoque_baixo = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ('data_cadastro',)


class ItemVendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemVenda
        fields = '__all__'


class VendaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ('data_venda',)


class VendaCreateSerializer(serializers.ModelSerializer):
    itens = ItemVendaSerializer(many=True)
    
    class Meta:
        model = Venda
        fields = ['cliente', 'desconto', 'observacoes', 'itens']
    
    def create(self, validated_data):
        itens_data = validated_data.pop('itens')
        
        # Calcular valor total
        valor_total = 0
        for item_data in itens_data:
            valor_total += item_data['quantidade'] * item_data['preco_unitario']
        
        # Aplicar desconto
        desconto = validated_data.get('desconto', 0)
        valor_total -= desconto
        
        venda = Venda.objects.create(valor_total=valor_total, **validated_data)
        
        # Criar itens da venda
        for item_data in itens_data:
            ItemVenda.objects.create(venda=venda, **item_data)
            
            # Atualizar estoque
            produto = item_data['produto']
            produto.estoque -= item_data['quantidade']
            produto.save()
        
        return venda


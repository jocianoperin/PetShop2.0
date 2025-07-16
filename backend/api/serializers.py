from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import models
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
    """
    Serializer para Cliente com suporte a tenant.
    Inclui validações específicas de tenant e campos calculados.
    """
    total_animais = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ('data_cadastro', 'tenant')
    
    def get_total_animais(self, obj):
        """Retorna o número total de animais do cliente"""
        return obj.animais.count()
    
    def validate_email(self, value):
        """
        Valida se o email é único dentro do tenant atual.
        """
        if not value:
            return value
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de email."
            )
        
        # Verificar se já existe cliente com este email no tenant
        queryset = Cliente.objects.filter(email=value)
        
        # Se estamos atualizando, excluir o próprio objeto da verificação
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um cliente com este email no seu petshop."
            )
        
        return value
    
    def validate(self, attrs):
        """
        Validações gerais do cliente.
        """
        attrs = super().validate(attrs)
        
        # Validar se o tenant está ativo
        tenant = self.context.get('tenant')
        if tenant and not tenant.is_active:
            raise serializers.ValidationError(
                "Não é possível criar/atualizar clientes em tenant inativo."
            )
        
        return attrs
    
    def create(self, validated_data):
        """
        Cria cliente associado ao tenant atual.
        """
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para criar cliente."
            )
        
        # O tenant será definido automaticamente pelo TenantAwareModel
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """
        Customiza a representação do cliente incluindo informações adicionais.
        """
        data = super().to_representation(instance)
        
        # Adicionar informações úteis se solicitado
        request = self.context.get('request')
        if request and request.query_params.get('include_stats') == 'true':
            # Incluir estatísticas do cliente
            data['estatisticas'] = {
                'total_agendamentos': instance.animais.aggregate(
                    total=models.Count('agendamento')
                )['total'] or 0,
                'total_vendas': getattr(instance, 'venda_set', instance.vendas).count(),
                'ultimo_agendamento': None,
                'ultima_venda': None
            }
            
            # Último agendamento
            ultimo_agendamento = Agendamento.objects.filter(
                animal__cliente=instance
            ).order_by('-data_hora').first()
            
            if ultimo_agendamento:
                data['estatisticas']['ultimo_agendamento'] = {
                    'data': ultimo_agendamento.data_hora,
                    'servico': ultimo_agendamento.servico.nome,
                    'status': ultimo_agendamento.status
                }
            
            # Última venda
            ultima_venda = getattr(instance, 'venda_set', instance.vendas).order_by('-data_venda').first()
            if ultima_venda:
                data['estatisticas']['ultima_venda'] = {
                    'data': ultima_venda.data_venda,
                    'valor': ultima_venda.valor_total
                }
        
        return data


class AnimalSerializer(serializers.ModelSerializer):
    """
    Serializer para Animal com suporte a tenant.
    Inclui validações de relacionamento cliente-animal dentro do tenant.
    """
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    cliente_email = serializers.CharField(source='cliente.email', read_only=True)
    cliente_telefone = serializers.CharField(source='cliente.telefone', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    idade_anos = serializers.SerializerMethodField()
    total_agendamentos = serializers.SerializerMethodField()
    
    class Meta:
        model = Animal
        fields = '__all__'
        read_only_fields = ('data_cadastro', 'tenant')
    
    def get_idade_anos(self, obj):
        """Calcula a idade do animal em anos"""
        if obj.data_nascimento:
            from datetime import date
            today = date.today()
            age = today.year - obj.data_nascimento.year
            if today.month < obj.data_nascimento.month or \
               (today.month == obj.data_nascimento.month and today.day < obj.data_nascimento.day):
                age -= 1
            return age
        return None
    
    def get_total_agendamentos(self, obj):
        """Retorna o número total de agendamentos do animal"""
        return obj.agendamento_set.count()
    
    def validate_cliente(self, value):
        """
        Valida se o cliente pertence ao tenant atual.
        """
        if not value:
            raise serializers.ValidationError("Cliente é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de cliente."
            )
        
        # Verificar se o cliente pertence ao tenant atual
        if value.tenant != tenant:
            raise serializers.ValidationError(
                "O cliente especificado não pertence ao seu petshop."
            )
        
        return value
    
    def validate_data_nascimento(self, value):
        """
        Valida se a data de nascimento é válida.
        """
        if value:
            from datetime import date
            if value > date.today():
                raise serializers.ValidationError(
                    "A data de nascimento não pode ser no futuro."
                )
            
            # Verificar se a data não é muito antiga (mais de 50 anos)
            if (date.today() - value).days > 50 * 365:
                raise serializers.ValidationError(
                    "A data de nascimento parece muito antiga. Verifique se está correta."
                )
        
        return value
    
    def validate_peso(self, value):
        """
        Valida se o peso é um valor razoável.
        """
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError(
                    "O peso deve ser maior que zero."
                )
            
            if value > 1000:  # 1000kg parece excessivo para um animal doméstico
                raise serializers.ValidationError(
                    "O peso parece muito alto. Verifique se está correto."
                )
        
        return value
    
    def validate(self, attrs):
        """
        Validações gerais do animal.
        """
        attrs = super().validate(attrs)
        
        # Validar se o tenant está ativo
        tenant = self.context.get('tenant')
        if tenant and not tenant.is_active:
            raise serializers.ValidationError(
                "Não é possível criar/atualizar animais em tenant inativo."
            )
        
        # Validar combinação espécie/raça se necessário
        especie = attrs.get('especie')
        raca = attrs.get('raca', '').strip()
        
        if especie and raca:
            # Aqui você pode adicionar validações específicas de raça por espécie
            # Por exemplo, verificar se a raça é válida para a espécie
            pass
        
        return attrs
    
    def create(self, validated_data):
        """
        Cria animal associado ao tenant atual.
        """
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para criar animal."
            )
        
        # O tenant será definido automaticamente pelo TenantAwareModel
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """
        Customiza a representação do animal incluindo informações adicionais.
        """
        data = super().to_representation(instance)
        
        # Adicionar informações úteis se solicitado
        request = self.context.get('request')
        if request and request.query_params.get('include_stats') == 'true':
            # Incluir estatísticas do animal
            data['estatisticas'] = {
                'total_agendamentos': instance.agendamento_set.count(),
                'agendamentos_concluidos': instance.agendamento_set.filter(
                    status='concluido'
                ).count(),
                'ultimo_agendamento': None,
                'proximo_agendamento': None
            }
            
            # Último agendamento
            ultimo_agendamento = instance.agendamento_set.order_by('-data_hora').first()
            if ultimo_agendamento:
                data['estatisticas']['ultimo_agendamento'] = {
                    'data': ultimo_agendamento.data_hora,
                    'servico': ultimo_agendamento.servico.nome,
                    'status': ultimo_agendamento.status
                }
            
            # Próximo agendamento
            from datetime import datetime
            proximo_agendamento = instance.agendamento_set.filter(
                data_hora__gte=datetime.now(),
                status__in=['agendado', 'confirmado']
            ).order_by('data_hora').first()
            
            if proximo_agendamento:
                data['estatisticas']['proximo_agendamento'] = {
                    'data': proximo_agendamento.data_hora,
                    'servico': proximo_agendamento.servico.nome,
                    'status': proximo_agendamento.status
                }
        
        return data


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = '__all__'


class AgendamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para Agendamento com suporte a tenant.
    Inclui validações de relacionamento e conflitos dentro do tenant.
    """
    animal_nome = serializers.CharField(source='animal.nome', read_only=True)
    cliente_nome = serializers.CharField(source='animal.cliente.nome', read_only=True)
    cliente_telefone = serializers.CharField(source='animal.cliente.telefone', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    servico_preco = serializers.DecimalField(source='servico.preco', max_digits=8, decimal_places=2, read_only=True)
    servico_duracao = serializers.DurationField(source='servico.duracao_estimada', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Agendamento
        fields = '__all__'
        read_only_fields = ('data_criacao', 'data_atualizacao', 'tenant')
    
    def validate_animal(self, value):
        """
        Valida se o animal pertence ao tenant atual.
        """
        if not value:
            raise serializers.ValidationError("Animal é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de animal."
            )
        
        # Verificar se o animal pertence ao tenant atual
        if value.tenant != tenant:
            raise serializers.ValidationError(
                "O animal especificado não pertence ao seu petshop."
            )
        
        return value
    
    def validate_servico(self, value):
        """
        Valida se o serviço pertence ao tenant atual.
        """
        if not value:
            raise serializers.ValidationError("Serviço é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de serviço."
            )
        
        # Verificar se o serviço pertence ao tenant atual
        if value.tenant != tenant:
            raise serializers.ValidationError(
                "O serviço especificado não pertence ao seu petshop."
            )
        
        # Verificar se o serviço está ativo
        if not value.ativo:
            raise serializers.ValidationError(
                "O serviço especificado não está ativo."
            )
        
        return value
    
    def validate_data_hora(self, value):
        """
        Valida se a data/hora do agendamento é válida.
        """
        if value:
            from datetime import datetime, timedelta
            
            # Não permitir agendamentos no passado (exceto para atualizações)
            if not self.instance and value < datetime.now():
                raise serializers.ValidationError(
                    "Não é possível agendar para datas/horários no passado."
                )
            
            # Não permitir agendamentos muito distantes no futuro (1 ano)
            limite_futuro = datetime.now() + timedelta(days=365)
            if value > limite_futuro:
                raise serializers.ValidationError(
                    "Não é possível agendar com mais de 1 ano de antecedência."
                )
            
            # Verificar horário comercial (exemplo: 8h às 18h)
            if value.hour < 8 or value.hour >= 18:
                raise serializers.ValidationError(
                    "Agendamentos devem ser feitos entre 8h e 18h."
                )
            
            # Não permitir agendamentos aos domingos
            if value.weekday() == 6:  # 6 = domingo
                raise serializers.ValidationError(
                    "Não é possível agendar aos domingos."
                )
        
        return value
    
    def validate(self, attrs):
        """
        Validações gerais do agendamento.
        """
        attrs = super().validate(attrs)
        
        # Validar se o tenant está ativo
        tenant = self.context.get('tenant')
        if tenant and not tenant.is_active:
            raise serializers.ValidationError(
                "Não é possível criar/atualizar agendamentos em tenant inativo."
            )
        
        # Validar relacionamento animal-cliente dentro do tenant
        animal = attrs.get('animal')
        if animal:
            if not hasattr(animal, 'cliente') or not animal.cliente:
                raise serializers.ValidationError({
                    'animal': 'O animal deve ter um cliente associado.'
                })
            
            # Verificar se animal e cliente pertencem ao mesmo tenant
            if animal.tenant != animal.cliente.tenant:
                raise serializers.ValidationError({
                    'animal': 'Inconsistência de dados: animal e cliente em tenants diferentes.'
                })
        
        # Validar conflitos de horário (será feito na view também)
        data_hora = attrs.get('data_hora')
        servico = attrs.get('servico')
        
        if data_hora and servico:
            # Esta validação será complementada na view
            pass
        
        return attrs
    
    def create(self, validated_data):
        """
        Cria agendamento associado ao tenant atual.
        """
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para criar agendamento."
            )
        
        # O tenant será definido automaticamente pelo TenantAwareModel
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """
        Customiza a representação do agendamento incluindo informações adicionais.
        """
        data = super().to_representation(instance)
        
        # Adicionar informações úteis se solicitado
        request = self.context.get('request')
        if request and request.query_params.get('include_details') == 'true':
            # Incluir detalhes adicionais
            data['detalhes'] = {
                'animal_especie': instance.animal.especie,
                'animal_raca': instance.animal.raca,
                'cliente_email': instance.animal.cliente.email,
                'servico_descricao': instance.servico.descricao,
                'valor_estimado': instance.servico.preco,
                'tempo_estimado': str(instance.servico.duracao_estimada),
            }
            
            # Calcular tempo até o agendamento
            from datetime import datetime
            if instance.data_hora > datetime.now():
                tempo_restante = instance.data_hora - datetime.now()
                data['detalhes']['tempo_ate_agendamento'] = {
                    'dias': tempo_restante.days,
                    'horas': tempo_restante.seconds // 3600,
                    'minutos': (tempo_restante.seconds % 3600) // 60
                }
            
            # Histórico de agendamentos do animal
            agendamentos_anteriores = Agendamento.objects.filter(
                animal=instance.animal,
                status='concluido'
            ).count()
            
            data['detalhes']['agendamentos_anteriores'] = agendamentos_anteriores
        
        return data


class ProdutoSerializer(serializers.ModelSerializer):
    """
    Serializer para Produto com suporte a tenant.
    Inclui validações de estoque e controle por tenant.
    """
    estoque_baixo = serializers.BooleanField(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    valor_total_estoque = serializers.SerializerMethodField()
    
    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ('data_cadastro', 'tenant')
    
    def get_valor_total_estoque(self, obj):
        """Calcula o valor total do estoque (preço * quantidade)"""
        return obj.preco * obj.estoque
    
    def validate_nome(self, value):
        """
        Valida se o nome do produto é único dentro do tenant atual.
        """
        if not value:
            raise serializers.ValidationError("Nome é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de nome."
            )
        
        # Verificar se já existe produto com este nome no tenant
        queryset = Produto.objects.filter(nome__iexact=value)
        
        # Se estamos atualizando, excluir o próprio objeto da verificação
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um produto com este nome no seu estoque."
            )
        
        return value
    
    def validate_preco(self, value):
        """
        Valida se o preço é um valor válido.
        """
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError(
                    "O preço deve ser maior que zero."
                )
            
            if value > 999999.99:  # Limite máximo razoável
                raise serializers.ValidationError(
                    "O preço parece muito alto. Verifique se está correto."
                )
        
        return value
    
    def validate_estoque(self, value):
        """
        Valida se o estoque é um valor válido.
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "O estoque não pode ser negativo."
                )
            
            if value > 999999:  # Limite máximo razoável
                raise serializers.ValidationError(
                    "A quantidade em estoque parece muito alta. Verifique se está correta."
                )
        
        return value
    
    def validate_estoque_minimo(self, value):
        """
        Valida se o estoque mínimo é um valor válido.
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "O estoque mínimo não pode ser negativo."
                )
            
            if value > 1000:  # Limite máximo razoável
                raise serializers.ValidationError(
                    "O estoque mínimo parece muito alto. Verifique se está correto."
                )
        
        return value
    
    def validate(self, attrs):
        """
        Validações gerais do produto.
        """
        attrs = super().validate(attrs)
        
        # Validar se o tenant está ativo
        tenant = self.context.get('tenant')
        if tenant and not tenant.is_active:
            raise serializers.ValidationError(
                "Não é possível criar/atualizar produtos em tenant inativo."
            )
        
        # Validar relação entre estoque e estoque mínimo
        estoque = attrs.get('estoque')
        estoque_minimo = attrs.get('estoque_minimo')
        
        if estoque is not None and estoque_minimo is not None:
            if estoque_minimo > estoque:
                # Apenas avisar, não bloquear
                pass  # Pode ser que o estoque esteja realmente baixo
        
        return attrs
    
    def create(self, validated_data):
        """
        Cria produto associado ao tenant atual.
        """
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para criar produto."
            )
        
        # O tenant será definido automaticamente pelo TenantAwareModel
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """
        Customiza a representação do produto incluindo informações adicionais.
        """
        data = super().to_representation(instance)
        
        # Adicionar informações úteis se solicitado
        request = self.context.get('request')
        if request and request.query_params.get('include_stats') == 'true':
            # Incluir estatísticas do produto
            data['estatisticas'] = {
                'valor_total_estoque': instance.preco * instance.estoque,
                'estoque_baixo': instance.estoque_baixo,
                'percentual_estoque': (
                    (instance.estoque / instance.estoque_minimo * 100) 
                    if instance.estoque_minimo > 0 else 100
                ),
                'vendas_mes_atual': 0,  # Implementar quando tiver histórico de vendas
                'ultima_entrada': None,  # Implementar quando tiver histórico de movimentações
            }
            
            # Calcular vendas do mês atual (se houver ItemVenda relacionado)
            try:
                from datetime import datetime
                inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                vendas_mes = ItemVenda.objects.filter(
                    produto=instance,
                    venda__data_venda__gte=inicio_mes
                ).aggregate(
                    total_vendido=models.Sum('quantidade')
                )['total_vendido'] or 0
                
                data['estatisticas']['vendas_mes_atual'] = vendas_mes
                
            except Exception:
                # Se não conseguir calcular, manter 0
                pass
        
        return data


class ItemVendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemVenda
        fields = '__all__'


class VendaSerializer(serializers.ModelSerializer):
    """
    Serializer para Venda com suporte a tenant.
    Inclui informações financeiras isoladas por tenant.
    """
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    cliente_email = serializers.CharField(source='cliente.email', read_only=True)
    cliente_telefone = serializers.CharField(source='cliente.telefone', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    valor_liquido = serializers.SerializerMethodField()
    total_itens = serializers.SerializerMethodField()
    
    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ('data_venda', 'tenant')
    
    def get_valor_liquido(self, obj):
        """Calcula o valor líquido (valor total - desconto)"""
        return obj.valor_total - obj.desconto
    
    def get_total_itens(self, obj):
        """Retorna o total de itens na venda"""
        return obj.itens.aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0
    
    def validate_cliente(self, value):
        """
        Valida se o cliente pertence ao tenant atual.
        """
        if not value:
            raise serializers.ValidationError("Cliente é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de cliente."
            )
        
        # Verificar se o cliente pertence ao tenant atual
        if value.tenant != tenant:
            raise serializers.ValidationError(
                "O cliente especificado não pertence ao seu petshop."
            )
        
        return value
    
    def validate_desconto(self, value):
        """
        Valida se o desconto é um valor válido.
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "O desconto não pode ser negativo."
                )
            
            if value > 99999.99:  # Limite máximo razoável
                raise serializers.ValidationError(
                    "O desconto parece muito alto. Verifique se está correto."
                )
        
        return value
    
    def validate(self, attrs):
        """
        Validações gerais da venda.
        """
        attrs = super().validate(attrs)
        
        # Validar se o tenant está ativo
        tenant = self.context.get('tenant')
        if tenant and not tenant.is_active:
            raise serializers.ValidationError(
                "Não é possível criar/atualizar vendas em tenant inativo."
            )
        
        return attrs


class VendaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de Venda com suporte a tenant.
    Inclui validações de estoque e cálculos automáticos.
    """
    itens = ItemVendaSerializer(many=True)
    
    class Meta:
        model = Venda
        fields = ['cliente', 'desconto', 'observacoes', 'itens']
    
    def validate_cliente(self, value):
        """
        Valida se o cliente pertence ao tenant atual.
        """
        if not value:
            raise serializers.ValidationError("Cliente é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de cliente."
            )
        
        # Verificar se o cliente pertence ao tenant atual
        if value.tenant != tenant:
            raise serializers.ValidationError(
                "O cliente especificado não pertence ao seu petshop."
            )
        
        return value
    
    def validate_itens(self, value):
        """
        Valida os itens da venda.
        """
        if not value:
            raise serializers.ValidationError("Pelo menos um item é obrigatório.")
        
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para validação de itens."
            )
        
        # Validar cada item
        for item_data in value:
            produto = item_data.get('produto')
            quantidade = item_data.get('quantidade', 0)
            
            # Verificar se o produto pertence ao tenant atual
            if produto and produto.tenant != tenant:
                raise serializers.ValidationError(
                    f"O produto '{produto.nome}' não pertence ao seu estoque."
                )
            
            # Verificar se há estoque suficiente
            if produto and quantidade > produto.estoque:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para '{produto.nome}'. "
                    f"Disponível: {produto.estoque}, Solicitado: {quantidade}"
                )
            
            # Verificar se o produto está ativo
            if produto and not produto.ativo:
                raise serializers.ValidationError(
                    f"O produto '{produto.nome}' não está ativo."
                )
        
        return value
    
    def validate(self, attrs):
        """
        Validações gerais da venda.
        """
        attrs = super().validate(attrs)
        
        # Validar se o tenant está ativo
        tenant = self.context.get('tenant')
        if tenant and not tenant.is_active:
            raise serializers.ValidationError(
                "Não é possível criar vendas em tenant inativo."
            )
        
        # Validar se o desconto não é maior que o valor total
        itens_data = attrs.get('itens', [])
        desconto = attrs.get('desconto', 0)
        
        # Calcular valor total dos itens
        valor_total_itens = sum(
            item['quantidade'] * item['preco_unitario'] 
            for item in itens_data
        )
        
        if desconto > valor_total_itens:
            raise serializers.ValidationError({
                'desconto': 'O desconto não pode ser maior que o valor total dos itens.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        Cria venda com validações de tenant e atualização de estoque.
        """
        tenant = self.context.get('tenant')
        if not tenant:
            from tenants.utils import get_current_tenant
            tenant = get_current_tenant()
        
        if not tenant:
            raise serializers.ValidationError(
                "Tenant requerido para criar venda."
            )
        
        itens_data = validated_data.pop('itens')
        
        # Calcular valor total
        valor_total = 0
        for item_data in itens_data:
            valor_total += item_data['quantidade'] * item_data['preco_unitario']
        
        # Aplicar desconto
        desconto = validated_data.get('desconto', 0)
        valor_total -= desconto
        
        # Criar venda (o tenant será definido automaticamente pelo TenantAwareModel)
        venda = Venda.objects.create(valor_total=valor_total, **validated_data)
        
        # Criar itens da venda e atualizar estoque
        for item_data in itens_data:
            # Criar item da venda
            ItemVenda.objects.create(venda=venda, **item_data)
            
            # Atualizar estoque do produto
            produto = item_data['produto']
            quantidade_vendida = item_data['quantidade']
            
            # Verificar novamente o estoque (por segurança)
            if produto.estoque < quantidade_vendida:
                # Reverter a venda se não há estoque suficiente
                venda.delete()
                raise serializers.ValidationError(
                    f"Estoque insuficiente para '{produto.nome}'. "
                    f"Disponível: {produto.estoque}, Solicitado: {quantidade_vendida}"
                )
            
            # Reduzir estoque
            produto.estoque -= quantidade_vendida
            produto.save()
            
            # Log da movimentação de estoque
            print(f"ESTOQUE - Produto: {produto.nome}, Saída: {quantidade_vendida}, "
                  f"Estoque atual: {produto.estoque}")
        
        return venda


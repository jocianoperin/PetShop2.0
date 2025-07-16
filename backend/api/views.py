from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Cliente, Animal, Servico, Agendamento, Produto, Venda
from .serializers import (
    ClienteSerializer, AnimalSerializer, ServicoSerializer,
    AgendamentoSerializer, ProdutoSerializer, VendaSerializer, 
    VendaCreateSerializer, UserSerializer
)
from tenants.utils import get_current_tenant, tenant_required
from tenants.permissions import TenantPermissionMixin

User = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(
            {'error': 'Credenciais inválidas'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout realizado com sucesso'})


class UserCreateView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        # Se for o primeiro usuário, definir como superusuário
        if User.objects.count() == 0:
            request.data['is_staff'] = True
            request.data['is_superuser'] = True
            
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class ClienteViewSet(TenantPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de clientes com isolamento por tenant.
    
    Funcionalidades:
    - Filtros automáticos por tenant
    - Validações de acesso por tenant
    - Busca por nome, email e telefone
    - Listagem de animais do cliente
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    
    def get_queryset(self):
        """
        Retorna queryset de clientes filtrado pelo tenant atual e parâmetros de busca.
        """
        # O TenantPermissionMixin já garante o filtro por tenant
        queryset = super().get_queryset()
        
        # Aplicar filtros de busca
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(email__icontains=search) | 
                Q(telefone__icontains=search)
            )
        
        return queryset.order_by('nome')
    
    def perform_create(self, serializer):
        """
        Cria cliente associado ao tenant atual com validações adicionais.
        """
        tenant = get_current_tenant()
        
        # Verificar se já existe cliente com mesmo email no tenant
        email = serializer.validated_data.get('email')
        if email and Cliente.objects.filter(email=email).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'email': 'Já existe um cliente com este email no seu petshop.'
            })
        
        super().perform_create(serializer)
    
    def perform_update(self, serializer):
        """
        Atualiza cliente com validações de tenant e unicidade de email.
        """
        tenant = get_current_tenant()
        instance = serializer.instance
        
        # Verificar se o email não está sendo usado por outro cliente no mesmo tenant
        email = serializer.validated_data.get('email')
        if email and email != instance.email:
            if Cliente.objects.filter(email=email).exclude(id=instance.id).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'email': 'Já existe um cliente com este email no seu petshop.'
                })
        
        super().perform_update(serializer)
    
    @action(detail=True, methods=['get'])
    def animais(self, request, pk=None):
        """
        Lista todos os animais de um cliente específico.
        Garante que apenas animais do tenant atual são retornados.
        """
        cliente = self.get_object()
        
        # Os animais já são filtrados automaticamente pelo TenantAwareManager
        animais = cliente.animais.all()
        
        # Aplicar filtros adicionais se necessário
        search = request.query_params.get('search', None)
        if search:
            animais = animais.filter(
                Q(nome__icontains=search) |
                Q(raca__icontains=search) |
                Q(especie__icontains=search)
            )
        
        serializer = AnimalSerializer(
            animais, 
            many=True, 
            context=self.get_serializer_context()
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def agendamentos(self, request, pk=None):
        """
        Lista agendamentos de um cliente específico.
        """
        cliente = self.get_object()
        
        # Buscar agendamentos através dos animais do cliente
        agendamentos = Agendamento.objects.filter(animal__cliente=cliente)
        
        # Aplicar filtros de data se fornecidos
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        status_filter = request.query_params.get('status')
        
        if data_inicio:
            agendamentos = agendamentos.filter(data_hora__date__gte=data_inicio)
        if data_fim:
            agendamentos = agendamentos.filter(data_hora__date__lte=data_fim)
        if status_filter:
            agendamentos = agendamentos.filter(status=status_filter)
        
        agendamentos = agendamentos.order_by('-data_hora')
        
        serializer = AgendamentoSerializer(
            agendamentos, 
            many=True, 
            context=self.get_serializer_context()
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def vendas(self, request, pk=None):
        """
        Lista vendas de um cliente específico.
        """
        cliente = self.get_object()
        
        # Buscar vendas do cliente
        vendas = Venda.objects.filter(cliente=cliente)
        
        # Aplicar filtros de data se fornecidos
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if data_inicio:
            vendas = vendas.filter(data_venda__date__gte=data_inicio)
        if data_fim:
            vendas = vendas.filter(data_venda__date__lte=data_fim)
        
        vendas = vendas.order_by('-data_venda')
        
        serializer = VendaSerializer(
            vendas, 
            many=True, 
            context=self.get_serializer_context()
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas dos clientes do tenant atual.
        """
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_clientes = queryset.count()
        
        # Clientes cadastrados nos últimos 30 dias
        data_limite = datetime.now() - timedelta(days=30)
        novos_clientes = queryset.filter(data_cadastro__gte=data_limite).count()
        
        # Clientes com mais animais
        clientes_com_animais = queryset.annotate(
            total_animais=Count('animais')
        ).filter(total_animais__gt=0)
        
        media_animais = clientes_com_animais.aggregate(
            media=Avg('total_animais')
        )['media'] or 0
        
        # Top 5 clientes com mais animais
        top_clientes = clientes_com_animais.order_by('-total_animais')[:5]
        
        return Response({
            'total_clientes': total_clientes,
            'novos_clientes_30_dias': novos_clientes,
            'media_animais_por_cliente': round(media_animais, 2),
            'clientes_com_animais': clientes_com_animais.count(),
            'top_clientes': [
                {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'total_animais': cliente.total_animais
                }
                for cliente in top_clientes
            ]
        })


class AnimalViewSet(TenantPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de animais com isolamento por tenant.
    
    Funcionalidades:
    - Filtros automáticos por tenant
    - Validação de relacionamentos cliente-animal dentro do tenant
    - Verificações de propriedade por tenant
    - Busca por nome, raça e nome do cliente
    """
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    
    def get_queryset(self):
        """
        Retorna queryset de animais filtrado pelo tenant atual e parâmetros de busca.
        """
        # O TenantPermissionMixin já garante o filtro por tenant
        queryset = super().get_queryset()
        
        # Aplicar filtros específicos
        cliente_id = self.request.query_params.get('cliente', None)
        search = self.request.query_params.get('search', None)
        especie = self.request.query_params.get('especie', None)
        
        if cliente_id:
            # Validar que o cliente pertence ao tenant atual
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                queryset = queryset.filter(cliente=cliente)
            except Cliente.DoesNotExist:
                # Cliente não existe no tenant atual, retornar queryset vazio
                queryset = queryset.none()
        
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(raca__icontains=search) |
                Q(cliente__nome__icontains=search) |
                Q(cor__icontains=search)
            )
        
        if especie:
            queryset = queryset.filter(especie=especie)
        
        return queryset.order_by('nome')
    
    def perform_create(self, serializer):
        """
        Cria animal associado ao tenant atual com validações de relacionamento.
        """
        tenant = get_current_tenant()
        cliente = serializer.validated_data.get('cliente')
        
        # Validar que o cliente pertence ao tenant atual
        if cliente and cliente.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'cliente': 'O cliente especificado não pertence ao seu petshop.'
            })
        
        super().perform_create(serializer)
    
    def perform_update(self, serializer):
        """
        Atualiza animal com validações de tenant e relacionamentos.
        """
        tenant = get_current_tenant()
        instance = serializer.instance
        cliente = serializer.validated_data.get('cliente', instance.cliente)
        
        # Validar que o cliente pertence ao tenant atual
        if cliente and cliente.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'cliente': 'O cliente especificado não pertence ao seu petshop.'
            })
        
        # Validar que não estamos movendo o animal para outro tenant
        if cliente != instance.cliente and cliente.tenant != instance.tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'cliente': 'Não é possível transferir animais entre petshops diferentes.'
            })
        
        super().perform_update(serializer)
    
    @action(detail=True, methods=['get'])
    def agendamentos(self, request, pk=None):
        """
        Lista agendamentos de um animal específico.
        """
        animal = self.get_object()
        
        # Buscar agendamentos do animal
        agendamentos = Agendamento.objects.filter(animal=animal)
        
        # Aplicar filtros de data e status se fornecidos
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        status_filter = request.query_params.get('status')
        
        if data_inicio:
            agendamentos = agendamentos.filter(data_hora__date__gte=data_inicio)
        if data_fim:
            agendamentos = agendamentos.filter(data_hora__date__lte=data_fim)
        if status_filter:
            agendamentos = agendamentos.filter(status=status_filter)
        
        agendamentos = agendamentos.order_by('-data_hora')
        
        serializer = AgendamentoSerializer(
            agendamentos, 
            many=True, 
            context=self.get_serializer_context()
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def especies(self, request):
        """
        Lista as espécies de animais disponíveis no sistema.
        """
        especies = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Animal.ESPECIES_CHOICES
        ]
        return Response(especies)
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas dos animais do tenant atual.
        """
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_animais = queryset.count()
        
        # Animais por espécie
        por_especie = queryset.values('especie').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Animais cadastrados nos últimos 30 dias
        data_limite = datetime.now() - timedelta(days=30)
        novos_animais = queryset.filter(data_cadastro__gte=data_limite).count()
        
        # Clientes com mais animais
        clientes_com_animais = Cliente.objects.annotate(
            total_animais=Count('animais')
        ).filter(total_animais__gt=0).order_by('-total_animais')[:5]
        
        return Response({
            'total_animais': total_animais,
            'novos_animais_30_dias': novos_animais,
            'por_especie': [
                {
                    'especie': item['especie'],
                    'especie_display': dict(Animal.ESPECIES_CHOICES).get(item['especie'], item['especie']),
                    'count': item['count']
                }
                for item in por_especie
            ],
            'top_clientes': [
                {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'total_animais': cliente.total_animais
                }
                for cliente in clientes_com_animais
            ]
        })
    
    @action(detail=True, methods=['post'])
    def transferir_cliente(self, request, pk=None):
        """
        Transfere um animal para outro cliente do mesmo tenant.
        """
        animal = self.get_object()
        novo_cliente_id = request.data.get('cliente_id')
        
        if not novo_cliente_id:
            return Response({
                'error': 'ID do novo cliente é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Buscar novo cliente (automaticamente filtrado por tenant)
            novo_cliente = Cliente.objects.get(id=novo_cliente_id)
            
            # Transferir animal
            animal.cliente = novo_cliente
            animal.save()
            
            serializer = self.get_serializer(animal)
            return Response({
                'message': f'Animal {animal.nome} transferido para {novo_cliente.nome}',
                'animal': serializer.data
            })
            
        except Cliente.DoesNotExist:
            return Response({
                'error': 'Cliente não encontrado no seu petshop'
            }, status=status.HTTP_404_NOT_FOUND)


class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.filter(ativo=True)
    serializer_class = ServicoSerializer
    
    def get_queryset(self):
        queryset = Servico.objects.filter(ativo=True)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(descricao__icontains=search)
            )
        return queryset


class AgendamentoViewSet(TenantPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de agendamentos com isolamento por tenant.
    
    Funcionalidades:
    - Isolamento de agendamentos por tenant
    - Validações de conflito apenas dentro do tenant
    - Notificações usando configurações do tenant
    - Filtros por status, data e cliente
    """
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    
    def get_queryset(self):
        """
        Retorna queryset de agendamentos filtrado pelo tenant atual e parâmetros.
        """
        # O TenantPermissionMixin já garante o filtro por tenant
        queryset = super().get_queryset()
        
        # Aplicar filtros específicos
        status_filter = self.request.query_params.get('status', None)
        data_inicio = self.request.query_params.get('data_inicio', None)
        data_fim = self.request.query_params.get('data_fim', None)
        cliente_id = self.request.query_params.get('cliente', None)
        animal_id = self.request.query_params.get('animal', None)
        servico_id = self.request.query_params.get('servico', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if data_inicio:
            queryset = queryset.filter(data_hora__date__gte=data_inicio)
        
        if data_fim:
            queryset = queryset.filter(data_hora__date__lte=data_fim)
        
        if cliente_id:
            # Validar que o cliente pertence ao tenant atual
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                queryset = queryset.filter(animal__cliente=cliente)
            except Cliente.DoesNotExist:
                # Cliente não existe no tenant atual, retornar queryset vazio
                queryset = queryset.none()
        
        if animal_id:
            # Validar que o animal pertence ao tenant atual
            try:
                animal = Animal.objects.get(id=animal_id)
                queryset = queryset.filter(animal=animal)
            except Animal.DoesNotExist:
                # Animal não existe no tenant atual, retornar queryset vazio
                queryset = queryset.none()
        
        if servico_id:
            # Validar que o serviço pertence ao tenant atual
            try:
                servico = Servico.objects.get(id=servico_id)
                queryset = queryset.filter(servico=servico)
            except Servico.DoesNotExist:
                # Serviço não existe no tenant atual, retornar queryset vazio
                queryset = queryset.none()
        
        return queryset.order_by('-data_hora')
    
    def perform_create(self, serializer):
        """
        Cria agendamento com validações de tenant e conflitos.
        """
        tenant = get_current_tenant()
        animal = serializer.validated_data.get('animal')
        servico = serializer.validated_data.get('servico')
        data_hora = serializer.validated_data.get('data_hora')
        
        # Validar que animal e serviço pertencem ao tenant atual
        if animal and animal.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'animal': 'O animal especificado não pertence ao seu petshop.'
            })
        
        if servico and servico.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'servico': 'O serviço especificado não pertence ao seu petshop.'
            })
        
        # Verificar conflitos de horário apenas dentro do tenant
        if data_hora:
            conflitos = self._verificar_conflitos_horario(data_hora, servico)
            if conflitos:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'data_hora': f'Já existe um agendamento neste horário: {conflitos}'
                })
        
        super().perform_create(serializer)
        
        # Enviar notificação usando configurações do tenant
        agendamento = serializer.instance
        self._enviar_notificacao_agendamento(agendamento, 'criado')
    
    def perform_update(self, serializer):
        """
        Atualiza agendamento com validações de tenant.
        """
        tenant = get_current_tenant()
        instance = serializer.instance
        animal = serializer.validated_data.get('animal', instance.animal)
        servico = serializer.validated_data.get('servico', instance.servico)
        data_hora = serializer.validated_data.get('data_hora', instance.data_hora)
        
        # Validar que animal e serviço pertencem ao tenant atual
        if animal and animal.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'animal': 'O animal especificado não pertence ao seu petshop.'
            })
        
        if servico and servico.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'servico': 'O serviço especificado não pertence ao seu petshop.'
            })
        
        # Verificar conflitos de horário se a data/hora mudou
        if data_hora != instance.data_hora:
            conflitos = self._verificar_conflitos_horario(data_hora, servico, exclude_id=instance.id)
            if conflitos:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'data_hora': f'Já existe um agendamento neste horário: {conflitos}'
                })
        
        # Verificar se o status mudou para enviar notificação
        status_anterior = instance.status
        super().perform_update(serializer)
        
        if serializer.instance.status != status_anterior:
            self._enviar_notificacao_agendamento(serializer.instance, 'atualizado')
    
    def _verificar_conflitos_horario(self, data_hora, servico, exclude_id=None):
        """
        Verifica conflitos de horário apenas dentro do tenant atual.
        """
        from datetime import timedelta
        
        # Calcular janela de conflito baseada na duração do serviço
        duracao = servico.duracao_estimada if servico else timedelta(hours=1)
        inicio_conflito = data_hora - duracao
        fim_conflito = data_hora + duracao
        
        # Buscar agendamentos conflitantes no tenant atual
        conflitos = Agendamento.objects.filter(
            data_hora__range=(inicio_conflito, fim_conflito),
            status__in=['agendado', 'confirmado', 'em_andamento']
        )
        
        if exclude_id:
            conflitos = conflitos.exclude(id=exclude_id)
        
        if conflitos.exists():
            conflito = conflitos.first()
            return f"{conflito.animal.nome} - {conflito.servico.nome}"
        
        return None
    
    def _enviar_notificacao_agendamento(self, agendamento, acao):
        """
        Envia notificação usando configurações específicas do tenant.
        """
        try:
            from tenants.models import TenantConfiguration
            
            tenant = get_current_tenant()
            
            # Obter configurações de notificação do tenant
            notificacoes_ativas = TenantConfiguration.get_config(
                tenant, 'notificacoes_agendamento', default=True
            )
            
            if not notificacoes_ativas:
                return
            
            email_notificacao = TenantConfiguration.get_config(
                tenant, 'email_notificacao', default=None
            )
            
            if email_notificacao:
                # Aqui você implementaria o envio real do email
                print(f"Notificação enviada para {email_notificacao}: Agendamento {acao}")
                print(f"- Animal: {agendamento.animal.nome}")
                print(f"- Cliente: {agendamento.animal.cliente.nome}")
                print(f"- Serviço: {agendamento.servico.nome}")
                print(f"- Data/Hora: {agendamento.data_hora}")
                print(f"- Status: {agendamento.status}")
        
        except Exception as e:
            # Log do erro mas não falha a operação
            print(f"Erro ao enviar notificação: {str(e)}")
    
    @action(detail=True, methods=['patch'])
    def atualizar_status(self, request, pk=None):
        """
        Atualiza o status de um agendamento com validações.
        """
        agendamento = self.get_object()
        novo_status = request.data.get('status')
        observacoes = request.data.get('observacoes', '')
        
        if not novo_status:
            return Response({
                'error': 'Status é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if novo_status not in dict(Agendamento.STATUS_CHOICES):
            return Response({
                'error': 'Status inválido',
                'opcoes_validas': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Agendamento.STATUS_CHOICES
                ]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar transições de status
        if not self._validar_transicao_status(agendamento.status, novo_status):
            return Response({
                'error': f'Transição de status inválida: {agendamento.status} -> {novo_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        status_anterior = agendamento.status
        agendamento.status = novo_status
        
        if observacoes:
            agendamento.observacoes = observacoes
        
        agendamento.save()
        
        # Enviar notificação se necessário
        if status_anterior != novo_status:
            self._enviar_notificacao_agendamento(agendamento, 'status_atualizado')
        
        serializer = self.get_serializer(agendamento)
        return Response({
            'message': f'Status atualizado de "{dict(Agendamento.STATUS_CHOICES)[status_anterior]}" para "{dict(Agendamento.STATUS_CHOICES)[novo_status]}"',
            'agendamento': serializer.data
        })
    
    def _validar_transicao_status(self, status_atual, novo_status):
        """
        Valida se a transição de status é permitida.
        """
        transicoes_validas = {
            'agendado': ['confirmado', 'cancelado'],
            'confirmado': ['em_andamento', 'cancelado'],
            'em_andamento': ['concluido', 'cancelado'],
            'concluido': [],  # Status final
            'cancelado': ['agendado']  # Pode reagendar
        }
        
        return novo_status in transicoes_validas.get(status_atual, [])
    
    @action(detail=False, methods=['get'])
    def agenda_dia(self, request):
        """
        Retorna a agenda de um dia específico.
        """
        data = request.query_params.get('data')
        if not data:
            from datetime import date
            data = date.today().isoformat()
        
        agendamentos = self.get_queryset().filter(
            data_hora__date=data
        ).order_by('data_hora')
        
        serializer = self.get_serializer(agendamentos, many=True)
        
        # Agrupar por horário para facilitar visualização
        agenda = {}
        for agendamento in serializer.data:
            hora = agendamento['data_hora'][:16]  # YYYY-MM-DD HH:MM
            if hora not in agenda:
                agenda[hora] = []
            agenda[hora].append(agendamento)
        
        return Response({
            'data': data,
            'total_agendamentos': agendamentos.count(),
            'agenda': agenda
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas dos agendamentos do tenant atual.
        """
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_agendamentos = queryset.count()
        
        # Agendamentos por status
        por_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Agendamentos dos últimos 30 dias
        data_limite = datetime.now() - timedelta(days=30)
        agendamentos_recentes = queryset.filter(data_hora__gte=data_limite).count()
        
        # Agendamentos de hoje
        hoje = datetime.now().date()
        agendamentos_hoje = queryset.filter(data_hora__date=hoje).count()
        
        # Próximos agendamentos (próximos 7 dias)
        proximos_7_dias = datetime.now() + timedelta(days=7)
        proximos_agendamentos = queryset.filter(
            data_hora__range=(datetime.now(), proximos_7_dias),
            status__in=['agendado', 'confirmado']
        ).count()
        
        # Serviços mais agendados
        servicos_populares = queryset.values(
            'servico__nome'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return Response({
            'total_agendamentos': total_agendamentos,
            'agendamentos_recentes_30_dias': agendamentos_recentes,
            'agendamentos_hoje': agendamentos_hoje,
            'proximos_agendamentos_7_dias': proximos_agendamentos,
            'por_status': [
                {
                    'status': item['status'],
                    'status_display': dict(Agendamento.STATUS_CHOICES).get(item['status'], item['status']),
                    'count': item['count']
                }
                for item in por_status
            ],
            'servicos_populares': [
                {
                    'servico': item['servico__nome'],
                    'count': item['count']
                }
                for item in servicos_populares
            ]
        })
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Confirma um agendamento.
        """
        agendamento = self.get_object()
        
        if agendamento.status != 'agendado':
            return Response({
                'error': 'Apenas agendamentos com status "agendado" podem ser confirmados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        agendamento.status = 'confirmado'
        agendamento.save()
        
        self._enviar_notificacao_agendamento(agendamento, 'confirmado')
        
        serializer = self.get_serializer(agendamento)
        return Response({
            'message': 'Agendamento confirmado com sucesso',
            'agendamento': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela um agendamento.
        """
        agendamento = self.get_object()
        motivo = request.data.get('motivo', '')
        
        if agendamento.status in ['concluido', 'cancelado']:
            return Response({
                'error': 'Não é possível cancelar agendamentos concluídos ou já cancelados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        agendamento.status = 'cancelado'
        if motivo:
            agendamento.observacoes = f"Cancelado: {motivo}"
        agendamento.save()
        
        self._enviar_notificacao_agendamento(agendamento, 'cancelado')
        
        serializer = self.get_serializer(agendamento)
        return Response({
            'message': 'Agendamento cancelado com sucesso',
            'agendamento': serializer.data
        })


class ProdutoViewSet(TenantPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de produtos com isolamento por tenant.
    
    Funcionalidades:
    - Controle de estoque por tenant
    - Filtros automáticos para produtos do tenant
    - Validações de movimentação de estoque por tenant
    - Alertas de estoque baixo
    """
    queryset = Produto.objects.filter(ativo=True)
    serializer_class = ProdutoSerializer
    
    def get_queryset(self):
        """
        Retorna queryset de produtos filtrado pelo tenant atual e parâmetros.
        """
        # O TenantPermissionMixin já garante o filtro por tenant
        queryset = super().get_queryset().filter(ativo=True)
        
        # Aplicar filtros específicos
        categoria = self.request.query_params.get('categoria', None)
        search = self.request.query_params.get('search', None)
        estoque_baixo = self.request.query_params.get('estoque_baixo', None)
        preco_min = self.request.query_params.get('preco_min', None)
        preco_max = self.request.query_params.get('preco_max', None)
        
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(descricao__icontains=search)
            )
        
        if preco_min:
            try:
                queryset = queryset.filter(preco__gte=float(preco_min))
            except ValueError:
                pass
        
        if preco_max:
            try:
                queryset = queryset.filter(preco__lte=float(preco_max))
            except ValueError:
                pass
        
        if estoque_baixo == 'true':
            # Filtrar produtos com estoque baixo
            produtos_estoque_baixo = []
            for produto in queryset:
                if produto.estoque_baixo:
                    produtos_estoque_baixo.append(produto.id)
            queryset = queryset.filter(id__in=produtos_estoque_baixo)
        
        return queryset.order_by('nome')
    
    def perform_create(self, serializer):
        """
        Cria produto associado ao tenant atual com validações.
        """
        tenant = get_current_tenant()
        
        # Verificar se já existe produto com mesmo nome no tenant
        nome = serializer.validated_data.get('nome')
        if nome and Produto.objects.filter(nome__iexact=nome).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'nome': 'Já existe um produto com este nome no seu estoque.'
            })
        
        super().perform_create(serializer)
        
        # Log da criação do produto
        produto = serializer.instance
        self._log_movimentacao_estoque(produto, 'criacao', produto.estoque, 'Produto criado')
    
    def perform_update(self, serializer):
        """
        Atualiza produto com validações de tenant e estoque.
        """
        tenant = get_current_tenant()
        instance = serializer.instance
        
        # Verificar se o nome não está sendo usado por outro produto no mesmo tenant
        nome = serializer.validated_data.get('nome', instance.nome)
        if nome != instance.nome:
            if Produto.objects.filter(nome__iexact=nome).exclude(id=instance.id).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'nome': 'Já existe um produto com este nome no seu estoque.'
                })
        
        # Verificar mudanças no estoque
        estoque_anterior = instance.estoque
        estoque_novo = serializer.validated_data.get('estoque', estoque_anterior)
        
        super().perform_update(serializer)
        
        # Log da movimentação se o estoque mudou
        if estoque_novo != estoque_anterior:
            diferenca = estoque_novo - estoque_anterior
            tipo_movimentacao = 'entrada' if diferenca > 0 else 'saida'
            observacao = f'Ajuste manual: {diferenca:+d} unidades'
            self._log_movimentacao_estoque(
                serializer.instance, 
                tipo_movimentacao, 
                abs(diferenca), 
                observacao
            )
    
    def _log_movimentacao_estoque(self, produto, tipo, quantidade, observacao):
        """
        Registra movimentação de estoque (implementação futura).
        """
        # Aqui você pode implementar um sistema de log de movimentações
        print(f"LOG ESTOQUE - Produto: {produto.nome}, Tipo: {tipo}, Qtd: {quantidade}, Obs: {observacao}")
    
    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """
        Lista produtos com estoque baixo no tenant atual.
        """
        queryset = self.get_queryset()
        produtos_estoque_baixo = [p for p in queryset if p.estoque_baixo]
        
        serializer = self.get_serializer(produtos_estoque_baixo, many=True)
        
        return Response({
            'total': len(produtos_estoque_baixo),
            'produtos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def categorias(self, request):
        """
        Lista as categorias de produtos disponíveis.
        """
        categorias = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Produto.CATEGORIAS_CHOICES
        ]
        return Response(categorias)
    
    @action(detail=True, methods=['post'])
    def entrada_estoque(self, request, pk=None):
        """
        Registra entrada de estoque para um produto.
        """
        produto = self.get_object()
        quantidade = request.data.get('quantidade')
        observacao = request.data.get('observacao', '')
        
        if not quantidade:
            return Response({
                'error': 'Quantidade é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantidade = int(quantidade)
            if quantidade <= 0:
                raise ValueError()
        except ValueError:
            return Response({
                'error': 'Quantidade deve ser um número inteiro positivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Atualizar estoque
        estoque_anterior = produto.estoque
        produto.estoque += quantidade
        produto.save()
        
        # Log da movimentação
        self._log_movimentacao_estoque(
            produto, 
            'entrada', 
            quantidade, 
            observacao or 'Entrada manual de estoque'
        )
        
        serializer = self.get_serializer(produto)
        return Response({
            'message': f'Entrada de {quantidade} unidades registrada com sucesso',
            'estoque_anterior': estoque_anterior,
            'estoque_atual': produto.estoque,
            'produto': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def saida_estoque(self, request, pk=None):
        """
        Registra saída de estoque para um produto.
        """
        produto = self.get_object()
        quantidade = request.data.get('quantidade')
        observacao = request.data.get('observacao', '')
        
        if not quantidade:
            return Response({
                'error': 'Quantidade é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantidade = int(quantidade)
            if quantidade <= 0:
                raise ValueError()
        except ValueError:
            return Response({
                'error': 'Quantidade deve ser um número inteiro positivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se há estoque suficiente
        if produto.estoque < quantidade:
            return Response({
                'error': f'Estoque insuficiente. Disponível: {produto.estoque} unidades'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Atualizar estoque
        estoque_anterior = produto.estoque
        produto.estoque -= quantidade
        produto.save()
        
        # Log da movimentação
        self._log_movimentacao_estoque(
            produto, 
            'saida', 
            quantidade, 
            observacao or 'Saída manual de estoque'
        )
        
        serializer = self.get_serializer(produto)
        return Response({
            'message': f'Saída de {quantidade} unidades registrada com sucesso',
            'estoque_anterior': estoque_anterior,
            'estoque_atual': produto.estoque,
            'produto': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas dos produtos do tenant atual.
        """
        from django.db.models import Count, Sum, Avg, Min, Max
        
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_produtos = queryset.count()
        valor_total_estoque = sum(p.preco * p.estoque for p in queryset)
        
        # Produtos por categoria
        por_categoria = queryset.values('categoria').annotate(
            count=Count('id'),
            valor_total=Sum(models.F('preco') * models.F('estoque'))
        ).order_by('-count')
        
        # Produtos com estoque baixo
        produtos_estoque_baixo = [p for p in queryset if p.estoque_baixo]
        
        # Produto mais caro e mais barato
        produto_mais_caro = queryset.order_by('-preco').first()
        produto_mais_barato = queryset.order_by('preco').first()
        
        # Produtos sem estoque
        produtos_sem_estoque = queryset.filter(estoque=0).count()
        
        return Response({
            'total_produtos': total_produtos,
            'valor_total_estoque': valor_total_estoque,
            'produtos_estoque_baixo': len(produtos_estoque_baixo),
            'produtos_sem_estoque': produtos_sem_estoque,
            'por_categoria': [
                {
                    'categoria': item['categoria'],
                    'categoria_display': dict(Produto.CATEGORIAS_CHOICES).get(item['categoria'], item['categoria']),
                    'count': item['count'],
                    'valor_total': item['valor_total'] or 0
                }
                for item in por_categoria
            ],
            'produto_mais_caro': {
                'nome': produto_mais_caro.nome,
                'preco': produto_mais_caro.preco
            } if produto_mais_caro else None,
            'produto_mais_barato': {
                'nome': produto_mais_barato.nome,
                'preco': produto_mais_barato.preco
            } if produto_mais_barato else None
        })
    
    @action(detail=False, methods=['post'])
    def inventario(self, request):
        """
        Realiza inventário completo do estoque.
        Permite ajustar o estoque de múltiplos produtos de uma vez.
        """
        ajustes = request.data.get('ajustes', [])
        
        if not ajustes or not isinstance(ajustes, list):
            return Response({
                'error': 'Lista de ajustes é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        resultados = []
        erros = []
        
        for ajuste in ajustes:
            produto_id = ajuste.get('produto_id')
            estoque_real = ajuste.get('estoque_real')
            observacao = ajuste.get('observacao', 'Inventário')
            
            if not produto_id or estoque_real is None:
                erros.append({
                    'produto_id': produto_id,
                    'erro': 'produto_id e estoque_real são obrigatórios'
                })
                continue
            
            try:
                produto = Produto.objects.get(id=produto_id)
                estoque_anterior = produto.estoque
                diferenca = estoque_real - estoque_anterior
                
                produto.estoque = estoque_real
                produto.save()
                
                # Log da movimentação
                if diferenca != 0:
                    tipo_movimentacao = 'entrada' if diferenca > 0 else 'saida'
                    self._log_movimentacao_estoque(
                        produto, 
                        tipo_movimentacao, 
                        abs(diferenca), 
                        f'Inventário: {observacao}'
                    )
                
                resultados.append({
                    'produto_id': produto_id,
                    'produto_nome': produto.nome,
                    'estoque_anterior': estoque_anterior,
                    'estoque_atual': estoque_real,
                    'diferenca': diferenca,
                    'status': 'sucesso'
                })
                
            except Produto.DoesNotExist:
                erros.append({
                    'produto_id': produto_id,
                    'erro': 'Produto não encontrado no seu estoque'
                })
            except Exception as e:
                erros.append({
                    'produto_id': produto_id,
                    'erro': str(e)
                })
        
        return Response({
            'message': f'Inventário processado: {len(resultados)} sucessos, {len(erros)} erros',
            'resultados': resultados,
            'erros': erros
        })


class VendaViewSet(TenantPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de vendas com isolamento por tenant.
    
    Funcionalidades:
    - Isolamento de vendas por tenant
    - Cálculos financeiros específicos por tenant
    - Relatórios financeiros segregados
    - Controle de estoque automático
    """
    queryset = Venda.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VendaCreateSerializer
        return VendaSerializer
    
    def get_queryset(self):
        """
        Retorna queryset de vendas filtrado pelo tenant atual e parâmetros.
        """
        # O TenantPermissionMixin já garante o filtro por tenant
        queryset = super().get_queryset()
        
        # Aplicar filtros específicos
        cliente_id = self.request.query_params.get('cliente', None)
        data_inicio = self.request.query_params.get('data_inicio', None)
        data_fim = self.request.query_params.get('data_fim', None)
        valor_min = self.request.query_params.get('valor_min', None)
        valor_max = self.request.query_params.get('valor_max', None)
        
        if cliente_id:
            # Validar que o cliente pertence ao tenant atual
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                queryset = queryset.filter(cliente=cliente)
            except Cliente.DoesNotExist:
                # Cliente não existe no tenant atual, retornar queryset vazio
                queryset = queryset.none()
        
        if data_inicio:
            queryset = queryset.filter(data_venda__date__gte=data_inicio)
        
        if data_fim:
            queryset = queryset.filter(data_venda__date__lte=data_fim)
        
        if valor_min:
            try:
                queryset = queryset.filter(valor_total__gte=float(valor_min))
            except ValueError:
                pass
        
        if valor_max:
            try:
                queryset = queryset.filter(valor_total__lte=float(valor_max))
            except ValueError:
                pass
        
        return queryset.order_by('-data_venda')
    
    def perform_create(self, serializer):
        """
        Cria venda com validações de tenant e atualização de estoque.
        """
        tenant = get_current_tenant()
        cliente = serializer.validated_data.get('cliente')
        
        # Validar que o cliente pertence ao tenant atual
        if cliente and cliente.tenant != tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'cliente': 'O cliente especificado não pertence ao seu petshop.'
            })
        
        super().perform_create(serializer)
        
        # A atualização de estoque é feita no VendaCreateSerializer
        venda = serializer.instance
        self._registrar_venda_financeiro(venda)
    
    def _registrar_venda_financeiro(self, venda):
        """
        Registra a venda no sistema financeiro (implementação futura).
        """
        # Aqui você pode implementar integração com sistema financeiro
        print(f"FINANCEIRO - Venda registrada: R$ {venda.valor_total} - Cliente: {venda.cliente.nome}")
    
    @action(detail=False, methods=['get'])
    def relatorio_financeiro(self, request):
        """
        Gera relatório financeiro do tenant atual.
        """
        from django.db.models import Sum, Count, Avg
        from datetime import datetime, timedelta
        
        # Parâmetros do relatório
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        queryset = self.get_queryset()
        
        # Aplicar filtros de data se fornecidos
        if data_inicio:
            queryset = queryset.filter(data_venda__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_venda__date__lte=data_fim)
        
        # Estatísticas básicas
        total_vendas = queryset.count()
        valor_total = queryset.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
        valor_medio = queryset.aggregate(Avg('valor_total'))['valor_total__avg'] or 0
        desconto_total = queryset.aggregate(Sum('desconto'))['desconto__sum'] or 0
        
        # Vendas por período
        hoje = datetime.now().date()
        ontem = hoje - timedelta(days=1)
        esta_semana = hoje - timedelta(days=7)
        este_mes = hoje.replace(day=1)
        
        vendas_hoje = queryset.filter(data_venda__date=hoje).aggregate(
            count=Count('id'), total=Sum('valor_total')
        )
        vendas_ontem = queryset.filter(data_venda__date=ontem).aggregate(
            count=Count('id'), total=Sum('valor_total')
        )
        vendas_semana = queryset.filter(data_venda__date__gte=esta_semana).aggregate(
            count=Count('id'), total=Sum('valor_total')
        )
        vendas_mes = queryset.filter(data_venda__date__gte=este_mes).aggregate(
            count=Count('id'), total=Sum('valor_total')
        )
        
        # Top clientes
        top_clientes = queryset.values(
            'cliente__nome', 'cliente__id'
        ).annotate(
            total_compras=Count('id'),
            valor_total=Sum('valor_total')
        ).order_by('-valor_total')[:10]
        
        # Produtos mais vendidos
        from django.db.models import F
        produtos_vendidos = ItemVenda.objects.filter(
            venda__in=queryset
        ).values(
            'produto__nome', 'produto__id'
        ).annotate(
            quantidade_vendida=Sum('quantidade'),
            valor_total=Sum(F('quantidade') * F('preco_unitario'))
        ).order_by('-quantidade_vendida')[:10]
        
        return Response({
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            },
            'resumo': {
                'total_vendas': total_vendas,
                'valor_total': float(valor_total),
                'valor_medio': float(valor_medio),
                'desconto_total': float(desconto_total),
                'valor_liquido': float(valor_total - desconto_total)
            },
            'por_periodo': {
                'hoje': {
                    'vendas': vendas_hoje['count'] or 0,
                    'valor': float(vendas_hoje['total'] or 0)
                },
                'ontem': {
                    'vendas': vendas_ontem['count'] or 0,
                    'valor': float(vendas_ontem['total'] or 0)
                },
                'esta_semana': {
                    'vendas': vendas_semana['count'] or 0,
                    'valor': float(vendas_semana['total'] or 0)
                },
                'este_mes': {
                    'vendas': vendas_mes['count'] or 0,
                    'valor': float(vendas_mes['total'] or 0)
                }
            },
            'top_clientes': [
                {
                    'cliente_id': item['cliente__id'],
                    'cliente_nome': item['cliente__nome'],
                    'total_compras': item['total_compras'],
                    'valor_total': float(item['valor_total'])
                }
                for item in top_clientes
            ],
            'produtos_mais_vendidos': [
                {
                    'produto_id': item['produto__id'],
                    'produto_nome': item['produto__nome'],
                    'quantidade_vendida': item['quantidade_vendida'],
                    'valor_total': float(item['valor_total'])
                }
                for item in produtos_vendidos
            ]
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_vendas(self, request):
        """
        Retorna dados para dashboard de vendas.
        """
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset()
        
        # Últimos 30 dias
        data_limite = datetime.now() - timedelta(days=30)
        vendas_30_dias = queryset.filter(data_venda__gte=data_limite)
        
        # Vendas por dia (últimos 7 dias)
        vendas_por_dia = []
        for i in range(7):
            data = datetime.now().date() - timedelta(days=i)
            vendas_dia = queryset.filter(data_venda__date=data).aggregate(
                count=Count('id'),
                total=Sum('valor_total')
            )
            vendas_por_dia.append({
                'data': data.isoformat(),
                'vendas': vendas_dia['count'] or 0,
                'valor': float(vendas_dia['total'] or 0)
            })
        
        # Metas (configuráveis por tenant no futuro)
        meta_vendas_mes = 10000.00  # Exemplo
        meta_vendas_dia = 500.00    # Exemplo
        
        # Vendas do mês atual
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        vendas_mes_atual = queryset.filter(data_venda__gte=inicio_mes).aggregate(
            count=Count('id'),
            total=Sum('valor_total')
        )
        
        # Vendas de hoje
        hoje = datetime.now().date()
        vendas_hoje = queryset.filter(data_venda__date=hoje).aggregate(
            count=Count('id'),
            total=Sum('valor_total')
        )
        
        return Response({
            'vendas_hoje': {
                'count': vendas_hoje['count'] or 0,
                'valor': float(vendas_hoje['total'] or 0),
                'meta': meta_vendas_dia,
                'percentual_meta': (float(vendas_hoje['total'] or 0) / meta_vendas_dia * 100) if meta_vendas_dia > 0 else 0
            },
            'vendas_mes': {
                'count': vendas_mes_atual['count'] or 0,
                'valor': float(vendas_mes_atual['total'] or 0),
                'meta': meta_vendas_mes,
                'percentual_meta': (float(vendas_mes_atual['total'] or 0) / meta_vendas_mes * 100) if meta_vendas_mes > 0 else 0
            },
            'vendas_30_dias': {
                'count': vendas_30_dias.count(),
                'valor': float(vendas_30_dias.aggregate(Sum('valor_total'))['valor_total__sum'] or 0)
            },
            'vendas_por_dia': list(reversed(vendas_por_dia))  # Mais recente primeiro
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas detalhadas das vendas do tenant atual.
        """
        from django.db.models import Sum, Count, Avg, Max, Min
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset()
        
        # Estatísticas básicas
        total_vendas = queryset.count()
        
        if total_vendas == 0:
            return Response({
                'message': 'Nenhuma venda encontrada',
                'total_vendas': 0
            })
        
        valor_total = queryset.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
        valor_medio = queryset.aggregate(Avg('valor_total'))['valor_total__avg'] or 0
        maior_venda = queryset.aggregate(Max('valor_total'))['valor_total__max'] or 0
        menor_venda = queryset.aggregate(Min('valor_total'))['valor_total__min'] or 0
        
        # Clientes únicos
        clientes_unicos = queryset.values('cliente').distinct().count()
        
        # Ticket médio por cliente
        ticket_medio_cliente = valor_total / clientes_unicos if clientes_unicos > 0 else 0
        
        # Produtos vendidos
        total_itens = ItemVenda.objects.filter(venda__in=queryset).aggregate(
            Sum('quantidade')
        )['quantidade__sum'] or 0
        
        # Desconto médio
        desconto_medio = queryset.aggregate(Avg('desconto'))['desconto__avg'] or 0
        
        return Response({
            'total_vendas': total_vendas,
            'valor_total': float(valor_total),
            'valor_medio': float(valor_medio),
            'maior_venda': float(maior_venda),
            'menor_venda': float(menor_venda),
            'clientes_unicos': clientes_unicos,
            'ticket_medio_cliente': float(ticket_medio_cliente),
            'total_itens_vendidos': total_itens,
            'desconto_medio': float(desconto_medio)
        })
    
    @action(detail=True, methods=['post'])
    def cancelar_venda(self, request, pk=None):
        """
        Cancela uma venda e reverte o estoque.
        """
        venda = self.get_object()
        motivo = request.data.get('motivo', '')
        
        if not motivo:
            return Response({
                'error': 'Motivo do cancelamento é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reverter estoque dos produtos
        for item in venda.itens.all():
            produto = item.produto
            produto.estoque += item.quantidade
            produto.save()
        
        # Marcar venda como cancelada (adicionar campo status no futuro)
        venda.observacoes = f"CANCELADA: {motivo}"
        venda.save()
        
        # Registrar no financeiro
        print(f"FINANCEIRO - Venda cancelada: R$ {venda.valor_total} - Motivo: {motivo}")
        
        serializer = self.get_serializer(venda)
        return Response({
            'message': 'Venda cancelada com sucesso',
            'motivo': motivo,
            'venda': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def fechar_caixa(self, request):
        """
        Fecha o caixa do dia com resumo financeiro.
        """
        from datetime import datetime
        
        hoje = datetime.now().date()
        vendas_hoje = self.get_queryset().filter(data_venda__date=hoje)
        
        if vendas_hoje.count() == 0:
            return Response({
                'message': 'Nenhuma venda registrada hoje',
                'data': hoje.isoformat()
            })
        
        # Resumo do dia
        resumo = vendas_hoje.aggregate(
            total_vendas=Count('id'),
            valor_bruto=Sum('valor_total'),
            desconto_total=Sum('desconto')
        )
        
        valor_liquido = (resumo['valor_bruto'] or 0) - (resumo['desconto_total'] or 0)
        
        # Produtos vendidos hoje
        itens_vendidos = ItemVenda.objects.filter(
            venda__in=vendas_hoje
        ).aggregate(
            total_itens=Sum('quantidade')
        )
        
        # Clientes atendidos
        clientes_hoje = vendas_hoje.values('cliente').distinct().count()
        
        fechamento = {
            'data': hoje.isoformat(),
            'total_vendas': resumo['total_vendas'] or 0,
            'valor_bruto': float(resumo['valor_bruto'] or 0),
            'desconto_total': float(resumo['desconto_total'] or 0),
            'valor_liquido': float(valor_liquido),
            'total_itens_vendidos': itens_vendidos['total_itens'] or 0,
            'clientes_atendidos': clientes_hoje,
            'ticket_medio': float((resumo['valor_bruto'] or 0) / (resumo['total_vendas'] or 1))
        }
        
        # Registrar fechamento (implementação futura)
        print(f"CAIXA FECHADO - {fechamento}")
        
        return Response({
            'message': 'Caixa fechado com sucesso',
            'fechamento': fechamento
        })


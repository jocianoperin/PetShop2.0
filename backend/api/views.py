from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Cliente, Animal, Servico, Agendamento, Produto, Venda
from .serializers import (
    ClienteSerializer, AnimalSerializer, ServicoSerializer,
    AgendamentoSerializer, ProdutoSerializer, VendaSerializer, VendaCreateSerializer
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    
    def get_queryset(self):
        queryset = Cliente.objects.all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(email__icontains=search) | 
                Q(telefone__icontains=search)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def animais(self, request, pk=None):
        cliente = self.get_object()
        animais = cliente.animais.all()
        serializer = AnimalSerializer(animais, many=True)
        return Response(serializer.data)


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    
    def get_queryset(self):
        queryset = Animal.objects.all()
        cliente_id = self.request.query_params.get('cliente', None)
        search = self.request.query_params.get('search', None)
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(raca__icontains=search) |
                Q(cliente__nome__icontains=search)
            )
        
        return queryset


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


class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    
    def get_queryset(self):
        queryset = Agendamento.objects.all()
        status_filter = self.request.query_params.get('status', None)
        data_inicio = self.request.query_params.get('data_inicio', None)
        data_fim = self.request.query_params.get('data_fim', None)
        cliente_id = self.request.query_params.get('cliente', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if data_inicio:
            queryset = queryset.filter(data_hora__date__gte=data_inicio)
        
        if data_fim:
            queryset = queryset.filter(data_hora__date__lte=data_fim)
        
        if cliente_id:
            queryset = queryset.filter(animal__cliente_id=cliente_id)
        
        return queryset
    
    @action(detail=True, methods=['patch'])
    def atualizar_status(self, request, pk=None):
        agendamento = self.get_object()
        novo_status = request.data.get('status')
        
        if novo_status in dict(Agendamento.STATUS_CHOICES):
            agendamento.status = novo_status
            agendamento.save()
            serializer = self.get_serializer(agendamento)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Status inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(ativo=True)
    serializer_class = ProdutoSerializer
    
    def get_queryset(self):
        queryset = Produto.objects.filter(ativo=True)
        categoria = self.request.query_params.get('categoria', None)
        search = self.request.query_params.get('search', None)
        estoque_baixo = self.request.query_params.get('estoque_baixo', None)
        
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | 
                Q(descricao__icontains=search)
            )
        
        if estoque_baixo == 'true':
            queryset = [p for p in queryset if p.estoque_baixo]
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        produtos = [p for p in self.get_queryset() if p.estoque_baixo]
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class VendaViewSet(viewsets.ModelViewSet):
    queryset = Venda.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VendaCreateSerializer
        return VendaSerializer
    
    def get_queryset(self):
        queryset = Venda.objects.all()
        cliente_id = self.request.query_params.get('cliente', None)
        data_inicio = self.request.query_params.get('data_inicio', None)
        data_fim = self.request.query_params.get('data_fim', None)
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if data_inicio:
            queryset = queryset.filter(data_venda__date__gte=data_inicio)
        
        if data_fim:
            queryset = queryset.filter(data_venda__date__lte=data_fim)
        
        return queryset


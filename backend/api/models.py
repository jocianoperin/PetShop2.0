from django.db import models
from django.contrib.auth.models import User
from tenants.base_models import TenantAwareModel


class Cliente(TenantAwareModel):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    endereco = models.TextField()
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = ['nome']
        # Email único por tenant, não globalmente
        unique_together = [['tenant', 'email']]


class Animal(TenantAwareModel):
    ESPECIES_CHOICES = [
        ('cao', 'Cão'),
        ('gato', 'Gato'),
        ('ave', 'Ave'),
        ('roedor', 'Roedor'),
        ('reptil', 'Réptil'),
        ('outro', 'Outro'),
    ]
    
    nome = models.CharField(max_length=50)
    especie = models.CharField(max_length=10, choices=ESPECIES_CHOICES)
    raca = models.CharField(max_length=50, blank=True)
    data_nascimento = models.DateField()
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cor = models.CharField(max_length=30, blank=True)
    observacoes = models.TextField(blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='animais')
    foto = models.ImageField(upload_to='animais/', null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} ({self.cliente.nome})"
    
    def clean(self):
        """Validações customizadas para garantir que cliente e animal pertencem ao mesmo tenant"""
        super().clean()
        if self.cliente and self.tenant and self.cliente.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Animal e cliente devem pertencer ao mesmo tenant')
    
    def save(self, *args, **kwargs):
        """Override save to ensure tenant consistency"""
        # Se o tenant não foi definido mas temos um cliente, usar o tenant do cliente
        if not self.tenant_id and self.cliente:
            self.tenant = self.cliente.tenant
        
        # Validar que cliente e animal pertencem ao mesmo tenant
        if self.cliente and self.tenant and self.cliente.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Animal e cliente devem pertencer ao mesmo tenant')
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['nome']


class Servico(TenantAwareModel):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_estimada = models.DurationField(help_text="Duração estimada do serviço")
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = ['nome']


class Agendamento(TenantAwareModel):
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('confirmado', 'Confirmado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    data_hora = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='agendado')
    observacoes = models.TextField(blank=True)
    valor_final = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.animal.nome} - {self.servico.nome} ({self.data_hora.strftime('%d/%m/%Y %H:%M')})"
    
    def clean(self):
        """Validações customizadas para garantir que animal, serviço e agendamento pertencem ao mesmo tenant"""
        super().clean()
        if self.animal and self.tenant and self.animal.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Animal e agendamento devem pertencer ao mesmo tenant')
        if self.servico and self.tenant and self.servico.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Serviço e agendamento devem pertencer ao mesmo tenant')
    
    class Meta:
        ordering = ['-data_hora']


class Produto(TenantAwareModel):
    CATEGORIAS_CHOICES = [
        ('racao', 'Ração'),
        ('brinquedo', 'Brinquedo'),
        ('higiene', 'Higiene'),
        ('acessorio', 'Acessório'),
        ('medicamento', 'Medicamento'),
        ('outro', 'Outro'),
    ]
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    categoria = models.CharField(max_length=15, choices=CATEGORIAS_CHOICES)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=5)
    ativo = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='produtos/', null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome
    
    @property
    def estoque_baixo(self):
        return self.estoque <= self.estoque_minimo
    
    class Meta:
        ordering = ['nome']


class Venda(TenantAwareModel):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data_venda = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Venda {self.id} - {self.cliente.nome} ({self.data_venda.strftime('%d/%m/%Y')})"
    
    def clean(self):
        """Validações customizadas para garantir que cliente e venda pertencem ao mesmo tenant"""
        super().clean()
        if self.cliente and self.tenant and self.cliente.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Cliente e venda devem pertencer ao mesmo tenant')
    
    class Meta:
        ordering = ['-data_venda']


class ItemVenda(TenantAwareModel):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"{self.produto.nome} x{self.quantidade}"
    
    def clean(self):
        """Validações customizadas para garantir que venda, produto e item pertencem ao mesmo tenant"""
        super().clean()
        if self.venda and self.tenant and self.venda.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Venda e item de venda devem pertencer ao mesmo tenant')
        if self.produto and self.tenant and self.produto.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError('Produto e item de venda devem pertencer ao mesmo tenant')
    
    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario


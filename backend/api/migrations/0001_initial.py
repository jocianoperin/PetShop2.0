# Generated by Django 5.2.3 on 2025-06-23 13:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('telefone', models.CharField(max_length=20)),
                ('endereco', models.TextField()),
                ('data_cadastro', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('categoria', models.CharField(choices=[('racao', 'Ração'), ('brinquedo', 'Brinquedo'), ('higiene', 'Higiene'), ('acessorio', 'Acessório'), ('medicamento', 'Medicamento'), ('outro', 'Outro')], max_length=15)),
                ('preco', models.DecimalField(decimal_places=2, max_digits=8)),
                ('estoque', models.PositiveIntegerField(default=0)),
                ('estoque_minimo', models.PositiveIntegerField(default=5)),
                ('ativo', models.BooleanField(default=True)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='produtos/')),
                ('data_cadastro', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Servico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('preco', models.DecimalField(decimal_places=2, max_digits=8)),
                ('duracao_estimada', models.DurationField(help_text='Duração estimada do serviço')),
                ('ativo', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Animal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50)),
                ('especie', models.CharField(choices=[('cao', 'Cão'), ('gato', 'Gato'), ('ave', 'Ave'), ('roedor', 'Roedor'), ('reptil', 'Réptil'), ('outro', 'Outro')], max_length=10)),
                ('raca', models.CharField(blank=True, max_length=50)),
                ('data_nascimento', models.DateField()),
                ('peso', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('cor', models.CharField(blank=True, max_length=30)),
                ('observacoes', models.TextField(blank=True)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='animais/')),
                ('data_cadastro', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='animais', to='api.cliente')),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Agendamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField()),
                ('status', models.CharField(choices=[('agendado', 'Agendado'), ('confirmado', 'Confirmado'), ('em_andamento', 'Em Andamento'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado')], default='agendado', max_length=15)),
                ('observacoes', models.TextField(blank=True)),
                ('valor_final', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('animal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.animal')),
                ('servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.servico')),
            ],
            options={
                'ordering': ['-data_hora'],
            },
        ),
        migrations.CreateModel(
            name='Venda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_venda', models.DateTimeField(auto_now_add=True)),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('desconto', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('observacoes', models.TextField(blank=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.cliente')),
            ],
            options={
                'ordering': ['-data_venda'],
            },
        ),
        migrations.CreateModel(
            name='ItemVenda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.PositiveIntegerField()),
                ('preco_unitario', models.DecimalField(decimal_places=2, max_digits=8)),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.produto')),
                ('venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='api.venda')),
            ],
        ),
    ]

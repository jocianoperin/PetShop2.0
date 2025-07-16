# Generated manually for tenant-aware models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_tenantconfiguration_config_type_and_more'),
        ('api', '0001_initial'),
    ]

    operations = [
        # First, create a default tenant if it doesn't exist
        migrations.RunSQL(
            """
            INSERT OR IGNORE INTO tenants (
                id, name, subdomain, schema_name, created_at, updated_at, 
                is_active, plan_type, max_users, max_animals
            ) VALUES (
                '00000000-0000-0000-0000-000000000001',
                'Default Tenant',
                'default',
                'tenant_default',
                datetime('now'),
                datetime('now'),
                1,
                'basic',
                10,
                1000
            );
            """,
            reverse_sql="DELETE FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001';"
        ),
        
        # Add tenant field to Cliente
        migrations.AddField(
            model_name='cliente',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='cliente_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Add tenant field to Animal
        migrations.AddField(
            model_name='animal',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='animal_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Add tenant field to Servico
        migrations.AddField(
            model_name='servico',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servico_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Add tenant field to Agendamento
        migrations.AddField(
            model_name='agendamento',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='agendamento_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Add tenant field to Produto
        migrations.AddField(
            model_name='produto',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='produto_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Add tenant field to Venda
        migrations.AddField(
            model_name='venda',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='venda_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Add tenant field to ItemVenda
        migrations.AddField(
            model_name='itemvenda',
            name='tenant',
            field=models.ForeignKey(
                default='00000000-0000-0000-0000-000000000001',
                help_text='Tenant ao qual este registro pertence',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='itemvenda_set',
                to='tenants.tenant',
                verbose_name='Tenant'
            ),
            preserve_default=False,
        ),
        
        # Remove unique constraint on Cliente.email and add unique_together with tenant
        migrations.AlterField(
            model_name='cliente',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        
        # Add unique_together constraint for Cliente
        migrations.AlterUniqueTogether(
            name='cliente',
            unique_together={('tenant', 'email')},
        ),
        
        # Add indexes for better performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_cliente_tenant_id ON api_cliente(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_cliente_tenant_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_animal_tenant_id ON api_animal(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_animal_tenant_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_servico_tenant_id ON api_servico(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_servico_tenant_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_agendamento_tenant_id ON api_agendamento(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_agendamento_tenant_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_produto_tenant_id ON api_produto(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_produto_tenant_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_venda_tenant_id ON api_venda(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_venda_tenant_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS api_itemvenda_tenant_id ON api_itemvenda(tenant_id);",
            reverse_sql="DROP INDEX IF EXISTS api_itemvenda_tenant_id;"
        ),
    ]
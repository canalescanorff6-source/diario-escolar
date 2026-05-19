# Generated manually for Diário IA - Etapa 11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('arquivo', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(choices=[('GERADO', 'Gerado'), ('FALHA', 'Falha')], default='GERADO', max_length=20)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='backups_sistema', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Backup do Sistema',
                'verbose_name_plural': 'Backups do Sistema',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='IntegracaoEscolar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('tipo', models.CharField(choices=[('GESTAO', 'Cadastro pela gestão'), ('PDF', 'PDF/documento'), ('SISTEMA', 'Sistema externo'), ('OUTRO', 'Outro')], default='GESTAO', max_length=20)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('ativa', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Integração Escolar',
                'verbose_name_plural': 'Integrações Escolares',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='IndicadorGestao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('valor', models.CharField(max_length=80)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('referencia', models.DateField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Indicador de Gestão',
                'verbose_name_plural': 'Indicadores de Gestão',
                'ordering': ['nome'],
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0012_integracao_gestao_manual'),
    ]

    operations = [
        migrations.AddField(
            model_name='escola',
            name='brasao_logo',
            field=models.ImageField(blank=True, help_text='Imagem institucional exibida na tela de login premium.', null=True, upload_to='escolas/', verbose_name='Foto, logo ou brasão'),
        ),
        migrations.AddField(
            model_name='escola',
            name='estado_nome',
            field=models.CharField(blank=True, default='ESTADO DO MARANHÃO', max_length=160, verbose_name='Estado/órgão superior'),
        ),
        migrations.AddField(
            model_name='escola',
            name='secretaria',
            field=models.CharField(blank=True, default='SECRETARIA DE ESTADO DA EDUCAÇÃO', max_length=180, verbose_name='Secretaria/órgão responsável'),
        ),
        migrations.AddField(
            model_name='escola',
            name='gestor_nome',
            field=models.CharField(blank=True, max_length=180, null=True, verbose_name='Diretor(a) ou gestor(a)'),
        ),
        migrations.AddField(
            model_name='escola',
            name='gestor_cargo',
            field=models.CharField(blank=True, default='Direção escolar', max_length=120, verbose_name='Cargo da gestão'),
        ),
        migrations.AddField(
            model_name='escola',
            name='texto_institucional',
            field=models.TextField(blank=True, null=True, verbose_name='Texto institucional do login'),
        ),
    ]

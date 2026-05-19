from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0011_fechamento_mensal_oficial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integracaoescolar',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('GESTAO', 'Cadastro pela gestão'),
                    ('PDF', 'PDF/documento'),
                    ('SISTEMA', 'Sistema externo'),
                    ('OUTRO', 'Outro'),
                ],
                default='GESTAO',
                max_length=20,
            ),
        ),
    ]

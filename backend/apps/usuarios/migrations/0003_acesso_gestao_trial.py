from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0002_usuario_foto"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="gestao_teste_inicio",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Início do teste da gestão"),
        ),
        migrations.AddField(
            model_name="usuario",
            name="gestao_acesso_expira_em",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Acesso da gestão expira em"),
        ),
        migrations.AddField(
            model_name="usuario",
            name="gestao_acesso_bloqueado",
            field=models.BooleanField(default=False, verbose_name="Acesso da gestão bloqueado"),
        ),
        migrations.AddField(
            model_name="usuario",
            name="gestao_serial_ultimo",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Último serial aplicado"),
        ),
    ]

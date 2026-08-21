from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("academico", "0015_escola_defaults_neutros")]

    operations = [
        migrations.AlterModelOptions(
            name="alertaia",
            options={
                "ordering": ["-criado_em"],
                "verbose_name": "Alerta pedagógico",
                "verbose_name_plural": "Alertas pedagógicos",
            },
        ),
    ]

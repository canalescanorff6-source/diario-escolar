from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("academico", "0014_regras_academicas_e_multiplas_aulas")]

    operations = [
        migrations.AlterField(
            model_name="escola",
            name="estado_nome",
            field=models.CharField(blank=True, default="", max_length=160, verbose_name="Estado/órgão superior"),
        ),
        migrations.AlterField(
            model_name="escola",
            name="secretaria",
            field=models.CharField(blank=True, default="", max_length=180, verbose_name="Secretaria/órgão responsável"),
        ),
        migrations.AlterField(
            model_name="escola",
            name="estado",
            field=models.CharField(blank=True, default="", max_length=2),
        ),
    ]

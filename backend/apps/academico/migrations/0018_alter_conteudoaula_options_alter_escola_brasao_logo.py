from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academico", "0017_indices_consultas_frequentes"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="conteudoaula",
            options={"ordering": ["-data", "aula_numero"]},
        ),
        migrations.AlterField(
            model_name="escola",
            name="brasao_logo",
            field=models.ImageField(
                blank=True,
                help_text="Imagem institucional exibida na tela de login institucional.",
                null=True,
                upload_to="escolas/",
                verbose_name="Foto, logo ou brasão",
            ),
        ),
    ]

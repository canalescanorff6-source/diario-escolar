from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academico", "0013_escola_login_institucional"),
    ]

    operations = [
        migrations.AddField(
            model_name="escola",
            name="media_aprovacao",
            field=models.DecimalField(decimal_places=2, default=6.0, max_digits=4, verbose_name="Média mínima para aprovação"),
        ),
        migrations.AddField(
            model_name="escola",
            name="media_atencao",
            field=models.DecimalField(decimal_places=2, default=7.0, max_digits=4, verbose_name="Média de atenção pedagógica"),
        ),
        migrations.AddField(
            model_name="escola",
            name="frequencia_minima",
            field=models.DecimalField(decimal_places=2, default=75.0, max_digits=5, verbose_name="Frequência mínima (%)"),
        ),
        migrations.AddField(
            model_name="frequencia",
            name="aula_numero",
            field=models.PositiveSmallIntegerField(default=1, help_text="Permite registrar mais de uma aula da mesma disciplina no mesmo dia.", verbose_name="Aula/horário do dia"),
        ),
        migrations.AlterUniqueTogether(
            name="frequencia",
            unique_together={("aluno", "disciplina", "data", "aula_numero")},
        ),
        migrations.AddField(
            model_name="conteudoaula",
            name="quantidade_aulas",
            field=models.PositiveSmallIntegerField(default=1, help_text="Quantidade de aulas/tempos registrados neste lançamento."),
        ),
        migrations.AddField(
            model_name="conteudoaula",
            name="aula_numero",
            field=models.PositiveSmallIntegerField(default=1, help_text="Diferencia duas aulas da mesma disciplina no mesmo dia.", verbose_name="Aula/horário do dia"),
        ),
        migrations.AlterUniqueTogether(
            name="conteudoaula",
            unique_together={("professor", "turma", "disciplina", "data", "aula_numero")},
        ),
    ]

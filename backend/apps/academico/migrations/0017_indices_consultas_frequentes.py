from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("academico", "0016_alerta_pedagogico_verbose")]

    operations = [
        migrations.AddIndex(
            model_name="nota",
            index=models.Index(fields=["turma", "disciplina", "bimestre"], name="nota_turma_disc_bim"),
        ),
        migrations.AddIndex(
            model_name="frequencia",
            index=models.Index(fields=["turma", "data", "disciplina"], name="freq_turma_data_disc"),
        ),
        migrations.AddIndex(
            model_name="conteudoaula",
            index=models.Index(fields=["turma", "data", "disciplina"], name="cont_turma_data_disc"),
        ),
        migrations.AddIndex(
            model_name="professorturmadisciplina",
            index=models.Index(fields=["professor", "ativo", "turma"], name="vinc_prof_ativo_turma"),
        ),
        migrations.AddIndex(
            model_name="horarioaula",
            index=models.Index(fields=["professor", "ativo", "dia_semana"], name="hora_prof_ativo_dia"),
        ),
    ]

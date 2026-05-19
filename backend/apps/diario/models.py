from django.db import models

from apps.academico.models import Turma

from apps.usuarios.models import Usuario


class Diario(models.Model):

    STATUS_CHOICES = (
        ("RASCUNHO", "Rascunho"),
        ("CONCLUIDA", "Concluída"),
        ("REVISAO", "Enviar para revisão"),
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='diarios'
    )

    professor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    data = models.DateField()

    titulo = models.CharField(
        max_length=255
    )

    disciplina = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    bimestre = models.PositiveSmallIntegerField(
        default=1
    )

    quantidade_aulas = models.PositiveSmallIntegerField(
        default=1
    )

    conteudo = models.TextField()

    objetivos = models.TextField(
        blank=True,
        null=True
    )

    habilidades = models.TextField(
        blank=True,
        null=True
    )

    metodologia = models.TextField(
        blank=True,
        null=True
    )

    recursos = models.TextField(
        blank=True,
        null=True
    )

    avaliacao = models.TextField(
        blank=True,
        null=True
    )

    tarefa_casa = models.TextField(
        blank=True,
        null=True
    )

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="CONCLUIDA"
    )

    resumo_ia = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ['-data']

    def __str__(self):

        return f'{self.turma.nome} - {self.data}'

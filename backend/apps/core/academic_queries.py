"""Consultas acadêmicas reutilizadas nas áreas de professor e gestão."""

from apps.academico.models import Disciplina, HorarioAula, Turma


def turmas_do_professor(professor):
    return Turma.objects.filter(
        vinculos_professores__professor=professor,
        vinculos_professores__ativo=True,
    ).distinct()


def disciplinas_do_professor(professor):
    return Disciplina.objects.filter(
        vinculos_professores__professor=professor,
        vinculos_professores__ativo=True,
    ).distinct()


def horarios_do_professor(professor):
    return HorarioAula.objects.select_related("turma", "disciplina").filter(
        professor=professor,
        ativo=True,
    )

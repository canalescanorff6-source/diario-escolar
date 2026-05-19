from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from django.conf import settings
from django.db.models import Count

from apps.academico.models import (
    Aluno,
    AnoLetivo,
    ConteudoAula,
    Disciplina,
    Escola,
    FechamentoMensal,
    Frequencia,
    HorarioAula,
    ProfessorTurmaDisciplina,
    Turma,
)
from apps.diario.models import Diario


TURNOS_OFICIAIS = {
    "MATUTINO": {"label": "Manhã", "esperado": 5, "descricao": "1º ao 5º ano"},
    "VESPERTINO": {"label": "Tarde", "esperado": 8, "descricao": "6º ano ao 3ª série do Ensino Médio"},
    "NOTURNO": {"label": "Noite", "esperado": 5, "descricao": "EJA"},
}


def _nome_usuario(user):
    if not user:
        return "Não vinculado"
    return user.get_full_name() or user.username


def _disciplinas_turma(turma, professor=None):
    qs = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related("disciplina", "professor")
    if professor:
        qs = qs.filter(professor=professor)
    ids = list(qs.values_list("disciplina_id", flat=True).distinct())
    return Disciplina.objects.filter(id__in=ids).order_by("nome")


def _professores_turma(turma, professor=None):
    qs = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related("professor")
    if professor:
        qs = qs.filter(professor=professor)
    professores = []
    vistos = set()
    for vinculo in qs:
        if vinculo.professor_id not in vistos:
            vistos.add(vinculo.professor_id)
            professores.append(vinculo.professor)
    if not professores and turma.professor:
        professores = [turma.professor]
    return professores


def resumo_turma_diario_classe_1281(turma, professor=None, mes=None, ano=None):
    hoje = date.today()
    mes = int(mes or hoje.month)
    ano = int(ano or hoje.year)
    disciplinas = _disciplinas_turma(turma, professor)
    professores = _professores_turma(turma, professor)
    horarios = HorarioAula.objects.filter(turma=turma, ativo=True).select_related("disciplina", "professor")
    if professor:
        horarios = horarios.filter(professor=professor)

    freq = Frequencia.objects.filter(turma=turma, data__month=mes, data__year=ano)
    if disciplinas.exists():
        freq = freq.filter(disciplina__in=disciplinas)
    total_freq = freq.count()
    presencas = freq.filter(status="P").count()
    faltas = freq.filter(status="F").count()
    justificadas = freq.filter(status="FJ").count()
    percentual = round((presencas / total_freq) * 100, 1) if total_freq else 0

    conteudos = ConteudoAula.objects.filter(turma=turma, data__month=mes, data__year=ano)
    diarios = Diario.objects.filter(turma=turma, data__month=mes, data__year=ano)
    if professor:
        conteudos = conteudos.filter(professor=professor)
        diarios = diarios.filter(professor=professor)
    fechamentos = FechamentoMensal.objects.filter(turma=turma, mes=mes, ano=ano)
    if professor:
        fechamentos = fechamentos.filter(professor=professor)

    return {
        "turma": turma,
        "ano_letivo": turma.ano_letivo,
        "turno": turma.turno or "Sem turno",
        "professores": professores,
        "professores_nomes": ", ".join(_nome_usuario(p) for p in professores) or "Sem professor vinculado",
        "disciplinas": disciplinas,
        "disciplinas_nomes": ", ".join(d.nome for d in disciplinas) or "Sem disciplina vinculada",
        "total_alunos": turma.alunos.filter(ativo=True).count(),
        "total_disciplinas": disciplinas.count(),
        "total_professores": len(professores),
        "total_horarios": horarios.count(),
        "total_frequencias": total_freq,
        "presencas": presencas,
        "faltas": faltas,
        "justificadas": justificadas,
        "frequencia_percentual": percentual,
        "conteudos": conteudos.count(),
        "diarios": diarios.count(),
        "fechamentos": fechamentos.count(),
        "fechados": fechamentos.filter(status="FECHADO").count(),
        "horarios": horarios.order_by("dia_semana", "ordem")[:8],
        "pendencias": [
            texto for cond, texto in [
                (not professores, "Vincular professor"),
                (not disciplinas.exists(), "Vincular disciplinas"),
                (not horarios.exists(), "Cadastrar horários semanais"),
                (total_freq == 0, "Lançar frequência mensal P/F/FJ"),
                (conteudos.count() == 0, "Registrar aulas do mês"),
                (fechamentos.count() == 0, "Gerar fechamento mensal"),
            ] if cond
        ],
    }


def estrutura_turnos_1281():
    linhas = []
    for codigo, meta in TURNOS_OFICIAIS.items():
        turmas = Turma.objects.filter(turno=codigo, ativa=True).order_by("nome")
        linhas.append({
            "codigo": codigo,
            "label": meta["label"],
            "descricao": meta["descricao"],
            "esperado": meta["esperado"],
            "total": turmas.count(),
            "ok": turmas.count() >= meta["esperado"],
            "turmas": turmas,
        })
    return linhas


def cobertura_diario_classe_1281(professor=None, mes=None, ano=None):
    hoje = date.today()
    mes = int(mes or hoje.month)
    ano = int(ano or hoje.year)
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    ano_letivo = escola.ano_letivo_ativo if escola and escola.ano_letivo_ativo else AnoLetivo.objects.filter(ativo=True).first()
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    if professor:
        turmas = turmas.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct()
    turmas = turmas.order_by("turno", "nome")
    linhas = [resumo_turma_diario_classe_1281(t, professor=professor, mes=mes, ano=ano) for t in turmas]
    total_pendencias = sum(len(linha["pendencias"]) for linha in linhas)
    requisitos = [
        {"nome": "Escola cadastrada", "ok": bool(escola), "valor": escola.nome if escola else "Não cadastrada"},
        {"nome": "Ano letivo ativo", "ok": bool(ano_letivo), "valor": getattr(ano_letivo, "ano", "Não informado")},
        {"nome": "Turmas oficiais", "ok": Turma.objects.filter(ativa=True).count() >= 18, "valor": Turma.objects.filter(ativa=True).count()},
        {"nome": "Professores cadastrados pela gestão", "ok": ProfessorTurmaDisciplina.objects.exists(), "valor": ProfessorTurmaDisciplina.objects.values("professor_id").distinct().count()},
        {"nome": "Vínculos professor/turma/disciplina", "ok": ProfessorTurmaDisciplina.objects.filter(ativo=True).exists(), "valor": ProfessorTurmaDisciplina.objects.filter(ativo=True).count()},
        {"nome": "Horários semanais", "ok": HorarioAula.objects.filter(ativo=True).exists(), "valor": HorarioAula.objects.filter(ativo=True).count()},
        {"nome": "Frequência mensal P/F/FJ", "ok": Frequencia.objects.filter(data__month=mes, data__year=ano).exists(), "valor": Frequencia.objects.filter(data__month=mes, data__year=ano).count()},
        {"nome": "Registro mensal de aulas", "ok": ConteudoAula.objects.filter(data__month=mes, data__year=ano).exists() or Diario.objects.filter(data__month=mes, data__year=ano).exists(), "valor": ConteudoAula.objects.filter(data__month=mes, data__year=ano).count() + Diario.objects.filter(data__month=mes, data__year=ano).count()},
        {"nome": "Fechamento mensal oficial", "ok": FechamentoMensal.objects.filter(mes=mes, ano=ano).exists(), "valor": FechamentoMensal.objects.filter(mes=mes, ano=ano).count()},
        {"nome": "Sem importador Excel", "ok": not caminho_excel_antigo_existe(), "valor": "Gestão é a fonte oficial"},
    ]
    return {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "mes": mes,
        "ano": ano,
        "hoje": hoje,
        "linhas": linhas,
        "turnos": estrutura_turnos_1281(),
        "requisitos": requisitos,
        "ok_total": all(item["ok"] for item in requisitos) and total_pendencias == 0,
        "total_pendencias": total_pendencias,
        "totais": {
            "turmas": turmas.count(),
            "alunos": Aluno.objects.filter(ativo=True).count(),
            "disciplinas": Disciplina.objects.count(),
            "vinculos": ProfessorTurmaDisciplina.objects.filter(ativo=True).count(),
            "horarios": HorarioAula.objects.filter(ativo=True).count(),
            "frequencias": Frequencia.objects.filter(data__month=mes, data__year=ano).count(),
            "conteudos": ConteudoAula.objects.filter(data__month=mes, data__year=ano).count(),
            "diarios": Diario.objects.filter(data__month=mes, data__year=ano).count(),
            "fechamentos": FechamentoMensal.objects.filter(mes=mes, ano=ano).count(),
        },
    }


def caminho_excel_antigo_existe():
    base = Path(settings.BASE_DIR)
    root = base.parent
    alvos = [
        base / "escola.xlsx",
        root / "frontend",
        root / "static",
        base / "apps" / "importador",
        base / "templates" / "importador",
    ]
    return any(p.exists() for p in alvos)


def auditoria_sem_excel_1281():
    base = Path(settings.BASE_DIR)
    root = base.parent
    alvos = []
    for rel in ["escola.xlsx", "apps/importador", "templates/importador"]:
        alvos.append(base / rel)
    for rel in ["frontend", "static"]:
        alvos.append(root / rel)
    req = base / "requirements.txt"
    req_text = req.read_text(errors="ignore").lower() if req.exists() else ""
    return {
        "arquivos_antigos": [{"path": str(p), "existe": p.exists()} for p in alvos],
        "dependencias_excel": [dep for dep in ["pandas", "openpyxl"] if dep in req_text],
        "ok": not any(p.exists() for p in alvos) and "pandas" not in req_text and "openpyxl" not in req_text,
    }

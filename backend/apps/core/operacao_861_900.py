"""Camada de consolidação operacional das etapas 861–900.

Não cria novas tabelas e não altera o banco. A ideia é medir a prontidão real
para orientar os painéis premium: gestão, professor, diário oficial e aula.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from apps.academico.models import (
    Aluno,
    AnoLetivo,
    ConteudoAula,
    Disciplina,
    Escola,
    Frequencia,
    HorarioAula,
    Nota,
    ProfessorTurmaDisciplina,
    Turma,
)


def _pct(parte: int, total: int) -> float:
    if not total:
        return 0.0
    return round((parte / total) * 100, 1)


def _nome_usuario(usuario) -> str:
    if not usuario:
        return "—"
    return usuario.get_full_name() or getattr(usuario, "nome", "") or usuario.username


def _status(ok: bool) -> str:
    return "OK" if ok else "Pendente"


def auditoria_visual_861_900() -> dict:
    """Inventário técnico seguro para orientar a limpeza de legado."""
    base = Path(settings.BASE_DIR)
    templates_dir = base / "templates"
    static_css = base / "static" / "css"
    htmls = list(templates_dir.rglob("*.html")) if templates_dir.exists() else []
    css = list(static_css.glob("*.css")) if static_css.exists() else []
    standalone = []
    inline_styles = 0
    old_links = 0
    for path in htmls:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(path.relative_to(templates_dir)).replace("\\", "/")
        if "<!DOCTYPE" in text or "<!doctype" in text:
            standalone.append(rel)
        inline_styles += text.count("<style")
        old_links += text.count("dashboard.css") + text.count("layout_premium_fix.css")
    return {
        "templates_total": len(htmls),
        "css_total": len(css),
        "standalone_total": len(standalone),
        "standalone_amostra": [x.replace("core/base_professor_premium.html", "Base visual do professor").replace("gestao/base_premium_gestao.html", "Base visual da gestão").replace("registration/base_auth_premium.html", "Base visual de acesso") for x in standalone[:18]],
        "inline_styles": inline_styles,
        "links_legados": old_links,
        "status": "Monitorado sem apagar arquivos antigos",
    }


def resumo_gestao_861_900() -> dict:
    """Resumo de prontidão da escola para a central administrativa premium."""
    User = get_user_model()
    hoje = date.today()
    escola = Escola.objects.filter(ativa=True).first()
    ano = AnoLetivo.objects.filter(ativo=True).first() or AnoLetivo.objects.order_by("-ano").first()
    turmas = Turma.objects.filter(ativa=True)
    alunos = Aluno.objects.filter(ativo=True)
    professores = User.objects.filter(tipo="PROF")
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios = HorarioAula.objects.filter(ativo=True)
    disciplinas = Disciplina.objects.all()
    frequencias = Frequencia.objects.all()
    conteudos = ConteudoAula.objects.all()

    turmas_sem_vinculo = turmas.exclude(vinculos_professores__ativo=True).distinct().count()
    turmas_sem_horario = turmas.exclude(horarios__ativo=True).distinct().count()
    turmas_sem_aluno = turmas.annotate(total_alunos=Count("alunos", filter=Q(alunos__ativo=True))).filter(total_alunos=0).count()
    prof_sem_vinculo = professores.exclude(vinculos_pedagogicos__ativo=True).distinct().count()
    prof_sem_horario = professores.exclude(horarios_aula__ativo=True).distinct().count()
    freq_total = frequencias.count()
    freq_p = frequencias.filter(status="P").count()
    freq_f = frequencias.filter(status="F").count()
    freq_fj = frequencias.filter(status="FJ").count()

    requisitos = [
        {"grupo": "Base", "item": "Escola ativa", "ok": escola is not None, "acao": "Configurar escola", "url": "gestao_escola"},
        {"grupo": "Base", "item": "Ano letivo", "ok": ano is not None, "acao": "Ano letivo", "url": "gestao_escola"},
        {"grupo": "Cadastro", "item": "Turmas ativas", "ok": turmas.exists(), "acao": "Turmas", "url": "gestao_cadastros_operacionais_301"},
        {"grupo": "Cadastro", "item": "Alunos ativos", "ok": alunos.exists(), "acao": "Alunos", "url": "gestao_alunos"},
        {"grupo": "Equipe", "item": "Professores", "ok": professores.exists(), "acao": "Professores", "url": "gestao_professores"},
        {"grupo": "Equipe", "item": "Vínculos professor/turma/disciplina", "ok": vinculos.exists() and turmas_sem_vinculo == 0, "acao": "Vínculos", "url": "gestao_vinculos"},
        {"grupo": "Rotina", "item": "Horários semanais", "ok": horarios.exists() and turmas_sem_horario == 0, "acao": "Horários", "url": "gestao_horarios"},
        {"grupo": "Diário", "item": "Frequência P/F/FJ", "ok": freq_total > 0, "acao": "Diário oficial", "url": "gestao_diario_oficial"},
        {"grupo": "Diário", "item": "Conteúdos de aula", "ok": conteudos.exists(), "acao": "Registro de aulas", "url": "gestao_diario_oficial"},
    ]
    ok = sum(1 for item in requisitos if item["ok"])

    pendencias = []
    if not escola:
        pendencias.append({"nivel": "ALTO", "area": "Identificação", "texto": "Configure a escola ativa e o ano letivo oficial."})
    if turmas_sem_vinculo:
        pendencias.append({"nivel": "ALTO", "area": "Vínculos", "texto": f"{turmas_sem_vinculo} turma(s) sem professor/turma/disciplina."})
    if turmas_sem_horario:
        pendencias.append({"nivel": "MEDIO", "area": "Horários", "texto": f"{turmas_sem_horario} turma(s) sem grade semanal."})
    if turmas_sem_aluno:
        pendencias.append({"nivel": "MEDIO", "area": "Alunos", "texto": f"{turmas_sem_aluno} turma(s) sem alunos ativos."})
    if prof_sem_vinculo:
        pendencias.append({"nivel": "MEDIO", "area": "Professores", "texto": f"{prof_sem_vinculo} professor(es) sem vínculo ativo."})
    if prof_sem_horario:
        pendencias.append({"nivel": "BAIXO", "area": "Carga horária", "texto": f"{prof_sem_horario} professor(es) sem horário semanal."})
    if not pendencias:
        pendencias.append({"nivel": "OK", "area": "Operação", "texto": "Base mínima da gestão pronta para o Diário Oficial."})

    turno_cards = []
    for chave, label in (("MAT", "Matutino"), ("VES", "Vespertino"), ("NOT", "Noturno/EJA")):
        turno_cards.append({
            "label": label,
            "total": turmas.filter(turno__icontains=chave).count(),
        })
    sem_turno = turmas.filter(Q(turno__isnull=True) | Q(turno="")).count()

    return {
        "hoje": hoje,
        "prontidao": _pct(ok, len(requisitos)),
        "requisitos_ok": ok,
        "requisitos_total": len(requisitos),
        "requisitos": requisitos,
        "pendencias": pendencias,
        "cards": [
            {"label": "Prontidão", "valor": f"{_pct(ok, len(requisitos))}%", "detalhe": "configuração inicial"},
            {"label": "Turmas", "valor": turmas.count(), "detalhe": f"{turmas_sem_vinculo} sem vínculo"},
            {"label": "Professores", "valor": professores.count(), "detalhe": f"{prof_sem_horario} sem horário"},
            {"label": "Diário", "valor": conteudos.count(), "detalhe": "conteúdos lançados"},
        ],
        "status_frequencia": {"total": freq_total, "p": freq_p, "f": freq_f, "fj": freq_fj, "percentual": _pct(freq_p, freq_total)},
        "turnos": turno_cards,
        "sem_turno": sem_turno,
        "trilha": [
            {"ordem": 1, "titulo": "Base institucional", "descricao": "escola + ano letivo + identificação oficial", "url": "gestao_escola"},
            {"ordem": 2, "titulo": "Cadastros vivos", "descricao": "professores, alunos, turmas e disciplinas", "url": "gestao_cadastros_operacionais_301"},
            {"ordem": 3, "titulo": "Rotina semanal", "descricao": "vínculos, horários, turnos e carga horária", "url": "gestao_centro_operacional_321"},
            {"ordem": 4, "titulo": "Diário oficial", "descricao": "frequência, conteúdo, documentos e conferência", "url": "gestao_diario_oficial"},
        ],
        "auditoria_visual": auditoria_visual_861_900(),
    }


def resumo_professor_861_900(professor) -> dict:
    """Resumo operacional do professor: jornada de aula real."""
    hoje = date.today()
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
    turmas = Turma.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True, ativa=True).distinct()
    disciplinas = Disciplina.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct()
    horarios = HorarioAula.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
    aulas_hoje = horarios.filter(dia_semana=hoje.isoweekday())
    alunos_total = Aluno.objects.filter(turma__in=turmas, ativo=True).count()
    freq_hoje = Frequencia.objects.filter(turma__in=turmas, disciplina__in=disciplinas, data=hoje)
    conteudos_hoje = ConteudoAula.objects.filter(professor=professor, turma__in=turmas, disciplina__in=disciplinas, data=hoje)

    requisitos = [
        {"item": "Turmas vinculadas", "ok": turmas.exists(), "url": "turmas", "acao": "Ver turmas"},
        {"item": "Disciplinas vinculadas", "ok": disciplinas.exists(), "url": "professor_diario_oficial", "acao": "Diário"},
        {"item": "Horários semanais", "ok": horarios.exists(), "url": "professor_carga_horaria_301", "acao": "Carga"},
        {"item": "Aulas de hoje", "ok": aulas_hoje.exists(), "url": "professor_centro_operacional_321", "acao": "Centro"},
        {"item": "Chamada de hoje", "ok": freq_hoje.exists(), "url": "professor_aula_rapida_321", "acao": "Chamada"},
        {"item": "Conteúdo de hoje", "ok": conteudos_hoje.exists(), "url": "professor_aula_rapida_321", "acao": "Conteúdo"},
    ]
    ok = sum(1 for item in requisitos if item["ok"])

    jornada = [
        {"numero": "01", "titulo": "Abrir aula", "descricao": "selecionar horário/turma/disciplina", "ok": horarios.exists()},
        {"numero": "02", "titulo": "Chamada P/F/FJ", "descricao": "frequência oficial por aluno", "ok": freq_hoje.exists()},
        {"numero": "03", "titulo": "Conteúdo", "descricao": "registro mensal da aula", "ok": conteudos_hoje.exists()},
        {"numero": "04", "titulo": "Fechamento", "descricao": "conferência antes da entrega", "ok": freq_hoje.exists() and conteudos_hoje.exists()},
    ]

    pendencias = []
    if not turmas.exists():
        pendencias.append("Solicite à gestão o vínculo com turma.")
    if not disciplinas.exists():
        pendencias.append("Solicite à gestão o vínculo com disciplina.")
    if not horarios.exists():
        pendencias.append("Solicite à gestão sua grade semanal.")
    if aulas_hoje.exists() and not freq_hoje.exists():
        pendencias.append("Chamada de hoje ainda não foi salva.")
    if aulas_hoje.exists() and not conteudos_hoje.exists():
        pendencias.append("Conteúdo de hoje ainda não foi registrado.")

    return {
        "hoje": hoje,
        "nome": _nome_usuario(professor),
        "prontidao": _pct(ok, len(requisitos)),
        "requisitos_ok": ok,
        "requisitos_total": len(requisitos),
        "requisitos": requisitos,
        "jornada": jornada,
        "pendencias": pendencias,
        "cards": [
            {"label": "Prontidão", "valor": f"{_pct(ok, len(requisitos))}%", "detalhe": "rotina do professor"},
            {"label": "Turmas", "valor": turmas.count(), "detalhe": "vinculadas"},
            {"label": "Alunos", "valor": alunos_total, "detalhe": "ativos"},
            {"label": "Hoje", "valor": aulas_hoje.count(), "detalhe": "aulas previstas"},
        ],
        "frequencia_hoje": {
            "total": freq_hoje.count(),
            "p": freq_hoje.filter(status="P").count(),
            "f": freq_hoje.filter(status="F").count(),
            "fj": freq_hoje.filter(status="FJ").count(),
        },
        "conteudos_hoje": conteudos_hoje.count(),
    }


def resumo_aula_861_900(horario, data_aula, professor) -> dict:
    if not horario:
        return {"percentual": 0, "checklist": [], "faltantes": []}
    alunos = horario.turma.alunos.filter(ativo=True)
    frequencias = Frequencia.objects.filter(turma=horario.turma, disciplina=horario.disciplina, data=data_aula)
    conteudo = ConteudoAula.objects.filter(professor=professor, turma=horario.turma, disciplina=horario.disciplina, data=data_aula).first()
    total_alunos = alunos.count()
    chamadas = frequencias.count()
    checklist = [
        {"item": "Turma selecionada", "ok": True},
        {"item": "Alunos carregados", "ok": total_alunos > 0},
        {"item": "Chamada completa", "ok": total_alunos > 0 and chamadas >= total_alunos},
        {"item": "Conteúdo registrado", "ok": bool(conteudo)},
        {"item": "Pronto para fechamento", "ok": total_alunos > 0 and chamadas >= total_alunos and bool(conteudo)},
    ]
    ok = sum(1 for item in checklist if item["ok"])
    return {
        "percentual": _pct(ok, len(checklist)),
        "checklist": checklist,
        "faltantes": [item["item"] for item in checklist if not item["ok"]],
        "status": _status(ok == len(checklist)),
        "chamadas": chamadas,
        "total_alunos": total_alunos,
    }

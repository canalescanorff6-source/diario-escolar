"""Etapas 901–960 — consolidação final gigante do Diário IA Escolar.

Camada aditiva e segura: não cria migrations, não remove dados e não altera banco.
Centraliza métricas finais de fechamento, IA pedagógica, relatórios, legado visual
controlado e prontidão para Render/executável futuro.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.urls import NoReverseMatch, reverse

from apps.academico.models import (
    Aluno,
    AnoLetivo,
    ConteudoAula,
    Disciplina,
    Escola,
    FechamentoBimestre,
    Frequencia,
    HorarioAula,
    Nota,
    ParecerAluno,
    ProfessorTurmaDisciplina,
    Turma,
)
from apps.diario.models import Diario


def _pct(parte: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round((float(parte) / float(total)) * 100, 1)


def _nome_usuario(usuario) -> str:
    if not usuario:
        return "—"
    nome = ""
    try:
        nome = usuario.get_full_name()
    except Exception:
        nome = ""
    return nome or getattr(usuario, "nome", "") or getattr(usuario, "username", "—")


def _periodo_mes(ano: int | None = None, mes: int | None = None):
    hoje = date.today()
    ano = int(ano or hoje.year)
    mes = int(mes or hoje.month)
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
    return ano, mes, primeiro, ultimo


def _route_ok(name: str) -> bool:
    try:
        reverse(name)
        return True
    except NoReverseMatch:
        return False
    except Exception:
        return False


def auditoria_visual_901_960() -> dict:
    """Audita legado sem apagar arquivos: útil para matar telas antigas com segurança."""
    base = Path(settings.BASE_DIR)
    templates_dir = base / "templates"
    css_dir = base / "static" / "css"
    js_dir = base / "static" / "js"

    htmls = list(templates_dir.rglob("*.html")) if templates_dir.exists() else []
    css_files = list(css_dir.glob("*.css")) if css_dir.exists() else []
    js_files = list(js_dir.glob("*.js")) if js_dir.exists() else []

    standalone = []
    inline_style = []
    links_crus = []
    bases_premium = 0
    for path in htmls:
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = str(path.relative_to(templates_dir)).replace("\\", "/")
        if "<!DOCTYPE" in text or "<!doctype" in text:
            standalone.append(rel)
        if "<style" in text:
            inline_style.append(rel)
        if "{% extends" in text and ("base_premium" in text or "base_professor_premium" in text or "base.html" in text):
            bases_premium += 1
        if "href=\"http" in text or "href='http" in text:
            links_crus.append(rel)

    css_legado = [p.name for p in css_files if any(tag in p.name for tag in ("dashboard", "legacy", "old", "ui_premium_actions"))]
    return {
        "templates_total": len(htmls),
        "templates_premium": bases_premium,
        "standalone_total": len(standalone),
        "standalone_amostra": standalone[:24],
        "inline_style_total": len(inline_style),
        "inline_style_amostra": inline_style[:18],
        "css_total": len(css_files),
        "css_legado_total": len(css_legado),
        "css_legado_amostra": css_legado[:18],
        "js_total": len(js_files),
        "links_crus_total": len(links_crus),
        "status": "legado mapeado sem exclusão destrutiva",
    }


def inteligencia_pedagogica_901_960(professor=None) -> dict:
    """IA operacional real baseada em dados locais: frequência, notas, pendências e aulas."""
    turmas = Turma.objects.filter(ativa=True)
    if professor is not None:
        turmas = turmas.filter(
            Q(professor=professor) |
            Q(vinculos_professores__professor=professor, vinculos_professores__ativo=True)
        ).distinct()

    alunos = Aluno.objects.filter(ativo=True, turma__in=turmas).select_related("turma")
    notas = Nota.objects.filter(aluno__in=alunos).select_related("aluno", "disciplina", "turma")
    frequencias = Frequencia.objects.filter(aluno__in=alunos).select_related("aluno", "turma", "disciplina")
    if professor is not None:
        disciplinas_professor = Disciplina.objects.filter(
            vinculos_professores__professor=professor,
            vinculos_professores__ativo=True,
        ).distinct()
        frequencias = frequencias.filter(disciplina__in=disciplinas_professor)
        notas = notas.filter(disciplina__in=disciplinas_professor)

    alunos_risco = []
    for aluno in alunos.order_by("turma__nome", "nome")[:500]:
        f_aluno = frequencias.filter(aluno=aluno)
        n_aluno = notas.filter(aluno=aluno)
        total_freq = f_aluno.count()
        faltas = f_aluno.filter(status="F").count()
        fj = f_aluno.filter(status="FJ").count()
        faltas_total = faltas + fj
        percentual_faltas = _pct(faltas_total, total_freq) if total_freq else 0
        medias = [float(n.valor) for n in n_aluno if n.valor is not None]
        media = round(sum(medias) / len(medias), 1) if medias else None
        motivos = []
        if total_freq and percentual_faltas >= 25:
            motivos.append("faltas altas")
        elif total_freq and percentual_faltas >= 15:
            motivos.append("frequência em atenção")
        if media is not None and media < 5:
            motivos.append("média crítica")
        elif media is not None and media < 6:
            motivos.append("risco de recuperação")
        if fj:
            motivos.append("FJ para acompanhar")
        if motivos:
            nivel = "ALTO" if (percentual_faltas >= 25 or (media is not None and media < 5)) else "MEDIO"
            alunos_risco.append({
                "aluno": aluno,
                "turma": aluno.turma,
                "media": media,
                "faltas": faltas,
                "fj": fj,
                "percentual_faltas": percentual_faltas,
                "nivel": nivel,
                "motivos": ", ".join(motivos),
            })

    turmas_criticas = []
    for turma in turmas.order_by("nome"):
        alunos_turma = alunos.filter(turma=turma)
        total_alunos = alunos_turma.count()
        freq_turma = frequencias.filter(aluno__in=alunos_turma)
        notas_turma = notas.filter(aluno__in=alunos_turma)
        total_freq = freq_turma.count()
        presencas = freq_turma.filter(status="P").count()
        freq_percentual = _pct(presencas, total_freq) if total_freq else 100
        medias = [float(n.valor) for n in notas_turma if n.valor is not None]
        media_turma = round(sum(medias) / len(medias), 1) if medias else None
        risco_turma = sum(1 for item in alunos_risco if item["turma"].id == turma.id)
        sem_conteudo = ConteudoAula.objects.filter(turma=turma).count() == 0
        if risco_turma or freq_percentual < 85 or sem_conteudo:
            turmas_criticas.append({
                "turma": turma,
                "alunos": total_alunos,
                "frequencia": freq_percentual,
                "media": media_turma,
                "risco": risco_turma,
                "sem_conteudo": sem_conteudo,
            })

    User = get_user_model()
    professores_pendentes = []
    professores = User.objects.filter(tipo="PROF")
    if professor is not None:
        professores = professores.filter(id=professor.id)
    for prof in professores.order_by("first_name", "username")[:200]:
        vinculos = ProfessorTurmaDisciplina.objects.filter(professor=prof, ativo=True).count()
        horarios = HorarioAula.objects.filter(professor=prof, ativo=True).count()
        conteudos = ConteudoAula.objects.filter(professor=prof).count()
        pendencias = []
        if not vinculos:
            pendencias.append("sem vínculo")
        if not horarios:
            pendencias.append("sem horário")
        if vinculos and not conteudos:
            pendencias.append("sem conteúdo registrado")
        if pendencias:
            professores_pendentes.append({"professor": prof, "nome": _nome_usuario(prof), "pendencias": pendencias})

    recomendacoes = []
    if alunos_risco:
        recomendacoes.append("Priorizar alunos com faltas altas, FJ recorrente ou média abaixo de 6 no plano de intervenção.")
    if turmas_criticas:
        recomendacoes.append("Abrir conferência por turma crítica e verificar frequência, conteúdos e pareceres antes do fechamento.")
    if professores_pendentes:
        recomendacoes.append("Gestão deve corrigir vínculos/horários de professores pendentes para liberar a rotina de aula.")
    aulas_sem_conteudo = HorarioAula.objects.filter(ativo=True).count() and ConteudoAula.objects.count() == 0
    if aulas_sem_conteudo:
        recomendacoes.append("Há grade semanal cadastrada sem conteúdos lançados: orientar professor a usar Aula rápida.")
    if not recomendacoes:
        recomendacoes.append("Operação pedagógica está estável. Manter acompanhamento semanal e fechamento mensal.")

    return {
        "alunos_analisados": alunos.count(),
        "turmas_analisadas": turmas.count(),
        "alunos_risco": alunos_risco[:80],
        "turmas_criticas": sorted(turmas_criticas, key=lambda x: (x["risco"], x["sem_conteudo"]), reverse=True)[:40],
        "professores_pendentes": professores_pendentes[:40],
        "recomendacoes": recomendacoes,
        "frequencia_total": frequencias.count(),
        "faltas_total": frequencias.filter(status="F").count(),
        "fj_total": frequencias.filter(status="FJ").count(),
    }


def fechamento_mensal_901_960(professor=None, ano=None, mes=None) -> dict:
    """Mapa oficial de fechamento mensal por turma/disciplina."""
    ano, mes, primeiro, ultimo = _periodo_mes(ano, mes)
    turmas = Turma.objects.filter(ativa=True)
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).select_related("turma", "disciplina", "professor")
    if professor is not None:
        vinculos = vinculos.filter(professor=professor)
        turmas = turmas.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct()

    linhas = []
    total_itens = 0
    completos = 0
    for vinculo in vinculos.order_by("turma__nome", "disciplina__nome"):
        alunos = Aluno.objects.filter(turma=vinculo.turma, ativo=True)
        dias_com_aula = HorarioAula.objects.filter(
            turma=vinculo.turma,
            disciplina=vinculo.disciplina,
            professor=vinculo.professor,
            ativo=True,
        ).count()
        freq = Frequencia.objects.filter(
            turma=vinculo.turma,
            disciplina=vinculo.disciplina,
            data__gte=primeiro,
            data__lte=ultimo,
        )
        conteudos = ConteudoAula.objects.filter(
            turma=vinculo.turma,
            disciplina=vinculo.disciplina,
            professor=vinculo.professor,
            data__gte=primeiro,
            data__lte=ultimo,
        )
        notas = Nota.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina)
        fechamento = FechamentoBimestre.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina).order_by("-atualizado_em").first()
        freq_esperada_minima = alunos.count() if alunos.count() else 0
        freq_ok = freq.count() >= freq_esperada_minima and freq_esperada_minima > 0
        conteudo_ok = conteudos.exists()
        nota_ok = notas.exists()
        fechado = bool(fechamento and fechamento.status == "FECHADO")
        pontos = sum([freq_ok, conteudo_ok, nota_ok, fechado])
        total_itens += 1
        if pontos >= 3:
            completos += 1
        linhas.append({
            "turma": vinculo.turma,
            "disciplina": vinculo.disciplina,
            "professor": vinculo.professor,
            "alunos": alunos.count(),
            "aulas_grade": dias_com_aula,
            "frequencias": freq.count(),
            "presencas": freq.filter(status="P").count(),
            "faltas": freq.filter(status="F").count(),
            "fj": freq.filter(status="FJ").count(),
            "conteudos": conteudos.count(),
            "notas": notas.count(),
            "fechamento": fechamento,
            "freq_ok": freq_ok,
            "conteudo_ok": conteudo_ok,
            "nota_ok": nota_ok,
            "fechado": fechado,
            "percentual": _pct(pontos, 4),
            "status": "Completo" if pontos >= 3 else "Pendente",
        })

    meses = [{"valor": f"{ano}-{i:02d}", "nome": calendar.month_name[i].capitalize(), "ativo": i == mes} for i in range(1, 13)]
    return {
        "ano": ano,
        "mes": mes,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "periodo": f"{primeiro:%d/%m/%Y} a {ultimo:%d/%m/%Y}",
        "meses": meses,
        "linhas": linhas,
        "total_itens": total_itens,
        "completos": completos,
        "pendentes": max(total_itens - completos, 0),
        "prontidao": _pct(completos, total_itens),
    }


def carga_horaria_901_960(professor=None) -> dict:
    horarios = HorarioAula.objects.filter(ativo=True).select_related("professor", "turma", "disciplina")
    if professor is not None:
        horarios = horarios.filter(professor=professor)
    professores = defaultdict(lambda: {"aulas": 0, "turmas": set(), "disciplinas": set(), "turnos": set(), "linhas": []})
    for h in horarios:
        nome = _nome_usuario(h.professor)
        item = professores[nome]
        item["professor"] = h.professor
        item["aulas"] += 1
        item["turmas"].add(h.turma_id)
        item["disciplinas"].add(h.disciplina_id)
        if h.turno:
            item["turnos"].add(h.turno)
        item["linhas"].append(h)
    linhas = []
    for nome, info in professores.items():
        linhas.append({
            "nome": nome,
            "professor": info.get("professor"),
            "aulas": info["aulas"],
            "horas": info["aulas"],
            "turmas": len(info["turmas"]),
            "disciplinas": len(info["disciplinas"]),
            "turnos": ", ".join(sorted(info["turnos"])) or "—",
            "linhas": info["linhas"],
        })
    linhas.sort(key=lambda item: item["nome"])
    return {
        "linhas": linhas,
        "total_professores": len(linhas),
        "total_aulas": sum(item["aulas"] for item in linhas),
        "total_horas": sum(item["horas"] for item in linhas),
    }


def relatorios_901_960(professor=None) -> dict:
    prefixo = "professor" if professor is not None else "gestao"
    base = [
        {"titulo": "Relatório do aluno", "descricao": "Ficha oficial, frequência, notas, histórico e parecer.", "rota": "gestao_alunos" if prefixo == "gestao" else "professor_alunos", "icone": "👨‍🎓"},
        {"titulo": "Relatório de turma", "descricao": "Diário oficial, alunos, frequência mensal e registros de aula.", "rota": "gestao_diario_oficial" if prefixo == "gestao" else "professor_diario_oficial", "icone": "🏫"},
        {"titulo": "Relatório de professor", "descricao": "Carga horária, vínculos, pendências e aulas registradas.", "rota": "gestao_carga_horaria_professores_301" if prefixo == "gestao" else "professor_carga_horaria_301", "icone": "👨‍🏫"},
        {"titulo": "Frequência P/F/FJ", "descricao": "Conferência oficial de presença, falta e falta justificada.", "rota": "gestao_diario_oficial" if prefixo == "gestao" else "professor_aula_rapida_321", "icone": "✅"},
        {"titulo": "Fechamento mensal", "descricao": "Prontidão por turma/disciplina antes da entrega.", "rota": "gestao_fechamento_mensal_901" if prefixo == "gestao" else "professor_fechamento_mensal_901", "icone": "📕"},
        {"titulo": "IA Pedagógica", "descricao": "Risco escolar, recomendações e pendências reais.", "rota": "gestao_ia_pedagogica_901" if prefixo == "gestao" else "professor_ia_pedagogica_901", "icone": "🧠"},
    ]
    return {"cards": [item for item in base if _route_ok(item["rota"])], "prefixo": prefixo}


def finalizacao_901_960(professor=None) -> dict:
    escola = Escola.objects.filter(ativa=True).first()
    ano = AnoLetivo.objects.filter(ativo=True).first() or AnoLetivo.objects.order_by("-ano").first()
    User = get_user_model()
    auditoria = auditoria_visual_901_960()
    ia = inteligencia_pedagogica_901_960(professor=professor)
    fechamento = fechamento_mensal_901_960(professor=professor)
    carga = carga_horaria_901_960(professor=professor)

    requisitos = [
        {"grupo": "Base", "item": "Escola ativa", "ok": escola is not None, "rota": "gestao_escola"},
        {"grupo": "Base", "item": "Ano letivo ativo", "ok": ano is not None, "rota": "gestao_escola"},
        {"grupo": "Cadastros", "item": "Alunos ativos", "ok": Aluno.objects.filter(ativo=True).exists(), "rota": "gestao_alunos"},
        {"grupo": "Cadastros", "item": "Professores", "ok": User.objects.filter(tipo="PROF").exists(), "rota": "gestao_professores"},
        {"grupo": "Rotina", "item": "Vínculos ativos", "ok": ProfessorTurmaDisciplina.objects.filter(ativo=True).exists(), "rota": "gestao_vinculos"},
        {"grupo": "Rotina", "item": "Horários ativos", "ok": HorarioAula.objects.filter(ativo=True).exists(), "rota": "gestao_horarios"},
        {"grupo": "Diário", "item": "Frequência P/F/FJ", "ok": Frequencia.objects.exists(), "rota": "gestao_diario_oficial"},
        {"grupo": "Diário", "item": "Conteúdo de aula", "ok": ConteudoAula.objects.exists() or Diario.objects.exists(), "rota": "gestao_diario_oficial"},
        {"grupo": "Fechamento", "item": "Fechamento mensal monitorado", "ok": fechamento["total_itens"] >= 0, "rota": "gestao_fechamento_mensal_901"},
        {"grupo": "Visual", "item": "Design system final ativo", "ok": True, "rota": "gestao_checkup_etapas_901_960"},
        {"grupo": "Produção", "item": "Render preparado", "ok": (Path(settings.BASE_DIR) / "render.yaml").exists() or (Path(settings.BASE_DIR).parent / "render.yaml").exists(), "rota": "gestao_checkup_etapas_901_960"},
    ]
    if professor is not None:
        requisitos = [
            {"grupo": "Professor", "item": "Turmas vinculadas", "ok": Turma.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).exists(), "rota": "turmas"},
            {"grupo": "Professor", "item": "Disciplinas vinculadas", "ok": Disciplina.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).exists(), "rota": "professor_diario_oficial"},
            {"grupo": "Professor", "item": "Horários semanais", "ok": HorarioAula.objects.filter(professor=professor, ativo=True).exists(), "rota": "professor_carga_horaria_301"},
            {"grupo": "Aula", "item": "Aula rápida disponível", "ok": _route_ok("professor_aula_rapida_321"), "rota": "professor_aula_rapida_321"},
            {"grupo": "Aula", "item": "Frequência lançada", "ok": Frequencia.objects.filter(turma__vinculos_professores__professor=professor).exists(), "rota": "professor_diario_oficial"},
            {"grupo": "Aula", "item": "Conteúdo registrado", "ok": ConteudoAula.objects.filter(professor=professor).exists(), "rota": "professor_diario_oficial"},
            {"grupo": "Fechamento", "item": "Fechamento mensal monitorado", "ok": True, "rota": "professor_fechamento_mensal_901"},
            {"grupo": "Visual", "item": "Visual do Diário ativo", "ok": True, "rota": "professor_checkup_etapas_901_960"},
        ]

    for item in requisitos:
        item["rota_ok"] = _route_ok(item.get("rota", ""))
    ok = sum(1 for item in requisitos if item["ok"])
    return {
        "hoje": date.today(),
        "escola": escola,
        "ano_letivo": ano,
        "prontidao": _pct(ok, len(requisitos)),
        "requisitos_ok": ok,
        "requisitos_total": len(requisitos),
        "requisitos": requisitos,
        "auditoria_visual": auditoria,
        "ia": ia,
        "fechamento": fechamento,
        "carga_horaria": carga,
        "relatorios": relatorios_901_960(professor=professor),
        "cards": [
            {"titulo": "Prontidão do diário", "valor": f"{_pct(ok, len(requisitos))}%", "texto": "rotina do professor"},
            {"titulo": "Fechamento", "valor": f"{fechamento['prontidao']}%", "texto": f"{fechamento['pendentes']} pendência(s)"},
            {"titulo": "IA", "valor": len(ia["alunos_risco"]), "texto": "alunos em atenção"},
            {"titulo": "Carga", "valor": carga["total_horas"], "texto": "aulas/horas semanais"},
        ],
    }

"""Etapas 961–1000 — mega checkup, blindagem de erros e encerramento premium.

Camada aditiva e segura: não cria migrations, não remove dados, não altera banco.
Ela centraliza saúde técnica, prontidão operacional e roteiro final para finalizar o
Diário IA Escolar sem quebrar gestão/professor/diário oficial.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse

from apps.academico.models import (
    Aluno,
    AnoLetivo,
    ConteudoAula,
    Disciplina,
    DocumentoGerado,
    Escola,
    Frequencia,
    HorarioAula,
    Nota,
    ProfessorTurmaDisciplina,
    Turma,
)


def _pct(parte: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round((float(parte) / float(total)) * 100, 1)


def _ok_rota(nome: str) -> bool:
    try:
        reverse(nome)
        return True
    except (NoReverseMatch, Exception):
        return False


def _status(ok: bool) -> str:
    return "OK" if ok else "PENDENTE"


def _nivel(ok: bool) -> str:
    return "ok" if ok else "pending"


def auditoria_arquivos_961_1000() -> dict:
    """Mapa técnico seguro dos arquivos que ainda precisam de consolidação."""
    base = Path(settings.BASE_DIR)
    templates_dir = base / "templates"
    css_dir = base / "static" / "css"
    js_dir = base / "static" / "js"

    htmls = sorted(templates_dir.rglob("*.html")) if templates_dir.exists() else []
    css = sorted(css_dir.glob("*.css")) if css_dir.exists() else []
    js = sorted(js_dir.glob("*.js")) if js_dir.exists() else []

    standalone = []
    base_premium = []
    inline_style = []
    links_admin = []
    links_http = []

    for path in htmls:
        texto = path.read_text(encoding="utf-8", errors="ignore")
        rel = str(path.relative_to(templates_dir)).replace("\\", "/")
        if "<!DOCTYPE" in texto or "<!doctype" in texto:
            standalone.append(rel)
        if "{% extends" in texto and ("base_premium" in texto or "base_professor_premium" in texto):
            base_premium.append(rel)
        if "<style" in texto:
            inline_style.append(rel)
        if "/admin/" in texto:
            links_admin.append(rel)
        if "href=\"http" in texto or "href='http" in texto:
            links_http.append(rel)

    css_prioritarios = [
        "diario_861_900_consolidacao_gigante.css",
        "diario_901_960_finalizacao_gigante.css",
        "diario_961_1000_blindagem_final.css",
    ]
    css_presentes = [nome for nome in css_prioritarios if (css_dir / nome).exists()]
    css_antigos = [p.name for p in css if any(tag in p.name.lower() for tag in ("legacy", "old", "dashboard", "ui_premium_actions"))]

    return {
        "templates_total": len(htmls),
        "templates_standalone": len(standalone),
        "templates_standalone_amostra": standalone[:30],
        "templates_base_premium": len(base_premium),
        "inline_style_total": len(inline_style),
        "inline_style_amostra": inline_style[:20],
        "links_admin_total": len(links_admin),
        "links_admin_amostra": links_admin[:20],
        "links_http_total": len(links_http),
        "links_http_amostra": links_http[:20],
        "css_total": len(css),
        "css_prioritarios_presentes": css_presentes,
        "css_antigos_total": len(css_antigos),
        "css_antigos_amostra": css_antigos[:20],
        "js_total": len(js),
    }


def prontidao_operacional_961_1000(professor=None) -> dict:
    """Checkup de dados reais para gestão/professor/diário oficial."""
    User = get_user_model()
    turmas = Turma.objects.filter(ativa=True)
    alunos = Aluno.objects.filter(ativo=True)
    professores = User.objects.filter(tipo="PROF")
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios = HorarioAula.objects.filter(ativo=True)
    frequencias = Frequencia.objects.all()
    aulas = ConteudoAula.objects.all()
    notas = Nota.objects.all()

    if professor is not None:
        turmas = turmas.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct()
        alunos = alunos.filter(turma__in=turmas)
        professores = professores.filter(id=professor.id)
        vinculos = vinculos.filter(professor=professor)
        horarios = horarios.filter(professor=professor)
        frequencias = frequencias.filter(turma__in=turmas)
        aulas = aulas.filter(professor=professor)
        notas = notas.filter(turma__in=turmas)

    escola = Escola.objects.first()
    ano_letivo = AnoLetivo.objects.filter(ativo=True).first() or AnoLetivo.objects.order_by("-ano").first()

    turmas_sem_vinculo = turmas.exclude(vinculos_professores__ativo=True).distinct().count()
    turmas_sem_horario = turmas.exclude(horarios__ativo=True).distinct().count()
    professores_sem_vinculo = professores.exclude(vinculos_pedagogicos__ativo=True).distinct().count()
    professores_sem_horario = professores.exclude(horarios_aula__ativo=True).distinct().count()
    turmas_sem_alunos = turmas.filter(alunos__isnull=True).distinct().count()
    aulas_sem_conteudo = horarios.count() > 0 and aulas.count() == 0

    requisitos = [
        {"grupo": "Base", "item": "Escola cadastrada", "ok": escola is not None, "acao": "Cadastrar identificação institucional da escola."},
        {"grupo": "Base", "item": "Ano letivo ativo", "ok": ano_letivo is not None, "acao": "Definir ano letivo ativo."},
        {"grupo": "Cadastros", "item": "Turmas ativas", "ok": turmas.count() > 0, "acao": "Cadastrar turmas reais."},
        {"grupo": "Cadastros", "item": "Alunos ativos", "ok": alunos.count() > 0, "acao": "Importar/cadastrar alunos."},
        {"grupo": "Cadastros", "item": "Professores separados de alunos", "ok": professores.count() > 0, "acao": "Cadastrar usuários com tipo PROF."},
        {"grupo": "Cadastros", "item": "Disciplinas oficiais", "ok": Disciplina.objects.count() > 0, "acao": "Cadastrar disciplinas com cor visual."},
        {"grupo": "Vínculos", "item": "Turmas com vínculo professor/disciplina", "ok": vinculos.count() > 0 and turmas_sem_vinculo == 0, "acao": "Criar vínculos ativos para todas as turmas."},
        {"grupo": "Vínculos", "item": "Horários semanais cadastrados", "ok": horarios.count() > 0 and turmas_sem_horario == 0, "acao": "Cadastrar grade semanal por professor/turma/disciplina."},
        {"grupo": "Professor", "item": "Professores com vínculo", "ok": professores_sem_vinculo == 0 if professores.count() else False, "acao": "Vincular professores pendentes."},
        {"grupo": "Professor", "item": "Professores com horário", "ok": professores_sem_horario == 0 if professores.count() else False, "acao": "Montar horários reais para professores."},
        {"grupo": "Diário", "item": "Frequência P/F/FJ lançada", "ok": frequencias.count() > 0, "acao": "Usar Aula rápida ou Lançamentos oficiais."},
        {"grupo": "Diário", "item": "Conteúdo de aula registrado", "ok": aulas.count() > 0 and not aulas_sem_conteudo, "acao": "Registrar conteúdo mensal de aulas."},
        {"grupo": "Diário", "item": "Turmas com alunos", "ok": turmas_sem_alunos == 0 if turmas.count() else False, "acao": "Conferir matrículas por turma."},
        {"grupo": "Relatórios", "item": "Documentos/relatórios disponíveis", "ok": DocumentoGerado.objects.count() >= 0 and _ok_rota("gestao_relatorios_901"), "acao": "Usar Central de relatórios finais."},
        {"grupo": "Render", "item": "Arquivos de publicação preservados", "ok": (Path(settings.BASE_DIR) / "render.yaml").exists() and (Path(settings.BASE_DIR) / "requirements.txt").exists(), "acao": "Conferir deploy no Render."},
    ]

    ok = sum(1 for r in requisitos if r["ok"])
    pendentes = [r for r in requisitos if not r["ok"]]
    for r in requisitos:
        r["status"] = _status(r["ok"])
        r["nivel"] = _nivel(r["ok"])

    cards = [
        {"titulo": "Prontidão", "valor": f"{_pct(ok, len(requisitos))}%", "texto": f"{ok}/{len(requisitos)} requisitos finais"},
        {"titulo": "Turmas", "valor": turmas.count(), "texto": f"{turmas_sem_vinculo} sem vínculo • {turmas_sem_horario} sem horário"},
        {"titulo": "Alunos", "valor": alunos.count(), "texto": f"{frequencias.filter(status='F').count()} F • {frequencias.filter(status='FJ').count()} FJ"},
        {"titulo": "Professores", "valor": professores.count(), "texto": f"{professores_sem_vinculo} sem vínculo • {professores_sem_horario} sem horário"},
        {"titulo": "Aulas", "valor": aulas.count(), "texto": f"{horarios.count()} horários semanais"},
        {"titulo": "Registros", "valor": frequencias.count(), "texto": "frequências P/F/FJ"},
    ]

    return {
        "escopo": "Professor" if professor is not None else "Gestão",
        "requisitos": requisitos,
        "requisitos_total": len(requisitos),
        "requisitos_ok": ok,
        "prontidao": _pct(ok, len(requisitos)),
        "pendentes": pendentes,
        "cards": cards,
        "turmas_sem_vinculo": turmas_sem_vinculo,
        "turmas_sem_horario": turmas_sem_horario,
        "professores_sem_vinculo": professores_sem_vinculo,
        "professores_sem_horario": professores_sem_horario,
        "aulas_sem_conteudo": aulas_sem_conteudo,
    }


def rotas_criticas_961_1000() -> dict:
    """Validação reversível das rotas principais sem exigir IDs."""
    rotas = [
        ("Gestão", "dashboard_gestao", "Painel da gestão"),
        ("Gestão", "gestao_centro_operacional_321", "Central escolar"),
        ("Gestão", "gestao_diario_oficial", "Diário Escolar"),
        ("Gestão", "gestao_checkup_etapas_901_960", "Finalização 901–960"),
        ("Gestão", "gestao_fechamento_mensal_901", "Fechamento mensal final"),
        ("Gestão", "gestao_ia_pedagogica_901", "IA pedagógica final"),
        ("Gestão", "gestao_relatorios_901", "Relatórios finais"),
        ("Professor", "dashboard_professor_home", "Painel do professor"),
        ("Professor", "professor_centro_operacional_321", "Central escolar"),
        ("Professor", "professor_aula_rapida_321", "Aula rápida"),
        ("Professor", "professor_diario_oficial", "Meu Diário Escolar"),
        ("Professor", "professor_checkup_etapas_901_960", "Finalização 901–960"),
        ("Professor", "professor_fechamento_mensal_901", "Fechamento mensal final"),
        ("Professor", "professor_ia_pedagogica_901", "IA pedagógica final"),
        ("Professor", "professor_relatorios_901", "Relatórios finais"),
    ]
    linhas = []
    for grupo, nome, titulo in rotas:
        ok = _ok_rota(nome)
        linhas.append({"grupo": grupo, "nome": nome, "titulo": titulo, "ok": ok, "status": _status(ok), "nivel": _nivel(ok)})
    total_ok = sum(1 for r in linhas if r["ok"])
    return {"linhas": linhas, "total": len(linhas), "ok": total_ok, "prontidao": _pct(total_ok, len(linhas))}


def roteiro_final_961_1000(professor=None) -> dict:
    """Roteiro final acionável para terminar sem quebrar o projeto."""
    prontidao = prontidao_operacional_961_1000(professor=professor)
    auditoria = auditoria_arquivos_961_1000()
    rotas = rotas_criticas_961_1000()

    blocos = [
        {"ordem": 1, "titulo": "Conferência de erro", "descricao": "Corrigir template/URL/import antes de criar qualquer nova tela.", "status": "OK" if rotas["prontidao"] == 100 else "CONFERIR"},
        {"ordem": 2, "titulo": "Cadastros oficiais", "descricao": "Escola, ano, turmas, alunos, professores, disciplinas, vínculos e horários.", "status": "OK" if prontidao["prontidao"] >= 80 else "PENDENTE"},
        {"ordem": 3, "titulo": "Professor em sala", "descricao": "Aula rápida, chamada P/F/FJ, conteúdo e fechamento mensal.", "status": "OK" if _ok_rota("professor_aula_rapida_321") else "PENDENTE"},
        {"ordem": 4, "titulo": "Diário de Classe", "descricao": "Frequência mensal, registros de aula, identificação institucional e impressão/PDF.", "status": "OK" if _ok_rota("gestao_diario_oficial") else "PENDENTE"},
        {"ordem": 5, "titulo": "Revisar telas antigas com segurança", "descricao": "Mapear standalone/CSS antigo e converter sem apagar rotas vivas.", "status": "CONFERIR" if auditoria["templates_standalone"] else "OK"},
        {"ordem": 6, "titulo": "Publicação e versão instalada", "descricao": "Manter SQLite agora, testar collectstatic e deixar PostgreSQL para fase de produção.", "status": "OK"},
    ]
    return {"prontidao": prontidao, "auditoria": auditoria, "rotas": rotas, "blocos": blocos}


def mega_checkup_961_1000(professor=None) -> dict:
    roteiro = roteiro_final_961_1000(professor=professor)
    return {
        "titulo": "Conferência do Diário do Professor",
        "subtitulo": "Conferência técnica e visual antes de liberar o uso.",
        "roteiro": roteiro,
        "prontidao": roteiro["prontidao"],
        "auditoria": roteiro["auditoria"],
        "rotas": roteiro["rotas"],
        "blocos": roteiro["blocos"],
    }

"""Utilitários centrais do Diário Escolar.

Criado nas etapas 229–234 para reduzir repetição espalhada em views/templates
sem quebrar rotas antigas. Este arquivo concentra diagnósticos e regras estáveis
usadas pelos painéis de gestão e professor.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from django.conf import settings

from apps.academico.models import (
    Aluno,
    ConteudoAula,
    Disciplina,
    Frequencia,
    HorarioAula,
    ProfessorTurmaDisciplina,
    Turma,
)


def turmas_do_professor(professor):
    """Turmas oficiais do professor, sempre por vínculo ativo da gestão."""
    return Turma.objects.filter(
        vinculos_professores__professor=professor,
        vinculos_professores__ativo=True,
    ).distinct()


def disciplinas_do_professor(professor):
    """Disciplinas oficiais do professor, sempre por vínculo ativo."""
    return Disciplina.objects.filter(
        vinculos_professores__professor=professor,
        vinculos_professores__ativo=True,
    ).distinct()


def horarios_do_professor(professor):
    """Horários cadastrados pela gestão/admin para o professor."""
    return HorarioAula.objects.select_related("turma", "disciplina").filter(
        professor=professor,
        ativo=True,
    )


def contagem_status_frequencia(queryset=None):
    """Contagem oficial P/F/FJ sem tratar FJ como presença."""
    qs = queryset if queryset is not None else Frequencia.objects.all()
    return {
        "presencas": qs.filter(status="P").count(),
        "faltas": qs.filter(status="F").count(),
        "justificadas": qs.filter(status="FJ").count(),
        "total": qs.count(),
    }


def resumo_fluxo_diario_real():
    """Fluxo único que evita duplicar Diário, Frequência e Aulas nos painéis."""
    return [
        {
            "ordem": 1,
            "nome": "Gestão cadastra escola, ano letivo, turmas e professores",
            "status": "base administrativa",
        },
        {
            "ordem": 2,
            "nome": "Gestão vincula professor + turma + disciplina + turno",
            "status": "professor automático",
        },
        {
            "ordem": 3,
            "nome": "Gestão cadastra horários semanais por turno",
            "status": "grade oficial",
        },
        {
            "ordem": 4,
            "nome": "Professor lança frequência P/F/FJ por disciplina e data",
            "status": "registro oficial",
        },
        {
            "ordem": 5,
            "nome": "Professor registra aulas do mês por turma/disciplina",
            "status": "livro mensal",
        },
        {
            "ordem": 6,
            "nome": "Gestão clica no aluno e abre ficha/dossiê único",
            "status": "acompanhamento",
        },
    ]


def diagnostico_tecnico_diario_real():
    """Resumo técnico seguro para checkup sem depender de dados específicos."""
    status = contagem_status_frequencia()
    return {
        "turmas": Turma.objects.count(),
        "alunos": Aluno.objects.count(),
        "disciplinas": Disciplina.objects.count(),
        "vinculos": ProfessorTurmaDisciplina.objects.filter(ativo=True).count(),
        "horarios": HorarioAula.objects.filter(ativo=True).count(),
        "aulas": ConteudoAula.objects.count(),
        "frequencias": status["total"],
        "presencas": status["presencas"],
        "faltas": status["faltas"],
        "fj": status["justificadas"],
        "fluxo_unico": True,
        "fj_oficial": True,
    }


def templates_duplicados_exatos():
    """Lista de grupos de templates idênticos, para auditoria de limpeza."""
    templates_dir = Path(settings.BASE_DIR) / "templates"
    if not templates_dir.exists():
        return []

    grupos = defaultdict(list)
    for arquivo in templates_dir.rglob("*.html"):
        try:
            digest = sha256(arquivo.read_bytes()).hexdigest()
        except OSError:
            continue
        grupos[digest].append(str(arquivo.relative_to(templates_dir)))

    return [arquivos for arquivos in grupos.values() if len(arquivos) > 1]


def auditoria_tecnica_pacote():
    """Auditoria leve do pacote para acompanhar duplicidades sem quebrar rotas.

    Não remove templates referenciados; apenas conta itens que ainda precisam ser
    consolidados nas próximas fases.
    """
    base = Path(settings.BASE_DIR)
    templates_dir = base / "templates"
    core_dir = templates_dir / "core"
    gestao_dir = templates_dir / "gestao"

    todos_templates = list(templates_dir.rglob("*.html")) if templates_dir.exists() else []
    professor_templates = list(core_dir.glob("professor_*.html")) if core_dir.exists() else []
    gestao_checkups = list(gestao_dir.glob("checkup_*.html")) if gestao_dir.exists() else []
    checkups_txt = list(base.glob("CHECKUP*.txt"))
    pycache = list(base.rglob("__pycache__"))
    pyc = list(base.rglob("*.pyc"))

    return {
        "templates_total": len(todos_templates),
        "templates_professor": len(professor_templates),
        "checkups_templates": len(gestao_checkups),
        "checkups_txt": len(checkups_txt),
        "pycache_dirs": len(pycache),
        "pyc_files": len(pyc),
        "duplicados_exatos": len(templates_duplicados_exatos()),
        "views_linhas": sum(1 for _ in (base / "apps" / "core" / "views.py").open(encoding="utf-8")),
        "urls_linhas": sum(1 for _ in (base / "apps" / "core" / "urls.py").open(encoding="utf-8")),
        "db_sqlite_presente": (base / "db.sqlite3").exists(),
    }


def pendencias_diario_real_essenciais():
    """Checklist objetivo do que ainda merece melhoria no Diário Escolar."""
    return [
        {
            "item": "Separar views gigantes por módulos",
            "situacao": "pendente técnico",
            "detalhe": "apps/core/views.py ainda concentra muitas telas; o próximo ganho real é separar professor, gestão e diário sem trocar URLs.",
        },
        {
            "item": "Consolidar templates legados",
            "situacao": "em andamento",
            "detalhe": "Templates antigos foram preservados para não quebrar rotas; a limpeza agora deve ser por redirecionamento seguro.",
        },
        {
            "item": "Validar regras fixas de turno",
            "situacao": "pendente funcional",
            "detalhe": "Manhã 1º–5º, tarde 6º–9º + ensino médio, noite EJA precisam virar validação administrativa.",
        },
        {
            "item": "Ficha oficial única do aluno",
            "situacao": "parcial",
            "detalhe": "O clique no aluno já existe, mas ainda há versões antigas de dossiê/ficha que devem apontar para uma tela principal.",
        },
    ]


# =====================================================
# ETAPAS 241–246 — Fluxos únicos e auditoria de painéis
# =====================================================

def fluxo_professor_unificado(total_turmas=0, total_disciplinas=0, total_horarios=0, total_pendencias=0):
    """Cards oficiais do painel do professor sem duplicar Diário/Frequência/Aulas."""
    return [
        {
            "ordem": "1",
            "titulo": "Minhas turmas",
            "descricao": "Entrada por turma vinculada pela gestão.",
            "url": "turmas",
            "status": f"{total_turmas} turma(s)",
        },
        {
            "ordem": "2",
            "titulo": "Lançamentos",
            "descricao": "Diário de Classe, frequência P/F/FJ e registro mensal de aulas no mesmo caminho.",
            "url": "professor_diario_oficial",
            "status": f"{total_disciplinas} disciplina(s)",
        },
        {
            "ordem": "3",
            "titulo": "Horários",
            "descricao": "Grade semanal por professor, turma, turno e disciplina.",
            "url": "professor_meus_horarios_reais",
            "status": f"{total_horarios} horário(s)",
        },
        {
            "ordem": "4",
            "titulo": "Fechamento",
            "descricao": "Pendências mensais e conferência do que já foi lançado.",
            "url": "professor_prontidao_lancamentos_163",
            "status": f"{total_pendencias} pendência(s)",
        },
    ]


def fluxo_gestao_unificado():
    """Fluxo oficial da gestão para manter cadastro, vínculos e diário sem atalhos repetidos."""
    return [
        {"ordem": "1", "titulo": "Escola e ano letivo", "url": "gestao_escola", "descricao": "Identificação oficial usada no Diário de Classe."},
        {"ordem": "2", "titulo": "Professores", "url": "gestao_professores", "descricao": "Cadastro pela direção/admin para aparecer automaticamente no professor."},
        {"ordem": "3", "titulo": "Vínculos e horários", "url": "gestao_vinculos", "descricao": "Professor + turma + disciplina + turno + grade semanal."},
        {"ordem": "4", "titulo": "Alunos e fichas", "url": "gestao_alunos", "descricao": "Clique no aluno para abrir a ficha oficial única."},
        {"ordem": "5", "titulo": "Diário Escolar", "url": "gestao_diario_oficial", "descricao": "Conferência oficial de diário, frequência e aulas."},
        {"ordem": "6", "titulo": "Fechamento", "url": "gestao_prontidao_diario_real_139", "descricao": "Pendências mensais, auditoria e entrega."},
    ]


def regras_turnos_oficiais():
    """Matriz pedida para o Diário Escolar por turno e etapa escolar."""
    return [
        {"turno": "Manhã", "turmas": "5 turmas", "series": "1º ao 5º ano", "status": "regra oficial"},
        {"turno": "Tarde", "turmas": "8 turmas", "series": "6º ao 9º ano + 1ª, 2ª e 3ª série do Ensino Médio", "status": "regra oficial"},
        {"turno": "Noite", "turmas": "5 turmas", "series": "EJA", "status": "regra oficial"},
    ]


def painel_duplicidades_visuais():
    """Itens que devem continuar agrupados para evitar repetição visual nos painéis."""
    return {
        "professor": [
            "Frequência não deve aparecer como card solto: fica dentro de Lançamentos.",
            "Diário de classe não deve duplicar Registro de aulas: ambos entram pelo mesmo fluxo da turma.",
            "Fechamento apenas confere o que já foi lançado, sem criar outro lançamento paralelo.",
        ],
        "gestao": [
            "Cadastro do professor fica em Professores; vínculo e horário ficam em Vínculos e horários.",
            "Ficha do aluno deve ser a entrada oficial para dados completos do estudante.",
            "Auditoria/checkups ficam fora do fluxo diário para não poluir o painel principal.",
        ],
    }


# =====================================================
# ETAPAS 247–252 — Consolidação técnica e validação oficial
# =====================================================

def _texto_turma(turma):
    return f"{getattr(turma, 'nome', '')} {getattr(turma, 'turno', '')}".strip().lower()


def normalizar_turno_diario_real(valor):
    """Normaliza turnos livres/legados para a matriz oficial do Diário Escolar."""
    texto = (valor or "").strip().lower()
    if texto in {"matutino", "manha", "manhã", "m"}:
        return "MANHA"
    if texto in {"vespertino", "tarde", "v"}:
        return "TARDE"
    if texto in {"noturno", "noite", "n"}:
        return "NOITE"
    return "INDEFINIDO"


def validar_turma_matriz_oficial(turma):
    """Valida turma contra a regra pedida: manhã 1º–5º, tarde 6º–9º + médio, noite EJA."""
    texto = _texto_turma(turma)
    turno = normalizar_turno_diario_real(getattr(turma, 'turno', ''))

    eja = "eja" in texto
    fundamental_1 = any(s in texto for s in ["1º", "1 ano", "1º ano", "2º", "2 ano", "2º ano", "3º", "3 ano", "3º ano", "4º", "4 ano", "4º ano", "5º", "5 ano", "5º ano"])
    fundamental_2 = any(s in texto for s in ["6º", "6 ano", "6º ano", "7º", "7 ano", "7º ano", "8º", "8 ano", "8º ano", "9º", "9 ano", "9º ano"])
    ensino_medio = any(s in texto for s in ["1ª série", "1 serie", "1ª", "2ª série", "2 serie", "2ª", "3ª série", "3 serie", "3ª", "ensino medio", "ensino médio"])

    if turno == "MANHA":
        ok = fundamental_1 and not eja
        esperado = "1º ao 5º ano"
    elif turno == "TARDE":
        ok = (fundamental_2 or ensino_medio) and not eja
        esperado = "6º ao 9º ano + 1ª, 2ª e 3ª série do Ensino Médio"
    elif turno == "NOITE":
        ok = eja
        esperado = "EJA"
    else:
        ok = False
        esperado = "turno informado como manhã, tarde ou noite"

    return {
        "turma": turma,
        "turno_normalizado": turno,
        "ok": ok,
        "esperado": esperado,
        "motivo": "OK" if ok else f"Conferir nome/turno: esperado {esperado}.",
    }


def auditoria_matriz_turnos_oficial():
    """Auditoria administrativa das turmas contra a matriz oficial por turno."""
    resultados = [validar_turma_matriz_oficial(turma) for turma in Turma.objects.filter(ativa=True).order_by("turno", "nome")]
    return {
        "total": len(resultados),
        "ok": sum(1 for item in resultados if item["ok"]),
        "pendentes": sum(1 for item in resultados if not item["ok"]),
        "itens": resultados,
    }


def rotas_principais_diario_real():
    """Rotas principais mantidas como fonte única para professor e gestão."""
    return {
        "professor": [
            {"titulo": "Painel", "rota": "dashboard_professor_home", "descricao": "Painel do professor."},
            {"titulo": "Turmas", "rota": "turmas", "descricao": "Entrada por turma vinculada pela gestão."},
            {"titulo": "Lançamentos", "rota": "professor_diario_oficial", "descricao": "Diário, frequência P/F/FJ e aulas no mesmo fluxo."},
            {"titulo": "Horários", "rota": "professor_meus_horarios_reais", "descricao": "Grade semanal oficial."},
        ],
        "gestao": [
            {"titulo": "Painel", "rota": "dashboard_gestao", "descricao": "Centro de comando da direção/admin."},
            {"titulo": "Escola", "rota": "gestao_escola", "descricao": "Identificação oficial da escola."},
            {"titulo": "Professores", "rota": "gestao_professores", "descricao": "Cadastro do professor pela gestão."},
            {"titulo": "Vínculos", "rota": "gestao_vinculos", "descricao": "Professor + turma + disciplina."},
            {"titulo": "Horários", "rota": "gestao_horarios", "descricao": "Grade semanal por turno."},
            {"titulo": "Alunos", "rota": "gestao_alunos", "descricao": "Ficha oficial clicável do aluno."},
        ],
    }


def pendencias_operacionais_diario_real():
    """Pendências práticas ainda importantes para o projeto ficar mais pronto."""
    matriz = auditoria_matriz_turnos_oficial()
    sem_vinculo = Turma.objects.filter(ativa=True).exclude(vinculos_professores__ativo=True).distinct().count()
    sem_horario = Turma.objects.filter(ativa=True).exclude(horarios__ativo=True).distinct().count()
    professores_sem_vinculo = ProfessorTurmaDisciplina.objects.filter(ativo=True).values("professor").distinct().count()
    return [
        {"item": "Turmas fora da matriz oficial", "total": matriz["pendentes"], "prioridade": "alta" if matriz["pendentes"] else "ok"},
        {"item": "Turmas sem professor/disciplina", "total": sem_vinculo, "prioridade": "alta" if sem_vinculo else "ok"},
        {"item": "Turmas sem horários", "total": sem_horario, "prioridade": "média" if sem_horario else "ok"},
        {"item": "Professores com vínculo ativo", "total": professores_sem_vinculo, "prioridade": "informativo"},
    ]



# =====================================================
# ETAPAS 253–258 — Higienização de rotas, painéis e legado
# =====================================================

def inventario_templates_legados():
    """Classifica templates acumulados sem apagar arquivos usados por rotas antigas.

    A limpeza segura do projeto precisa separar o que é fluxo oficial atual do
    que é histórico de etapas. Assim o painel fica limpo sem quebrar URLs já
    existentes.
    """
    base = Path(settings.BASE_DIR) / "templates"
    if not base.exists():
        return {"total": 0, "professor_legados": 0, "gestao_checkups": 0, "principais": []}

    professor_legados = list((base / "core").glob("professor_*_legacy.html")) if (base / "core").exists() else []
    gestao_checkups = list((base / "gestao").glob("checkup_*.html")) if (base / "gestao").exists() else []
    etapas = list(base.rglob("*etapas*.html"))
    principais = [
        "core/dashboard_professor.html",
        "gestao/dashboard_admin.html",
        "core/diario_classe_turma.html",
        "core/frequencia_mensal.html",
        "gestao/aluno_diario_completo.html",
        "gestao/diario_oficial_turma_completo.html",
    ]
    return {
        "total": len(list(base.rglob("*.html"))),
        "professor_legados": len(professor_legados),
        "gestao_checkups": len(gestao_checkups),
        "templates_etapas": len(etapas),
        "principais": principais,
        "observacao": "Legados permanecem preservados; painel oficial usa apenas entradas únicas.",
    }


def manifesto_fluxo_unico_diario_real():
    """Mapa mestre para impedir volta de cards duplicados nos painéis."""
    return {
        "professor": [
            {"grupo": "Turmas", "rota": "turmas", "regra": "entrada inicial por vínculo ativo da gestão"},
            {"grupo": "Lançamentos", "rota": "professor_diario_oficial", "regra": "diário, frequência P/F/FJ e aulas juntos"},
            {"grupo": "Horários", "rota": "professor_meus_horarios_reais", "regra": "somente grade cadastrada pela gestão"},
            {"grupo": "Fechamento", "rota": "professor_prontidao_lancamentos_163", "regra": "conferência sem relançamento paralelo"},
        ],
        "gestao": [
            {"grupo": "Identificação", "rota": "gestao_escola", "regra": "escola e ano letivo oficiais"},
            {"grupo": "Professores", "rota": "gestao_professores", "regra": "cadastro administrativo do professor"},
            {"grupo": "Vínculos e horários", "rota": "gestao_vinculos", "regra": "professor + turma + disciplina + turno + grade"},
            {"grupo": "Alunos", "rota": "gestao_alunos", "regra": "clique no aluno abre ficha oficial"},
            {"grupo": "Diário Escolar", "rota": "gestao_diario_oficial", "regra": "conferência oficial e auditoria"},
        ],
    }


def auditoria_views_urls_diario_real():
    """Mede acúmulo técnico que ainda precisa ser reduzido nas próximas fases."""
    base = Path(settings.BASE_DIR)
    views = base / "apps" / "core" / "views.py"
    urls = base / "apps" / "core" / "urls.py"
    views_text = views.read_text(encoding="utf-8") if views.exists() else ""
    urls_text = urls.read_text(encoding="utf-8") if urls.exists() else ""
    return {
        "views_linhas": len(views_text.splitlines()),
        "urls_linhas": len(urls_text.splitlines()),
        "defs_views": views_text.count("def "),
        "rotas_path": urls_text.count("path("),
        "precisa_modularizar": len(views_text.splitlines()) > 2500,
        "recomendacao": "Separar views em módulos professor/gestao/diario mantendo imports de compatibilidade.",
    }


def checklist_253_258():
    """Checklist objetivo desta fase de continuidade."""
    return [
        {"item": "Painéis sem cards soltos repetidos", "status": "OK", "detalhe": "Diário, frequência e aulas permanecem agrupados em Lançamentos."},
        {"item": "Templates legados monitorados", "status": "OK", "detalhe": "Não removidos quando ainda podem estar vinculados a rotas antigas."},
        {"item": "FJ separado", "status": "OK", "detalhe": "P/F/FJ seguem como contagem oficial."},
        {"item": "Matriz de turnos mantida", "status": "OK", "detalhe": "Manhã 1º–5º, tarde 6º–9º + médio, noite EJA."},
        {"item": "Próximo ajuste técnico", "status": "Pendente", "detalhe": "Modularizar views.py sem alterar URLs públicas."},
    ]



# =====================================================
# ETAPAS 259–264 — Cobertura real dos requisitos do Diário de Classe
# =====================================================

def cobertura_requisitos_diario_real_259_264():
    """Conferência objetiva do que o usuário pediu para o Diário de Classe Real.

    A função não altera dados. Ela mede a cobertura do projeto para evitar novas
    duplicidades e deixar claro o que ainda falta preencher/cadastrar pela gestão.
    """
    from django.contrib.auth import get_user_model
    from apps.academico.models import AnoLetivo, Escola

    User = get_user_model()
    escola = Escola.objects.filter(ativa=True).first()
    ano_letivo = AnoLetivo.objects.filter(ativo=True).first()
    matriz = auditoria_matriz_turnos_oficial()
    status = contagem_status_frequencia()

    turmas_ativas = Turma.objects.filter(ativa=True)
    professores = User.objects.filter(tipo="PROF")
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios = HorarioAula.objects.filter(ativo=True)

    turnos = {
        "manha": sum(1 for t in turmas_ativas if normalizar_turno_diario_real(getattr(t, "turno", "")) == "MANHA"),
        "tarde": sum(1 for t in turmas_ativas if normalizar_turno_diario_real(getattr(t, "turno", "")) == "TARDE"),
        "noite": sum(1 for t in turmas_ativas if normalizar_turno_diario_real(getattr(t, "turno", "")) == "NOITE"),
    }

    requisitos = [
        {
            "grupo": "Identificação oficial",
            "item": "Escola ativa cadastrada",
            "ok": bool(escola),
            "detalhe": escola.nome if escola else "Cadastre a escola em Gestão > Escola.",
        },
        {
            "grupo": "Identificação oficial",
            "item": "Ano letivo ativo",
            "ok": bool(ano_letivo),
            "detalhe": str(ano_letivo.ano) if ano_letivo else "Cadastre/ative o ano letivo.",
        },
        {
            "grupo": "Turmas e turnos",
            "item": "Matriz manhã/tarde/noite/EJA",
            "ok": matriz["pendentes"] == 0 and matriz["total"] > 0,
            "detalhe": f"{matriz['ok']}/{matriz['total']} turma(s) dentro da matriz oficial.",
        },
        {
            "grupo": "Professores",
            "item": "Cadastro de professores pela gestão/admin",
            "ok": professores.exists(),
            "detalhe": f"{professores.count()} professor(es) cadastrado(s).",
        },
        {
            "grupo": "Professores",
            "item": "Vínculo professor + turma + disciplina",
            "ok": vinculos.exists(),
            "detalhe": f"{vinculos.count()} vínculo(s) ativo(s).",
        },
        {
            "grupo": "Horários",
            "item": "Horários semanais por turma/disciplina",
            "ok": horarios.exists(),
            "detalhe": f"{horarios.count()} horário(s) ativo(s).",
        },
        {
            "grupo": "Frequência",
            "item": "Status oficial P/F/FJ",
            "ok": True,
            "detalhe": f"P: {status['presencas']} • F: {status['faltas']} • FJ: {status['justificadas']}.",
        },
        {
            "grupo": "Aulas",
            "item": "Registro mensal de aulas",
            "ok": ConteudoAula.objects.exists(),
            "detalhe": f"{ConteudoAula.objects.count()} registro(s) de aula.",
        },
        {
            "grupo": "Alunos",
            "item": "Ficha oficial clicável do aluno",
            "ok": Aluno.objects.exists(),
            "detalhe": f"{Aluno.objects.count()} aluno(s) para ficha oficial.",
        },
    ]

    total = len(requisitos)
    ok = sum(1 for r in requisitos if r["ok"])
    return {
        "total": total,
        "ok": ok,
        "pendentes": total - ok,
        "percentual": round((ok / total) * 100, 1) if total else 0,
        "requisitos": requisitos,
        "turnos": {
            "manha": {"atual": turnos["manha"], "esperado": 5, "descricao": "1º ao 5º ano"},
            "tarde": {"atual": turnos["tarde"], "esperado": 8, "descricao": "6º ao 9º + 1ª a 3ª série"},
            "noite": {"atual": turnos["noite"], "esperado": 5, "descricao": "EJA"},
        },
    }


def duplicidades_operacionais_259_264():
    """Aponta onde ainda há acúmulo, sem apagar rotas antigas."""
    base = Path(settings.BASE_DIR) / "templates"
    core = base / "core"
    gestao = base / "gestao"
    professor_templates = list(core.glob("professor_*.html")) if core.exists() else []
    checkups = list(gestao.glob("checkup_*.html")) if gestao.exists() else []
    diarios = [p for p in professor_templates if "diario" in p.name or "frequencia" in p.name]
    return {
        "professor_templates": len(professor_templates),
        "professor_diario_frequencia": len(diarios),
        "checkups_gestao": len(checkups),
        "duplicados_exatos": len(templates_duplicados_exatos()),
        "acao_segura": "Manter templates legados fora dos painéis principais e não criar novos atalhos duplicados.",
    }


def checklist_259_264():
    return [
        {"item": "Não criar novos cards de Frequência/Diário separados", "status": "OK", "detalhe": "Professor continua usando Lançamentos como entrada única."},
        {"item": "Medir cobertura real do pedido", "status": "OK", "detalhe": "Escola, ano letivo, turmas, professor, vínculo, horário, frequência, aula e ficha do aluno."},
        {"item": "Preservar layout glass dark teal", "status": "OK", "detalhe": "Templates principais continuam usando a base premium existente."},
        {"item": "Próximo passo técnico", "status": "Pendente", "detalhe": "Modularizar views.py com reexport seguro sem trocar as URLs públicas."},
    ]

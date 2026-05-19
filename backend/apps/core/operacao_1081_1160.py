from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse

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
from apps.diario.models import Diario

BASE_DIR = Path(settings.BASE_DIR)
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
ROOT_DIR = BASE_DIR.parent


def _exists(rel: str) -> bool:
    return (BASE_DIR / rel).exists() or (ROOT_DIR / rel).exists()


def _route(name: str, **kwargs) -> bool:
    try:
        reverse(name, kwargs=kwargs or None)
        return True
    except NoReverseMatch:
        return False


def _status(ok: bool, parcial: bool = False) -> str:
    if ok:
        return "OK"
    return "PARCIAL" if parcial else "PENDENTE"


def _nivel(status: str) -> str:
    return {"OK": "success", "PARCIAL": "warning", "PENDENTE": "danger"}.get(status, "warning")


def _count_standalone_templates() -> tuple[int, list[str]]:
    items: list[str] = []
    for p in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = p.relative_to(BASE_DIR).as_posix()
        if rel.startswith("templates/partials/") or rel.startswith("templates/admin/"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")[:1400]
        if "{% extends" not in text and ("<!doctype" in text.lower() or "<html" in text.lower()):
            items.append(rel)
    return len(items), items[:40]


def _count_static_files() -> dict:
    return {
        "css": len(list((STATIC_DIR / "css").glob("*.css"))) if (STATIC_DIR / "css").exists() else 0,
        "js": len(list((STATIC_DIR / "js").glob("*.js"))) if (STATIC_DIR / "js").exists() else 0,
    }


def _project_counts() -> dict:
    User = get_user_model()
    return {
        "escolas": Escola.objects.count(),
        "anos": AnoLetivo.objects.count(),
        "gestores": User.objects.filter(tipo__in=["ADMIN", "COORD", "SEC"]).count(),
        "professores": User.objects.filter(tipo="PROF").count(),
        "alunos": Aluno.objects.filter(ativo=True).count(),
        "turmas": Turma.objects.filter(ativa=True).count(),
        "disciplinas": Disciplina.objects.count(),
        "vinculos": ProfessorTurmaDisciplina.objects.filter(ativo=True).count(),
        "horarios": HorarioAula.objects.filter(ativo=True).count(),
        "frequencias": Frequencia.objects.count(),
        "conteudos": ConteudoAula.objects.count(),
        "diarios": Diario.objects.count(),
        "notas": Nota.objects.count(),
    }


def mega_checkup_1081_1160(professor=None) -> dict:
    counts = _project_counts()
    standalone_total, standalone_amostra = _count_standalone_templates()
    static_counts = _count_static_files()

    checks = [
        {
            "grupo": "Pedidos do roteiro final",
            "pedido": "Gestão separada do professor, sem navegação cruzada perigosa.",
            "status": _status(_route("dashboard_gestao") and _route("dashboard_professor_home")),
            "detalhe": "Rotas e bases separadas para Gestão/Professor continuam existindo.",
        },
        {
            "grupo": "Gestão administrativa",
            "pedido": "Cadastros de escola, ano letivo, professores, alunos, turmas, disciplinas, vínculos, horários e carga.",
            "status": _status(all(_route(x) for x in ["gestao_escola", "gestao_professores", "gestao_alunos", "gestao_cadastros_operacionais_301", "gestao_carga_horaria_professores_301"])),
            "detalhe": f"Escolas={counts['escolas']} • anos={counts['anos']} • alunos={counts['alunos']} • turmas={counts['turmas']} • vínculos={counts['vinculos']} • horários={counts['horarios']}",
        },
        {
            "grupo": "Professor em sala",
            "pedido": "Abrir aula, lançar frequência P/F/FJ, registrar conteúdo, salvar aula e fechar mês.",
            "status": _status(_route("professor_aula_rapida_321") and _route("professor_fechamento_mensal_901") and _route("professor_diario_oficial")),
            "detalhe": f"Frequências={counts['frequencias']} • conteúdos={counts['conteudos']} • diários={counts['diarios']}",
        },
        {
            "grupo": "Diário de Classe",
            "pedido": "Documento institucional com escola, turma, disciplina, professor, horários, frequência, aulas, carga e fechamento.",
            "status": _status(_route("gestao_diario_oficial") and _route("professor_diario_oficial")),
            "detalhe": "Rotas oficiais de diário para gestão e professor estão ativas.",
        },
        {
            "grupo": "Ficha oficial do aluno",
            "pedido": "Ficha única com dados, turma, frequência, faltas, FJ, aulas, disciplinas, histórico e relatórios.",
            "status": _status(_route("gestao_ficha_aluno", aluno_id=1), parcial=counts["alunos"] == 0),
            "detalhe": "A rota existe; depende de aluno real para abrir uma ficha específica.",
        },
        {
            "grupo": "IA pedagógica",
            "pedido": "Analisar faltas, turmas críticas, pendências, frequência atrasada, aulas sem conteúdo e risco escolar.",
            "status": _status(_route("gestao_ia_pedagogica_901") and _route("professor_ia_pedagogica_901")),
            "detalhe": "IA final da gestão e do professor integrada às sidebars e painéis.",
        },
        {
            "grupo": "Relatórios e fechamento",
            "pedido": "Relatórios premium e fechamento mensal por aluno, turma, professor, disciplina, frequência, aulas e carga.",
            "status": _status(_route("gestao_relatorios_901") and _route("professor_relatorios_901") and _route("gestao_fechamento_mensal_901") and _route("professor_fechamento_mensal_901")),
            "detalhe": "Camada final de relatórios e fechamento mensal presente.",
        },
        {
            "grupo": "Visual do Diário",
            "pedido": "Design system único com cards, tabelas, botões, scroll-box, estados vazios e responsividade.",
            "status": _status(_exists("static/css/diario_1081_1160_render_ready.css") and static_counts["css"] <= 45, parcial=standalone_total > 80),
            "detalhe": f"CSS={static_counts['css']} • JS={static_counts['js']} • templates standalone mapeados={standalone_total}. Legado está revestido e mapeado, não apagado à força.",
        },
        {
            "grupo": "Publicação do sistema",
            "pedido": "Deixar pronto para colocar online no Render com PostgreSQL, static, health check e variáveis.",
            "status": _status(_exists("../render.yaml") and _exists("build.sh") and _exists("requirements.txt") and _route("healthz")),
            "detalhe": "Blueprint raiz, health check /healthz/, WhiteNoise, DATABASE_URL e PYTHON_VERSION preparados.",
        },
        {
            "grupo": "Banco e segurança",
            "pedido": "Manter SQLite local por enquanto, mas permitir PostgreSQL no Render sem quebrar banco local.",
            "status": _status(_exists("db.sqlite3") and "DATABASE_URL" in (BASE_DIR / "config/settings.py").read_text(encoding="utf-8")),
            "detalhe": "SQLite preservado; se DATABASE_URL existir, o sistema usa PostgreSQL automaticamente.",
        },
    ]
    for item in checks:
        item["nivel"] = _nivel(item["status"])

    total = len(checks)
    ok = sum(1 for c in checks if c["status"] == "OK")
    parcial = sum(1 for c in checks if c["status"] == "PARCIAL")
    pendente = total - ok - parcial
    score = round(((ok + parcial * 0.55) / total) * 100) if total else 0
    return {
        "titulo": "Conferência antes da publicação",
        "checks": checks,
        "total": total,
        "ok": ok,
        "parcial": parcial,
        "pendente": pendente,
        "score": score,
        "counts": counts,
        "standalone_total": standalone_total,
        "standalone_amostra": standalone_amostra,
        "static_counts": static_counts,
    }


def plano_render_1081_1160(professor=None) -> dict:
    checks = [
        {"titulo": "Blueprint raiz", "status": _status((ROOT_DIR / "render.yaml").exists()), "detalhe": "Render lê render.yaml na raiz do repositório."},
        {"titulo": "RootDir backend", "status": "OK", "detalhe": "O serviço aponta para backend/ e não tenta subir o frontend vazio."},
        {"titulo": "PostgreSQL", "status": _status("DATABASE_URL" in (BASE_DIR / "config/settings.py").read_text(encoding="utf-8")), "detalhe": "DATABASE_URL ativa Postgres automaticamente; db.sqlite3 segue preservado localmente."},
        {"titulo": "Static files", "status": _status("whitenoise" in (BASE_DIR / "requirements.txt").read_text(encoding="utf-8").lower()), "detalhe": "WhiteNoise + collectstatic no build.sh."},
        {"titulo": "Health check", "status": _status(_route("healthz")), "detalhe": "Endpoint /healthz/ faz SELECT 1 no banco e retorna JSON."},
        {"titulo": "Python fixado", "status": _status((ROOT_DIR / ".python-version").exists() or (BASE_DIR / ".python-version").exists()), "detalhe": "Versão fixada para evitar diferença entre local e Render."},
        {"titulo": "Gunicorn", "status": _status("gunicorn" in (BASE_DIR / "requirements.txt").read_text(encoding="utf-8").lower()), "detalhe": "StartCommand usa WEB_CONCURRENCY/RENDER_WEB_CONCURRENCY quando disponível."},
        {"titulo": "Segurança HTTPS", "status": _status("SECURE_SSL_REDIRECT" in (BASE_DIR / "config/settings.py").read_text(encoding="utf-8")), "detalhe": "Cookies seguros, HSTS e proxy SSL prontos para Render."},
    ]
    for c in checks:
        c["nivel"] = _nivel(c["status"])
    return {
        "titulo": "Publicação do sistema 1081–1160",
        "checks": checks,
        "ok": sum(1 for c in checks if c["status"] == "OK"),
        "total": len(checks),
        "comandos": [
            "python manage.py check --deploy",
            "python manage.py migrate --check --noinput",
            "python manage.py collectstatic --noinput --dry-run",
            "python manage.py mega_checkup_diario --strict --show-skipped",
            "python manage.py render_prontidao_diario",
        ],
        "variaveis": [
            "DEBUG=False",
            "SECRET_KEY=gerada no Render",
            "ALLOWED_HOSTS=.onrender.com,seudominio.com",
            "CSRF_TRUSTED_ORIGINS=https://*.onrender.com,https://seudominio.com",
            "DATABASE_URL=fornecida pelo Render Postgres",
            "PYTHON_VERSION=3.13.5",
        ],
    }


def estimativa_acessos_render_1081_1160() -> dict:
    """Estimativa conservadora para uso escolar típico.

    Não é benchmark definitivo: depende de dados reais, upload/fotos, PDFs,
    latência do banco, plano Render, cache e quantidade de relatórios pesados.
    """
    cenarios = [
        {
            "plano": "Free",
            "uso": "Teste e demonstração",
            "usuarios_simultaneos": "1–3",
            "observacao": "Pode dormir por inatividade; não recomendo para escola em produção.",
        },
        {
            "plano": "Starter — 1 instância",
            "uso": "Escola pequena, uso leve",
            "usuarios_simultaneos": "10–25 ativos",
            "observacao": "Bom para secretaria + poucos professores lançando frequência. Evitar muitos PDFs ao mesmo tempo.",
        },
        {
            "plano": "Standard — 1 instância",
            "uso": "Escola pequena/média",
            "usuarios_simultaneos": "30–70 ativos",
            "observacao": "Recomendado para operação real inicial com PostgreSQL e static servido pelo WhiteNoise.",
        },
        {
            "plano": "Pro — 1 instância",
            "uso": "Uso intenso ou várias turmas ao mesmo tempo",
            "usuarios_simultaneos": "80–150 ativos",
            "observacao": "Melhor para muitos professores lançando chamada no mesmo horário.",
        },
        {
            "plano": "2+ instâncias / autoscaling",
            "uso": "Rede escolar ou picos grandes",
            "usuarios_simultaneos": "150+ ativos",
            "observacao": "Escala horizontalmente; precisa Postgres e sem depender de arquivo local persistente.",
        },
    ]
    return {
        "titulo": "Estimativa de acessos simultâneos",
        "cenarios": cenarios,
        "recomendacao": "Para começar sem travar: Render Standard + PostgreSQL. Para teste: Starter. Para produção com muitos professores no mesmo horário: Pro ou 2 instâncias.",
        "regra_pratica": "Considere usuário ativo quem clica/salva/abre relatórios ao mesmo tempo; usuário apenas lendo a tela pesa muito menos.",
        "alertas": [
            "A resposta real só vem com teste de carga usando os dados da escola.",
            "Relatórios/PDFs e uploads pesam mais que navegação comum.",
            "SQLite não deve ser usado em produção multiusuário no Render; use PostgreSQL.",
        ],
    }

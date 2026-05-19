# Etapas 1281-1340 — Diário de Classe Oficial Real Completo.
# Gestão é a única fonte oficial dos dados; importador/Excel antigo foi removido.

from .views_shared import *  # noqa: F401,F403
from apps.core.operacao_1281_1340 import cobertura_diario_classe_1281, auditoria_sem_excel_1281


@login_required
def gestao_diario_classe_oficial_1281(request):
    """Compatibilidade: a gestão usa uma única central chamada Diário oficial.

    A rota antiga do Diário de Classe continua existindo para não quebrar links,
    mas redireciona para a central oficial consolidada da gestão.
    """
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    return redirect("gestao_diario_oficial")


@login_required
def professor_diario_classe_oficial_1281(request):
    if not usuario_professor(request.user):
        if usuario_gestor(request.user):
            return redirect("gestao_diario_classe_oficial_1281")
        return render(request, "core/acesso_negado.html")
    mes = request.GET.get("mes")
    ano = request.GET.get("ano")
    cobertura = cobertura_diario_classe_1281(professor=request.user, mes=mes, ano=ano)
    return render(request, "core/professor_diario_classe_oficial_1281.html", {
        "cobertura": cobertura,
        "auditoria_excel": auditoria_sem_excel_1281(),
        "professor": request.user,
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_etapas_1281_1340(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    cobertura = cobertura_diario_classe_1281()
    auditoria_excel = auditoria_sem_excel_1281()
    cards = [
        {"titulo": "Fonte de dados", "valor": "Gestão", "ok": auditoria_excel["ok"], "texto": "Sem Excel/importador antigo."},
        {"titulo": "Turnos oficiais", "valor": f"{sum(1 for t in cobertura['turnos'] if t['ok'])}/3", "ok": all(t["ok"] for t in cobertura["turnos"]), "texto": "Manhã, tarde e noite/EJA."},
        {"titulo": "Diário mensal", "valor": cobertura["totais"]["diarios"], "ok": cobertura["totais"]["diarios"] > 0, "texto": "Registros de aulas oficiais."},
        {"titulo": "Fechamentos", "valor": cobertura["totais"]["fechamentos"], "ok": cobertura["totais"]["fechamentos"] > 0, "texto": "Fechamento mensal persistente."},
    ]
    return render(request, "gestao/checkup_etapas_1281_1340.html", {
        "cobertura": cobertura,
        "auditoria_excel": auditoria_excel,
        "cards": cards,
        "hoje": date.today(),
    })

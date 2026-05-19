from django import template
from django.utils import timezone

register = template.Library()

PERFIS_GESTAO = {"ADMIN", "COORD", "SEC"}


@register.simple_tag(takes_context=True)
def licenca_gestao_status(context):
    """Retorna dados simples para exibir aviso de validade da gestão.

    Mantém o template seguro: se a função de licença ainda não estiver instalada,
    apenas não mostra o aviso.
    """
    request = context.get("request")
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {"mostrar": False}

    if getattr(user, "tipo", "") not in PERFIS_GESTAO:
        return {"mostrar": False}

    try:
        from apps.core.licenca_gestao import garantir_periodo_teste
        garantir_periodo_teste(user)
    except Exception:
        pass

    expira = getattr(user, "gestao_acesso_expira_em", None)
    if not expira:
        return {"mostrar": False}

    agora = timezone.now()
    if timezone.is_naive(expira):
        expira = timezone.make_aware(expira, timezone.get_current_timezone())

    segundos = (expira - agora).total_seconds()
    dias = 0 if segundos <= 0 else int((segundos + 86399) // 86400)
    expirado = segundos <= 0 or bool(getattr(user, "gestao_acesso_bloqueado", False))

    if expirado:
        status = "expirado"
        titulo = "Acesso da gestão expirado"
        texto = "Informe o serial/key de ativação para liberar novamente o painel da gestão."
    elif dias <= 3:
        status = "critico"
        titulo = f"Acesso da gestão vence em {dias} dia(s)"
        texto = "Renove com antecedência para evitar bloqueio do painel da gestão."
    elif dias <= 7:
        status = "atencao"
        titulo = f"Acesso da gestão vence em {dias} dia(s)"
        texto = "O período de teste/licença está perto do fim."
    else:
        status = "ok"
        titulo = f"Acesso da gestão ativo por mais {dias} dia(s)"
        texto = "Sistema liberado para uso da gestão escolar."

    return {
        "mostrar": True,
        "status": status,
        "titulo": titulo,
        "texto": texto,
        "dias": dias,
        "expira": expira,
        "expirado": expirado,
    }

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone

from apps.core.licenca_gestao import acesso_gestao_expirado, garantir_periodo_teste


class SessaoGestaoExpiraMiddleware:
    """Expira automaticamente a sessão da gestão.

    Professores podem manter o fluxo normal. Gestão, coordenação e secretaria
    são perfis sensíveis porque criam contas, vinculam professores e alteram
    dados oficiais. Para esses perfis, o login expira por inatividade e também
    tem um limite máximo de duração.
    """

    PERFIS_GESTAO = {"ADMIN", "COORD", "SEC"}
    SESSION_INICIO = "gestao_session_inicio_ts"
    SESSION_ULTIMO = "gestao_session_ultimo_ts"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user is not None and getattr(user, "is_authenticated", False):
            tipo = getattr(user, "tipo", "")

            if tipo in self.PERFIS_GESTAO:
                # Primeiro garante o período de teste/validade comercial da gestão.
                # Se o teste/licença venceu, o gestor só acessa a tela de ativação.
                garantir_periodo_teste(user)
                caminhos_liberados = (
                    "/ativar-acesso-gestao/",
                    "/accounts/logout/",
                    "/logout/",
                    "/static/",
                    "/media/",
                    "/healthz/",
                    f"/{getattr(settings, 'CRIADOR_ADMIN_URL', 'admin-criador/')}",
                )
                if acesso_gestao_expirado(user) and not any(path.startswith(item) for item in caminhos_liberados):
                    messages.warning(
                        request,
                        "O período de teste/acesso da gestão expirou. Informe o serial/key para liberar novamente.",
                    )
                    return redirect("ativar_acesso_gestao")

                agora = int(timezone.now().timestamp())
                inicio = request.session.get(self.SESSION_INICIO) or agora
                ultimo = request.session.get(self.SESSION_ULTIMO) or agora

                idle_seconds = getattr(settings, "GESTAO_SESSION_IDLE_SECONDS", 30 * 60)
                absolute_seconds = getattr(settings, "GESTAO_SESSION_ABSOLUTE_SECONDS", 8 * 60 * 60)

                expirou_por_inatividade = agora - int(ultimo) > idle_seconds
                expirou_por_tempo_total = agora - int(inicio) > absolute_seconds

                if expirou_por_inatividade or expirou_por_tempo_total:
                    logout(request)
                    messages.warning(
                        request,
                        "Sua sessão da gestão expirou por segurança. Entre novamente para continuar.",
                    )
                    return redirect(settings.LOGIN_URL)

                request.session[self.SESSION_INICIO] = int(inicio)
                request.session[self.SESSION_ULTIMO] = agora
                request.session.set_expiry(idle_seconds)
                request.session.modified = True
            else:
                # Não deixa dados antigos de sessão da gestão presos em login de professor.
                request.session.pop(self.SESSION_INICIO, None)
                request.session.pop(self.SESSION_ULTIMO, None)

        return self.get_response(request)


class PerfilAreaSeguraMiddleware:
    """Mantém gestão e professor em áreas separadas.

    Evita que botões, histórico do navegador ou links antigos levem o usuário
    para o painel do outro perfil. A regra é leve e não mexe na lógica das views:
    gestor permanece em /gestao/ e professor permanece em /professor/.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        path = request.path or ""

        if user is not None and getattr(user, "is_authenticated", False):
            tipo = getattr(user, "tipo", "")
            if path.startswith("/professor/") and tipo in {"ADMIN", "COORD", "SEC"}:
                return redirect("dashboard_gestao")
            if path.startswith("/gestao/") and tipo == "PROF":
                return redirect("dashboard_professor")

        return self.get_response(request)

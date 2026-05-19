from django.shortcuts import redirect


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

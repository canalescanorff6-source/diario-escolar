"""Contexto institucional compartilhado pelas telas públicas."""


def _clean(value):
    return str(value).strip() if value is not None else ""


def escola_institucional(request):
    dados = {
        "escola_login": None,
        "escola_login_nome_info": "Sua instituição de ensino",
        "escola_login_texto": "Um ambiente organizado para a rotina acadêmica.",
        "escola_login_municipio": "",
        "escola_login_estado_sigla": "",
        "escola_login_logo": "",
    }
    try:
        from apps.academico.models import Escola

        escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()
        if not escola:
            return dados
        dados["escola_login"] = escola
        dados["escola_login_nome_info"] = _clean(escola.nome) or dados["escola_login_nome_info"]
        dados["escola_login_texto"] = _clean(escola.texto_institucional) or dados["escola_login_texto"]
        dados["escola_login_municipio"] = _clean(escola.municipio)
        dados["escola_login_estado_sigla"] = _clean(escola.estado)
        if escola.brasao_logo:
            try:
                dados["escola_login_logo"] = escola.brasao_logo.url
            except (ValueError, AttributeError):
                pass
    except Exception:
        # A tela de login deve continuar disponível mesmo antes das migrations
        # ou durante indisponibilidade momentânea do banco.
        pass
    return dados

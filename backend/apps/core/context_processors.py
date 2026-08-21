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
        "escola_login_estado": "ESTADO DO MARANHÃO",
        "escola_login_secretaria": "SECRETARIA DE ESTADO DA EDUCAÇÃO",
        "escola_login_aldeia": "",
        "escola_login_terra": "",
        "gestor_login_nome": "",
        "gestor_login_cargo": "Direção escolar",
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
        dados["escola_login_estado"] = _clean(escola.estado_nome) or dados["escola_login_estado"]
        dados["escola_login_secretaria"] = _clean(escola.secretaria) or dados["escola_login_secretaria"]
        dados["escola_login_aldeia"] = _clean(escola.aldeia)
        dados["escola_login_terra"] = _clean(escola.terra_indigena)
        dados["gestor_login_nome"] = _clean(escola.gestor_nome)
        dados["gestor_login_cargo"] = _clean(escola.gestor_cargo) or dados["gestor_login_cargo"]

        if escola.brasao_logo:
            try:
                dados["escola_login_logo"] = escola.brasao_logo.url
            except (ValueError, AttributeError):
                pass
    except Exception:
        # A tela de login deve continuar disponível durante migrations ou em
        # indisponibilidade temporária do banco; os fallbacks acima continuam.
        pass
    return dados

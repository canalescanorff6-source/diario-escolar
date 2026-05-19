"""Contextos globais seguros para telas premium."""

from django.contrib.auth import get_user_model


_PLACEHOLDER_NAMES = {
    "escola modelo diario ia premium",
    "escola modelo diário ia premium",
    "escola modelo",
    "diario ia premium",
    "diário ia premium",
}


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _is_placeholder_school_name(value):
    normalized = _clean(value).lower()
    return (not normalized) or normalized in _PLACEHOLDER_NAMES or "escola modelo" in normalized


def escola_institucional(request):
    """Fornece dados institucionais da escola ativa para a tela de login.

    A tela de login não deve exibir dados técnicos, usuários de teste ou placeholders
    como placeholders antigos. Se a gestão ainda não configurou a escola, mostramos
    textos institucionais neutros e seguros.
    """
    dados = {
        "escola_login": None,
        "escola_login_estado": "ESTADO DO MARANHÃO",
        "escola_login_secretaria": "SECRETARIA DE ESTADO DA EDUCAÇÃO",
        "escola_login_nome_titulo": "Instituição escolar",
        "escola_login_nome_info": "Aguardando configuração no painel da gestão",
        "escola_login_aldeia": "Aguardando configuração no painel da gestão",
        "escola_login_terra": "Aguardando configuração no painel da gestão",
        "escola_login_texto": "Ambiente oficial de acesso da instituição escolar.",
        "gestor_login_nome": "Direção escolar",
        "gestor_login_cargo": "Responsável institucional pela escola",
    }
    try:
        from apps.academico.models import Escola

        escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()
        dados["escola_login"] = escola

        if escola:
            nome = _clean(getattr(escola, "nome", ""))
            nome_valido = not _is_placeholder_school_name(nome)
            dados["escola_login_nome_titulo"] = nome if nome_valido else "Instituição escolar"
            dados["escola_login_nome_info"] = nome if nome_valido else "Aguardando configuração no painel da gestão"
            dados["escola_login_estado"] = _clean(getattr(escola, "estado_nome", "")) or dados["escola_login_estado"]
            dados["escola_login_secretaria"] = _clean(getattr(escola, "secretaria", "")) or dados["escola_login_secretaria"]
            dados["escola_login_aldeia"] = _clean(getattr(escola, "aldeia", "")) or "Aguardando configuração no painel da gestão"
            dados["escola_login_terra"] = _clean(getattr(escola, "terra_indigena", "")) or "Aguardando configuração no painel da gestão"
            dados["escola_login_texto"] = _clean(getattr(escola, "texto_institucional", "")) or dados["escola_login_texto"]

            gestor_nome = _clean(getattr(escola, "gestor_nome", ""))
            gestor_cargo = _clean(getattr(escola, "gestor_cargo", ""))
            if gestor_nome and gestor_nome.lower() not in {"gestão teste", "gestao teste", "gestão escolar"}:
                dados["gestor_login_nome"] = gestor_nome
            else:
                Usuario = get_user_model()
                gestor = (
                    Usuario.objects.filter(tipo__in=["ADMIN", "COORD", "SEC"], is_active=True)
                    .exclude(username__icontains="teste")
                    .order_by("first_name", "username")
                    .first()
                )
                if gestor:
                    dados["gestor_login_nome"] = gestor.get_full_name() or gestor.username
            if gestor_cargo:
                dados["gestor_login_cargo"] = gestor_cargo
    except Exception:
        pass
    return dados

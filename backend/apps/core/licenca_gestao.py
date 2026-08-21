import secrets
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone


# Não alterar: este salt legado mantém válidas as licenças já emitidas.
SERIAL_SALT = "diario-ia-escolar-licenca-gestao-v1"
PERFIS_GESTAO = {"ADMIN", "COORD", "SEC"}


def dias_teste_gestao():
    return max(int(getattr(settings, "GESTAO_TRIAL_DIAS", 7)), 1)


def _usuario_identidade(user):
    email = (getattr(user, "email", "") or "").strip().lower()
    username = (getattr(user, "username", "") or "").strip().lower()
    return email, username


def usuario_eh_gestao(user):
    return getattr(user, "is_authenticated", False) and getattr(user, "tipo", "") in PERFIS_GESTAO


def garantir_periodo_teste(user):
    """Cria a data de teste inicial quando a conta de gestão ainda não tem validade.

    O padrão é GESTAO_TRIAL_DIAS, configurável no Render. A data é salva no
    usuário para o teste não reiniciar a cada login.
    """
    if not usuario_eh_gestao(user):
        return user

    if getattr(user, "gestao_acesso_expira_em", None):
        return user

    agora = timezone.now()
    inicio = getattr(user, "date_joined", None) or agora
    if timezone.is_naive(inicio):
        inicio = timezone.make_aware(inicio, timezone.get_current_timezone())

    user.gestao_teste_inicio = getattr(user, "gestao_teste_inicio", None) or inicio
    user.gestao_acesso_expira_em = inicio + timedelta(days=dias_teste_gestao())
    user.gestao_acesso_bloqueado = False
    user.save(update_fields=["gestao_teste_inicio", "gestao_acesso_expira_em", "gestao_acesso_bloqueado"])
    return user


def acesso_gestao_expirado(user):
    if not usuario_eh_gestao(user):
        return False

    garantir_periodo_teste(user)
    if getattr(user, "gestao_acesso_bloqueado", False):
        return True

    expira = getattr(user, "gestao_acesso_expira_em", None)
    if not expira:
        return False
    return timezone.now() > expira


def dias_restantes_gestao(user):
    if not usuario_eh_gestao(user):
        return None
    garantir_periodo_teste(user)
    expira = getattr(user, "gestao_acesso_expira_em", None)
    if not expira:
        return None
    segundos = (expira - timezone.now()).total_seconds()
    if segundos <= 0:
        return 0
    return int((segundos + 86399) // 86400)


def gerar_serial_gestao(email_ou_usuario="", dias=30, observacao=""):
    dias = max(int(dias or 30), 1)
    identidade = (email_ou_usuario or "").strip().lower()
    payload = {
        "tipo": "LICENCA_GESTAO",
        "versao": 1,
        "identidade": identidade,
        "dias": dias,
        "observacao": (observacao or "").strip()[:120],
        "gerado_em": timezone.now().isoformat(),
        "nonce": secrets.token_urlsafe(10),
    }
    return signing.dumps(payload, salt=SERIAL_SALT, compress=True)


def validar_serial_gestao(serial, user):
    serial = (serial or "").strip()
    if not serial:
        return False, "Informe o serial/key de ativação."

    try:
        payload = signing.loads(serial, salt=SERIAL_SALT)
    except signing.BadSignature:
        return False, "Serial/key inválido. Confira se você copiou o código completo."

    if payload.get("tipo") != "LICENCA_GESTAO":
        return False, "Serial/key inválido para acesso da gestão."

    try:
        dias = int(payload.get("dias") or 0)
    except (TypeError, ValueError):
        dias = 0
    if dias <= 0:
        return False, "Serial/key sem quantidade de dias válida."

    identidade = (payload.get("identidade") or "").strip().lower()
    email, username = _usuario_identidade(user)
    if identidade and identidade not in {email, username}:
        return False, "Este serial/key foi gerado para outra conta da gestão."

    user.gestao_teste_inicio = getattr(user, "gestao_teste_inicio", None) or timezone.now()
    user.gestao_acesso_expira_em = timezone.now() + timedelta(days=dias)
    user.gestao_acesso_bloqueado = False
    user.gestao_serial_ultimo = serial[-120:]
    user.save(update_fields=[
        "gestao_teste_inicio",
        "gestao_acesso_expira_em",
        "gestao_acesso_bloqueado",
        "gestao_serial_ultimo",
    ])
    return True, f"Acesso da gestão liberado por {dias} dia(s)."

"""Configurações do Diário Escolar Pro.

Produção é segura por padrão: segredos, banco e domínios são fornecidos por
variáveis de ambiente. O SQLite permanece disponível apenas para desenvolvimento.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return int(default)


def env_csv(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def env_set(name: str, default: str = "") -> set[str]:
    return {item.lower() for item in env_csv(name, default)}


ON_RENDER = env_bool("RENDER")
ON_RUNSITE = any(env_bool(name) for name in ("RUNSITE", "RUNSITE_APP", "RUNSITE_DEPLOY"))
PRODUCTION_SERVER = ON_RENDER or ON_RUNSITE or env_bool("PRODUCTION")
DEBUG = env_bool("DEBUG", False)
RUNNING_DEV_SERVER = any(arg == "runserver" or arg.startswith("runserver") for arg in sys.argv)
LOCAL_DEV_SERVER = RUNNING_DEV_SERVER and not env_bool("FORCE_PRODUCTION_SECURITY")

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if PRODUCTION_SERVER:
        raise RuntimeError("SECRET_KEY é obrigatória em produção.")
    SECRET_KEY = secrets.token_urlsafe(48)

ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,.onrender.com,.runsite.app")
CSRF_TRUSTED_ORIGINS = env_csv(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.onrender.com,https://*.runsite.app",
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.usuarios",
    "apps.core",
    "apps.academico",
    "apps.diario",  # Mantido para compatibilidade com dados históricos; sem rota pública legada.
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SessaoGestaoExpiraMiddleware",
    "apps.core.middleware.PerfilAreaSeguraMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.escola_institucional",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
REQUIRE_DATABASE_URL = env_bool("DJANGO_REQUIRE_DATABASE_URL", PRODUCTION_SERVER)
if DATABASE_URL:
    try:
        import dj_database_url

        DATABASES["default"] = dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=PRODUCTION_SERVER,
        )
    except Exception as exc:
        if REQUIRE_DATABASE_URL:
            raise RuntimeError("DATABASE_URL inválida ou indisponível.") from exc
elif REQUIRE_DATABASE_URL:
    raise RuntimeError("DATABASE_URL é obrigatória em produção. Use PostgreSQL persistente.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.environ.get("TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "usuarios.Usuario"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Sessões administrativas.
GESTAO_SESSION_IDLE_MINUTES = env_int("GESTAO_SESSION_IDLE_MINUTES", 30)
GESTAO_SESSION_ABSOLUTE_MINUTES = env_int("GESTAO_SESSION_ABSOLUTE_MINUTES", 480)
GESTAO_SESSION_IDLE_SECONDS = max(GESTAO_SESSION_IDLE_MINUTES, 1) * 60
GESTAO_SESSION_ABSOLUTE_SECONDS = max(GESTAO_SESSION_ABSOLUTE_MINUTES, 1) * 60
GESTAO_TRIAL_DIAS = env_int("GESTAO_TRIAL_DIAS", 7)
GESTAO_LICENCA_CONTATO_WHATSAPP = os.environ.get("GESTAO_LICENCA_CONTATO_WHATSAPP", "").strip()

# Django Admin reservado a superusuários. Identificadores adicionais são opcionais.
CRIADOR_ADMIN_URL = os.environ.get("CRIADOR_ADMIN_URL", "admin-criador/").strip().strip("/") + "/"
CRIADOR_ADMIN_EMAILS = env_set("CRIADOR_ADMIN_EMAILS")
CRIADOR_ADMIN_USERNAMES = env_set("CRIADOR_ADMIN_USERNAMES")
CRIADOR_ADMIN_IDENTIFICADORES = CRIADOR_ADMIN_EMAILS | CRIADOR_ADMIN_USERNAMES

STATICFILES_STORAGE = os.environ.get("DJANGO_STATICFILES_STORAGE") or (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if LOCAL_DEV_SERVER
    else "whitenoise.storage.CompressedStaticFilesStorage"
    if ON_RUNSITE
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": STATICFILES_STORAGE},
}
WHITENOISE_USE_FINDERS = env_bool("WHITENOISE_USE_FINDERS", ON_RUNSITE)
RUNSITE_STATIC_URL_FALLBACK = env_bool("RUNSITE_STATIC_URL_FALLBACK", ON_RUNSITE)

# Segurança HTTP.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = False if LOCAL_DEV_SERVER else env_bool("SESSION_COOKIE_SECURE", PRODUCTION_SERVER)
CSRF_COOKIE_SECURE = False if LOCAL_DEV_SERVER else env_bool("CSRF_COOKIE_SECURE", PRODUCTION_SERVER)
SECURE_SSL_REDIRECT = False if LOCAL_DEV_SERVER else env_bool("SECURE_SSL_REDIRECT", PRODUCTION_SERVER and not DEBUG)
SECURE_HSTS_SECONDS = 0 if LOCAL_DEV_SERVER else env_int("SECURE_HSTS_SECONDS", 31536000 if PRODUCTION_SERVER and not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not LOCAL_DEV_SERVER and env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", PRODUCTION_SERVER and not DEBUG)
SECURE_HSTS_PRELOAD = not LOCAL_DEV_SERVER and env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int("DATA_UPLOAD_MAX_MEMORY_SIZE", 5 * 1024 * 1024)
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int("FILE_UPLOAD_MAX_MEMORY_SIZE", 5 * 1024 * 1024)

# Código de autorização da gestão. Nunca deixe um e-mail pessoal fixo no GitHub.
GESTAO_AUTORIZACAO_EMAIL = os.environ.get("GESTAO_AUTORIZACAO_EMAIL", os.environ.get("EMAIL_GESTAO_AUTORIZADA", "")).strip()
GESTAO_CODIGO_MAX_TENTATIVAS = env_int("GESTAO_CODIGO_MAX_TENTATIVAS", 5)
GESTAO_CODIGO_COOLDOWN_SEGUNDOS = env_int("GESTAO_CODIGO_COOLDOWN_SEGUNDOS", 60)
MOBILE_LOGIN_MAX_ATTEMPTS = env_int("MOBILE_LOGIN_MAX_ATTEMPTS", 10)
MOBILE_LOGIN_WINDOW_SECONDS = env_int("MOBILE_LOGIN_WINDOW_SECONDS", 300)

# E-mail: Brevo por HTTPS é recomendado nas hospedagens que bloqueiam SMTP.
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = os.environ.get("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", os.environ.get("EMAIL_HOST_USER", ""))
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Diário Escolar Pro")
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND") or (
    "apps.core.email_backends.BrevoEmailBackend"
    if BREVO_API_KEY and BREVO_SENDER_EMAIL
    else "django.core.mail.backends.smtp.EmailBackend"
    if os.environ.get("EMAIL_HOST")
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 20)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    f"Diário Escolar Pro <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "Diário Escolar Pro <no-reply@localhost>",
)
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": True},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

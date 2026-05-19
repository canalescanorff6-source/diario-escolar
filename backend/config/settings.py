import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ON_RENDER = os.environ.get('RENDER', '').lower() == 'true'
ON_RUNSITE = any(
    os.environ.get(name, '').lower() in ('1', 'true', 'yes', 'on')
    for name in ('RUNSITE', 'RUNSITE_APP', 'RUNSITE_DEPLOY')
)

SECRET_KEY = os.environ.get('SECRET_KEY', 'diario-ia-premium-local-dev-secret-key-1221-1280-render-safe-fallback-9f8a7b6c5d4e3')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes', 'on')
PRODUCTION_SERVER = (
    ON_RENDER
    or ON_RUNSITE
    or os.environ.get('PRODUCTION', '').lower() in ('1', 'true', 'yes', 'on')
    or (not DEBUG and bool(os.environ.get('DATABASE_URL')))
)
RUNNING_DEV_SERVER = any(arg == 'runserver' or arg.startswith('runserver') for arg in sys.argv)
# No servidor local do Django, segurança HTTPS de produção fica desligada mesmo que o terminal ainda tenha RENDER=true/RUNSITE=true.
LOCAL_DEV_SERVER = RUNNING_DEV_SERVER and os.environ.get('FORCE_RENDER_SECURITY', '').lower() not in ('1', 'true', 'yes', 'on')

DEFAULT_ALLOWED_HOSTS = (
    'diario-escolar.runsite.app,.runsite.app,'
    'diario-escolar.onrender.com,.onrender.com,'
    'localhost,127.0.0.1,testserver'
)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.usuarios',
    'apps.core',
    'apps.academico',
    'apps.ia',
    'apps.diario',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.SessaoGestaoExpiraMiddleware',
    'apps.core.middleware.PerfilAreaSeguraMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.escola_institucional',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL = os.environ.get('DATABASE_URL')
REQUIRE_DATABASE_URL = os.environ.get('DJANGO_REQUIRE_DATABASE_URL', 'true' if PRODUCTION_SERVER else 'false').lower() in ('1', 'true', 'yes', 'on')
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    except Exception as exc:
        if REQUIRE_DATABASE_URL:
            raise RuntimeError('DATABASE_URL foi informado, mas não pôde ser lido. Confira a URL do banco PostgreSQL.') from exc
        # Mantém SQLite local caso a biblioteca ou variável esteja indisponível no desenvolvimento.
        pass
elif REQUIRE_DATABASE_URL:
    raise RuntimeError(
        'Na hospedagem online, configure DATABASE_URL com um banco PostgreSQL externo/persistente. '
        'Não use SQLite em produção porque o sistema de arquivos da hospedagem é temporário.'
    )

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'usuarios.Usuario'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Segurança da sessão da gestão. Gestores criam contas e mexem nos dados oficiais,
# por isso a sessão da gestão expira automaticamente após inatividade.
def _int_env(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return int(default)

GESTAO_SESSION_IDLE_MINUTES = _int_env('GESTAO_SESSION_IDLE_MINUTES', 30)
GESTAO_SESSION_ABSOLUTE_MINUTES = _int_env('GESTAO_SESSION_ABSOLUTE_MINUTES', 480)
GESTAO_SESSION_IDLE_SECONDS = max(GESTAO_SESSION_IDLE_MINUTES, 1) * 60
GESTAO_SESSION_ABSOLUTE_SECONDS = max(GESTAO_SESSION_ABSOLUTE_MINUTES, 1) * 60

# Validade comercial do acesso da gestão.
# Padrão: 7 dias de teste. Depois disso a gestão consegue fazer login,
# mas fica presa na tela de ativação até aplicar um serial/key válido.
GESTAO_TRIAL_DIAS = _int_env('GESTAO_TRIAL_DIAS', 7)
GESTAO_LICENCA_CONTATO_WHATSAPP = os.environ.get('GESTAO_LICENCA_CONTATO_WHATSAPP', '98996127032').strip()

# Acesso ao Django Admin reservado ao criador do sistema.
# /admin/ deixa de existir; use a URL configurada em CRIADOR_ADMIN_URL.
# No Render, configure CRIADOR_ADMIN_EMAILS com o e-mail do seu superusuário criador.
def _csv_env(name, default=''):
    return {item.strip().lower() for item in os.environ.get(name, default).split(',') if item.strip()}

CRIADOR_ADMIN_URL = os.environ.get('CRIADOR_ADMIN_URL', 'admin-criador/').strip().strip('/') + '/'
CRIADOR_ADMIN_EMAILS = _csv_env('CRIADOR_ADMIN_EMAILS', 'canalescanorff28@gmail.com')
CRIADOR_ADMIN_USERNAMES = _csv_env('CRIADOR_ADMIN_USERNAMES', '')
CRIADOR_ADMIN_IDENTIFICADORES = CRIADOR_ADMIN_EMAILS | CRIADOR_ADMIN_USERNAMES

STATIC_ROOT = BASE_DIR / 'staticfiles'
# Na RunSite, use storage sem manifesto para evitar erro 500 caso o collectstatic
# ainda não tenha gerado staticfiles.json no primeiro boot.
STATICFILES_STORAGE = os.environ.get('DJANGO_STATICFILES_STORAGE') or (
    'django.contrib.staticfiles.storage.StaticFilesStorage' if LOCAL_DEV_SERVER
    else 'whitenoise.storage.CompressedStaticFilesStorage' if ON_RUNSITE
    else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': STATICFILES_STORAGE},
}

DEFAULT_CSRF_TRUSTED_ORIGINS = (
    'https://diario-escolar.runsite.app,https://*.runsite.app,'
    'https://diario-escolar.onrender.com,https://*.onrender.com'
)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', DEFAULT_CSRF_TRUSTED_ORIGINS).split(',')
    if origin.strip()
]

# Segurança progressiva: local continua simples, Render/produção já sobe com HTTPS e cookies seguros.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = False if LOCAL_DEV_SERVER else os.environ.get('SESSION_COOKIE_SECURE', str(PRODUCTION_SERVER)).lower() in ('1', 'true', 'yes', 'on')
CSRF_COOKIE_SECURE = False if LOCAL_DEV_SERVER else os.environ.get('CSRF_COOKIE_SECURE', str(PRODUCTION_SERVER)).lower() in ('1', 'true', 'yes', 'on')
SECURE_SSL_REDIRECT = False if LOCAL_DEV_SERVER else os.environ.get('SECURE_SSL_REDIRECT', str(PRODUCTION_SERVER and not DEBUG)).lower() in ('1', 'true', 'yes', 'on')
SECURE_HSTS_SECONDS = 0 if LOCAL_DEV_SERVER else int(os.environ.get('SECURE_HSTS_SECONDS', '31536000' if PRODUCTION_SERVER and not DEBUG else '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False if LOCAL_DEV_SERVER else os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', str(PRODUCTION_SERVER and not DEBUG)).lower() in ('1', 'true', 'yes', 'on')
SECURE_HSTS_PRELOAD = False if LOCAL_DEV_SERVER else os.environ.get('SECURE_HSTS_PRELOAD', str(PRODUCTION_SERVER and not DEBUG)).lower() in ('1', 'true', 'yes', 'on')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

# E-mail para envio do código numérico de 6 dígitos da gestão.
# Em produção, configure na hospedagem: GESTAO_AUTORIZACAO_EMAIL e variáveis de e-mail.
GESTAO_AUTORIZACAO_EMAIL = os.environ.get(
    "GESTAO_AUTORIZACAO_EMAIL",
    os.environ.get("EMAIL_GESTAO_AUTORIZADA", "thiago01268230@gmail.com"),
).strip()
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND") or (
    "django.core.mail.backends.smtp.EmailBackend" if os.environ.get("EMAIL_HOST") else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
try:
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
except (TypeError, ValueError):
    EMAIL_PORT = 587
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() in ("1", "true", "yes", "on")
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() in ("1", "true", "yes", "on")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "20"))
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    f"Diário IA Escolar <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "Diário IA Escolar <no-reply@diarioia.local>",
)
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# Envio gratuito recomendado em hospedagens free: API HTTPS da Brevo.
# Algumas hospedagens bloqueiam SMTP nas portas 25/465/587; para e-mail real,
# prefira EMAIL_BACKEND=apps.core.email_backends.BrevoEmailBackend.
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = os.environ.get("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", EMAIL_HOST_USER or "")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Diário IA Escolar")

# Deploy do Diário IA Escolar na RunSite

Domínio preparado neste pacote:

```text
https://diario-escolar.runsite.app
```

Use o mesmo repositório do GitHub. Não apague o Render até testar tudo na RunSite.

## Configuração principal na RunSite

```text
Service type: Web Service
Root Directory: backend
Build Command: bash build.sh
Start Command: bash runsite_start.sh
```

Se a RunSite pedir porta, use a variável `$PORT`. Se ela exigir número fixo, use `10000`.

## Variáveis de ambiente

Copie as variáveis do arquivo:

```text
backend/.env.runsite.example
```

As linhas importantes já estão prontas para seu domínio:

```text
ALLOWED_HOSTS=diario-escolar.runsite.app,.runsite.app,diario-escolar.onrender.com,.onrender.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://diario-escolar.runsite.app,https://*.runsite.app,https://diario-escolar.onrender.com,https://*.onrender.com
```

## Banco

No começo, use a mesma `DATABASE_URL` do Neon. Assim a RunSite usa o mesmo banco que o Render.

## E-mail

Continue usando a Brevo:

```text
EMAIL_BACKEND=apps.core.email_backends.BrevoEmailBackend
BREVO_API_KEY=sua chave
BREVO_SENDER_EMAIL=thiago01268230@gmail.com
```

## Testes após deploy

Teste:

```text
https://diario-escolar.runsite.app/
https://diario-escolar.runsite.app/accounts/login/
https://diario-escolar.runsite.app/solicitar-codigo-gestao/
https://diario-escolar.runsite.app/criar-conta-gestao/
https://diario-escolar.runsite.app/gestao/
https://diario-escolar.runsite.app/professor/
```

Se der erro CSRF, confira `CSRF_TRUSTED_ORIGINS`.
Se der erro de domínio inválido, confira `ALLOWED_HOSTS`.

# Deploy gratuito: Render + Neon + Brevo

Este é o caminho recomendado para colocar o Diário IA Escolar online sem pagar agora:

```text
Site Django: Render Free
Banco PostgreSQL: Neon Free
E-mail do código de 6 dígitos: Brevo Free via API HTTPS
```

## 1. Criar o banco no Neon

1. Acesse o Neon e crie uma conta gratuita.
2. Crie um projeto novo, por exemplo: `diario-escolar`.
3. Crie/abra o banco padrão.
4. Copie a conexão PostgreSQL no formato `DATABASE_URL`.
5. Use a URL com SSL, normalmente parecida com:

```text
postgresql://usuario:senha@host.neon.tech/banco?sslmode=require
```

Guarde essa URL. Ela vai no Render como `DATABASE_URL`.

## 2. Criar a Brevo para envio do código por e-mail

1. Crie uma conta gratuita na Brevo.
2. Confirme/verifique o e-mail que será usado como remetente.
3. Gere uma chave de API em SMTP & API / API Keys.
4. Guarde a chave.

No Render, o projeto usa a API HTTPS da Brevo, não SMTP, porque o plano gratuito do Render bloqueia SMTP nas portas 25, 465 e 587.

## 3. Subir o projeto para GitHub

1. Extraia este projeto.
2. Abra a pasta no PyCharm.
3. Confirme que o `.gitignore` está protegendo estes arquivos:

```text
.env
db.sqlite3
media/
staticfiles/
__pycache__/
```

4. Envie o projeto para um repositório GitHub.

## 4. Criar o Web Service no Render

1. Entre no Render.
2. Clique em `New +`.
3. Escolha `Web Service`.
4. Conecte ao repositório GitHub do projeto.
5. Se o Render detectar o `render.yaml`, use o Blueprint/arquivo automaticamente.
6. Confirme que o serviço está em `Free`.

Configuração esperada:

```text
Root Directory: backend
Build Command: bash build.sh
Start Command: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-2} --timeout 120 --access-logfile - --error-logfile -
Health Check Path: /healthz/
```

## 5. Variáveis obrigatórias no Render

Coloque estas variáveis em `Environment Variables`:

```text
DEBUG=False
DJANGO_REQUIRE_DATABASE_URL=True
DATABASE_URL=cole-a-url-do-neon-aqui
GESTAO_AUTORIZACAO_EMAIL=thiago01268230@gmail.com
EMAIL_BACKEND=apps.core.email_backends.BrevoEmailBackend
BREVO_API_KEY=cole-a-chave-api-da-brevo-aqui
BREVO_SENDER_EMAIL=email-remetente-verificado-na-brevo
BREVO_SENDER_NAME=Diário IA Escolar
DEFAULT_FROM_EMAIL=Diário IA Escolar <email-remetente-verificado-na-brevo>
EMAIL_TIMEOUT=20
ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
WEB_CONCURRENCY=1
GUNICORN_THREADS=2
```

O Render pode gerar `SECRET_KEY` automaticamente pelo `render.yaml`. Se você estiver criando manualmente, crie também:

```text
SECRET_KEY=uma-chave-grande-e-secreta
```

## 6. Primeiro deploy

Depois de salvar as variáveis, faça o deploy.

O projeto está preparado para rodar:

```text
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Se o Render pedir comando manual, use:

```bash
python manage.py migrate --noinput
```

## 7. Testar o e-mail depois do deploy

No Render, abra o Shell/Console se disponível ou rode o comando pelo ambiente de deploy:

```bash
python manage.py testar_email_gestao
```

O destino padrão é:

```text
thiago01268230@gmail.com
```

Também teste no navegador:

```text
https://seu-projeto.onrender.com/solicitar-codigo-gestao/
```

O código enviado será numérico, aleatório, com 6 dígitos e validade de 15 minutos.

## 8. O que esperar do plano grátis

- O site pode dormir depois de um período sem acesso.
- Quando alguém abrir, pode demorar cerca de 1 minuto para acordar.
- Não use SQLite no Render, porque os arquivos locais do Render são temporários.
- Use Neon como banco persistente.
- Use Brevo API para e-mail real.
- Para 6 escolas e 180 professores cadastrados, serve para começar/piloto. Se muitos acessarem exatamente ao mesmo tempo, pode ficar lento no gratuito.

## 9. Checklist final

Antes de entregar para a escola, confira:

```text
/healthz/
/accounts/login/
/solicitar-codigo-gestao/
/criar-conta-gestao/
/gestao/
/professor/
```

E rode localmente:

```bash
python manage.py check
```

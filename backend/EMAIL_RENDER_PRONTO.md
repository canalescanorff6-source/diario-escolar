# E-mail real no Render — Diário IA Escolar

O projeto já está preparado para enviar por e-mail real um código numérico aleatório de 6 dígitos para a gestão.

## E-mail autorizado

O código numérico de 6 dígitos será enviado para:

```text
thiago01268230@gmail.com
```

A tela pública `/solicitar-codigo-gestao/` não permite trocar esse e-mail. Para alterar no futuro, somente pela variável de ambiente `GESTAO_AUTORIZACAO_EMAIL`. O código é gerado automaticamente, expira em 15 minutos e não precisa da variável `CODIGO_AUTORIZACAO_GESTAO`.

## Variáveis obrigatórias no Render

Configure em **Render > Environment > Environment Variables**:

```text
GESTAO_AUTORIZACAO_EMAIL=thiago01268230@gmail.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_HOST_USER=seu-email-remetente@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail
DEFAULT_FROM_EMAIL=Diário IA Escolar <seu-email-remetente@gmail.com>
EMAIL_TIMEOUT=20
```

## Importante sobre Gmail

O Gmail geralmente não aceita a senha normal da conta. Use uma **senha de app do Gmail**.

## Teste local no PowerShell

Na pasta `backend`, antes de rodar o servidor:

```powershell
$env:EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST="smtp.gmail.com"
$env:EMAIL_PORT="587"
$env:EMAIL_USE_TLS="true"
$env:EMAIL_USE_SSL="false"
$env:EMAIL_HOST_USER="seu-email-remetente@gmail.com"
$env:EMAIL_HOST_PASSWORD="sua-senha-de-app-do-gmail"
$env:DEFAULT_FROM_EMAIL="Diário IA Escolar <seu-email-remetente@gmail.com>"
$env:GESTAO_AUTORIZACAO_EMAIL="thiago01268230@gmail.com"

python manage.py testar_email_gestao
python manage.py runserver 127.0.0.1:8080
```

Depois acesse:

```text
http://127.0.0.1:8080/solicitar-codigo-gestao/
```

## Se o código aparecer no terminal

Isso significa que o projeto está usando `console.EmailBackend`, normalmente porque `EMAIL_HOST`/SMTP não foi configurado. Configure as variáveis acima para envio real. Mesmo no terminal, o código mostrado será numérico com 6 dígitos.

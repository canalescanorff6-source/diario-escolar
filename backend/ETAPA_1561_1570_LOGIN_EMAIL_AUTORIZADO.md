# Etapa 1561–1570 — Login institucional e código de gestão por e-mail

## Ajustes feitos

- Tela inicial/login redesenhada para ficar mais equilibrada e premium.
- Mantidas as informações institucionais da escola sem parecer painel interno.
- Mantida a logo fixa em `backend/static/img/logo_escola_login.png`.
- Adicionada a opção pública `Receber código por e-mail`.
- Mantida a criação de conta da gestão somente com código de autorização.
- Diretor(a) não precisa acessar o Render: basta solicitar o código pela tela de login, desde que o e-mail autorizado esteja configurado.

## Variáveis para produção

Configure no Render:

- O código de autorização da gestão é numérico, aleatório, tem 6 dígitos e é gerado no momento da solicitação por e-mail.
- `GESTAO_AUTORIZACAO_EMAIL`: e-mail autorizado da direção/gestão que receberá o código.
- `EMAIL_HOST`: servidor SMTP.
- `EMAIL_PORT`: porta SMTP, geralmente `587`.
- `EMAIL_USE_TLS`: `true`.
- `EMAIL_HOST_USER`: usuário do e-mail SMTP.
- `EMAIL_HOST_PASSWORD`: senha/app password SMTP.
- `DEFAULT_FROM_EMAIL`: remetente usado pelo sistema.

Se o SMTP não estiver configurado, em desenvolvimento o e-mail será exibido no console/log, não enviado de verdade.

## Rotas

- `/accounts/login/` — login institucional.
- `/solicitar-codigo-gestao/` — solicitar código por e-mail.
- `/criar-conta-gestao/` — criar conta autorizada da gestão.

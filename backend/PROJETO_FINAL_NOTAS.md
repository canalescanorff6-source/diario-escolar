# Diário IA Escolar — Ajustes finais

Pacote com remoção do botão PDF global, imagem de perfil para gestão/professor e cadastro autorizado da gestão pela tela de login.

- O PDF/Excel permanece nas telas de relatórios/exportação.
- A imagem da gestão é alterada em Gestão > Configurações.
- A imagem do professor é alterada pelo próprio professor em Professor > Configurações.
- A criação de conta da gestão exige código de autorização.
- Em produção no Render, o código da gestão é numérico, aleatório e gerado na solicitação por e-mail; não é necessário configurar CODIGO_AUTORIZACAO_GESTAO.

## E-mail da gestão no Render

Configuração documentada em `EMAIL_RENDER_PRONTO.md`. O projeto inclui o comando `python manage.py testar_email_gestao` para validar SMTP antes da entrega.

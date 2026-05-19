# ETAPA 1581–1590 — E-mail autorizado travado

## Correção aplicada

- A tela `/solicitar-codigo-gestao/` não mostra mais campo editável de e-mail.
- O e-mail autorizado aparece fixo na tela.
- O botão envia o código diretamente para `thiago01268230@gmail.com`.
- A mensagem da tela orienta que somente esse e-mail autorizado receberá o código.
- O fluxo de criação da conta da gestão continua protegido por código de autorização.

## Segurança

- O e-mail pode continuar sendo configurado no Render pela variável `GESTAO_AUTORIZACAO_EMAIL`.
- No local, o padrão é `thiago01268230@gmail.com`.
- O usuário não consegue trocar o e-mail pela interface pública.

## Validações

- `python manage.py check`
- `python manage.py visual_unico_check_diario --strict`
- `python manage.py validar_polimento_final_1341_1360 --strict`
- `python manage.py mega_checkup_diario --strict --show-skipped`
- `python manage.py render_prontidao_diario`
- `DEBUG=False RENDER=true python manage.py check --deploy`
- Teste GET/POST em `/solicitar-codigo-gestao/`

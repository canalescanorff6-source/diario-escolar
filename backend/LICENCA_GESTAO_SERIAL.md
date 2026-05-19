# Licença/serial da gestão escolar

Esta correção cria um controle de acesso comercial para a gestão.

## Validade padrão

Por padrão, a conta da gestão recebe **7 dias de teste**.

No Render, você pode trocar o prazo com a variável:

```text
GESTAO_TRIAL_DIAS=7
```

Exemplos:

```text
GESTAO_TRIAL_DIAS=15
GESTAO_TRIAL_DIAS=30
```

A expiração de sessão continua separada:

```text
GESTAO_SESSION_IDLE_MINUTES=30
GESTAO_SESSION_ABSOLUTE_MINUTES=480
```

- `GESTAO_TRIAL_DIAS`: quantos dias o acesso da gestão fica liberado.
- `GESTAO_SESSION_IDLE_MINUTES`: expira a sessão por inatividade.
- `GESTAO_SESSION_ABSOLUTE_MINUTES`: limite máximo da sessão logada.

## Como gerar um serial/key

No Render Shell ou no terminal local com as variáveis de ambiente configuradas:

```bash
python manage.py gerar_serial_gestao --gestor email-da-gestao@exemplo.com --dias 30
```

Também pode gerar para 90 dias:

```bash
python manage.py gerar_serial_gestao --gestor email-da-gestao@exemplo.com --dias 90
```

O serial/key será mostrado no terminal e enviado para o e-mail configurado em:

```text
GESTAO_AUTORIZACAO_EMAIL
```

No seu projeto, esse e-mail é o mesmo que recebe o código de criação da gestão.

## Como ativar depois que expirar

A gestão faz login e será levada para:

```text
/ativar-acesso-gestao/
```

Ela cola o serial/key e o acesso volta a ser liberado pela quantidade de dias do serial.

## Variáveis novas no Render

```text
GESTAO_TRIAL_DIAS=7
GESTAO_LICENCA_CONTATO_WHATSAPP=98996127032
```

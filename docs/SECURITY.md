# Segurança e privacidade

## Princípios adotados

- Professores só acessam turmas vinculadas a eles.
- A API valida vínculo professor/turma/disciplina e se o aluno pertence à turma.
- Tokens móveis são opacos, expiram e são armazenados no servidor somente por hash.
- O login mobile possui janela de limitação de tentativas configurável por ambiente.
- Fotos de alunos e professores armazenadas localmente são entregues por rota protegida; somente o brasão/logo institucional pode ser público.
- Senhas passam pelos validadores do Django.
- `SECRET_KEY` é obrigatória em produção.
- Cookies de sessão são HTTP-only e as opções Secure/HSTS são ativadas em produção.
- O repositório não deve conter banco SQLite, sessões, `.env`, dados escolares reais ou contatos pessoais.
- Auditorias podem ser exportadas pela gestão em CSV.

## Antes de produção

1. Use PostgreSQL persistente e HTTPS.
2. Defina `SECRET_KEY`, hosts e origens CSRF explicitamente.
3. Configure e teste e-mail.
4. Revise contas administrativas e remova usuários de desenvolvimento.
5. Garanta armazenamento persistente para mídia se fotos/logos forem usados.
6. Execute os workflows de backend e Android.
7. Faça backup do banco pelo provedor e teste restauração periodicamente.

## Backups

O projeto não apresenta um botão de “backup” que apenas registre uma linha no banco. Backups reais devem ser executados no PostgreSQL/provedor e possuir política de retenção e restauração testada.

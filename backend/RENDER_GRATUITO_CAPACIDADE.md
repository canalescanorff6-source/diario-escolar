# Render gratuito, capacidade e cuidados

Este projeto foi ajustado para evitar criação automática de serviço pago no Render.

## O que mudou

- `render.yaml` usa `plan: free` para o web service.
- O banco do Render foi removido do blueprint, porque o Postgres Free do Render expira em 30 dias.
- `DATABASE_URL` ficou como variável obrigatória (`sync: false`). Use um PostgreSQL externo gratuito, como Neon ou Supabase.
- O envio de e-mail no Render Free foi preparado para Brevo API, porque o Render Free bloqueia SMTP nas portas 25, 465 e 587.
- `buildCommand` usa `bash build.sh`, evitando erro de permissão do arquivo `build.sh`.

## Variáveis obrigatórias no Render

```text
DATABASE_URL=postgresql://...
BREVO_API_KEY=sua-chave-api-da-brevo
BREVO_SENDER_EMAIL=email-remetente-verificado
DEFAULT_FROM_EMAIL=Diário IA Escolar <email-remetente-verificado>
```

## Sobre 6 escolas e 180 professores

180 professores cadastrados não é problema para o sistema. O ponto crítico é quantos acessam ao mesmo tempo.

- Uso leve, poucos professores ao mesmo tempo: pode funcionar em piloto gratuito.
- Todos os professores lançando aula/frequência ao mesmo tempo: Render Free não é recomendado.
- Para uso real de escola, o ideal é uma VPS Always Free da Oracle ou plano pago pequeno quando houver recurso.

## Atenção

Não use SQLite no Render para dados reais. O filesystem do Render é temporário, e dados locais podem sumir em restart/redeploy/spin down.

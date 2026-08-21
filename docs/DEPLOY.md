# Implantação do Diário Escolar Pro

## Render + PostgreSQL

O `render.yaml` usa `backend/` como diretório raiz, executa `build.sh`, aplica migrations no pre-deploy e inicia Gunicorn.

### Variáveis obrigatórias

- `SECRET_KEY`: gerada pelo provedor ou por um gerenciador de segredos.
- `DATABASE_URL`: PostgreSQL persistente com SSL.
- `DJANGO_REQUIRE_DATABASE_URL=True`.
- `ALLOWED_HOSTS`: domínios autorizados.
- `CSRF_TRUSTED_ORIGINS`: origens HTTPS autorizadas.

Para e-mail de autorização/recuperação, configure o backend e as credenciais da Brevo ou outro provedor compatível.

Use `backend/.env.example` apenas como referência; nunca faça commit de valores reais.

## Banco

Em produção, use PostgreSQL. O SQLite existe somente como fallback de desenvolvimento local e está ignorado pelo Git.

O deploy executa:

```bash
python manage.py migrate --noinput
```

Antes de publicar uma alteração de models, confirme no GitHub Actions que `makemigrations --check --dry-run` passa sem mudanças pendentes.

## Arquivos enviados

Fotos e brasões gravados em `MEDIA_ROOT` funcionam localmente. Em hospedagem com filesystem efêmero, configure armazenamento persistente externo antes de depender desses arquivos em produção.

## Primeiro acesso

Prefira `python manage.py createsuperuser`. Se precisar do comando específico do projeto:

```bash
python manage.py criar_gestor_inicial --usuario gestor --senha "SENHA-FORTE-AQUI" --email gestor@escola.com
```

O comando não possui senha padrão.

# Migração segura para o Diário Escolar Pro 2.0

Este pacote foi preparado para substituir o código antigo **sem apagar o banco PostgreSQL existente**. O banco não faz parte do ZIP e não deve ser enviado ao GitHub.

## Antes de substituir o repositório

1. Faça um backup real do PostgreSQL no provedor (Neon, Supabase, Render ou outro).
2. Guarde as variáveis de ambiente atuais: `DATABASE_URL`, `SECRET_KEY`, e-mail e domínio.
3. Não copie `db.sqlite3`, `.env`, `media/`, sessões ou arquivos temporários para o GitHub.
4. Se o banco antigo já estiver em produção, mantenha a mesma `DATABASE_URL` no novo deploy.

## Substituição do código

Na raiz do repositório, remova os arquivos antigos que não existem mais no pacote e copie o conteúdo desta versão. É importante substituir a árvore, não apenas sobrepor os arquivos, para que templates/rotas legadas realmente desapareçam.

A raiz deve conter, entre outros:

```text
.github/
backend/
docs/
mobile-android/
.gitignore
.python-version
README.md
VERSION
build.sh
render.yaml
requirements.txt
```

## Primeiro deploy

O Render executa migrations antes de iniciar o Gunicorn. No GitHub, aguarde o workflow **Backend quality** concluir com sucesso.

Se um banco muito antigo acusar `InconsistentMigrationHistory`, use **somente nesse caso**:

```bash
cd backend
python manage.py reparar_migrations_academico
python manage.py migrate --noinput
```

O comando existe apenas para compatibilidade com instalações antigas.

## Depois do deploy

Valide estes fluxos antes de liberar para professores:

- login de professor e gestão;
- cadastro/vínculo de professor, turma e disciplina;
- grade de horários;
- registro de aula;
- chamada P/F/FJ;
- duas aulas da mesma disciplina no mesmo dia;
- lançamento de notas;
- relatórios e documentos;
- permissões: um professor não deve visualizar turma alheia;
- recuperação de senha/e-mail;
- API Android `/api/v1/`.

## Android

Crie no GitHub a variável de repositório `DIARIO_API_BASE_URL` com a URL HTTPS do sistema. O workflow **Android APK** gera um APK de teste. A publicação na Play Store exige assinatura de release/AAB separada do repositório.

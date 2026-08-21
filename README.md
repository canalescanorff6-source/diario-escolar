# Diário Escolar Pro 2.0.1

**Versão:** 2.0.0

Plataforma de diário de classe e gestão acadêmica com **website Django responsivo**, **PWA** e **aplicativo Android nativo** usando o mesmo banco de dados e as mesmas regras acadêmicas.

## Estrutura

```text
backend/         Django, regras acadêmicas, templates, API e PostgreSQL
mobile-android/  Aplicativo Android nativo (Java 17, SDK 36)
docs/            Guias de implantação, Android e segurança
.github/         Testes automáticos e geração de APK
render.yaml      Blueprint de implantação no Render
```

## Principais fluxos

**Professor:** painel, turmas, agenda, registro de aula, chamada P/F/FJ, notas, Diário de Classe, relatórios e assistente pedagógico.

**Gestão:** escola, pessoas, vínculos, horários, calendário, acompanhamento do diário, fechamentos, documentos, relatórios, auditoria e configurações acadêmicas.

**Android:** login do professor, agenda do dia, chamada, conteúdo da aula, armazenamento local criptografado, cache da agenda/alunos e fila de sincronização offline.

## Executar localmente

Requer Python 3.13+.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Nunca publique `backend/.env`, `db.sqlite3`, arquivos de mídia locais, keystores Android ou credenciais.

## Validação

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py collectstatic --noinput
```

O workflow **Backend quality** executa esses passos em todo push/PR para `main`.

## Android

Configure a variável de repositório `DIARIO_API_BASE_URL` com a URL HTTPS do website, por exemplo `https://seu-dominio.com/`. O workflow **Android APK** gera um APK de debug como artefato do GitHub Actions.

Para compilação local e detalhes de sincronização, consulte [`docs/ANDROID.md`](docs/ANDROID.md).

Para substituir uma instalação/repositório antigo com segurança, consulte [`docs/MIGRACAO_V2.md`](docs/MIGRACAO_V2.md). O histórico completo da limpeza está em [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

## Produção

O projeto está preparado para Render + PostgreSQL persistente. Consulte [`docs/DEPLOY.md`](docs/DEPLOY.md) e [`docs/SECURITY.md`](docs/SECURITY.md) antes da publicação.

## Regras acadêmicas

Média mínima de aprovação, faixa de atenção e frequência mínima são configuradas na escola e consumidas por dashboards, relatórios e análises. A aplicação não deve preencher nota inexistente com valor fictício.

## Licença e dados

Este repositório não inclui dados escolares reais, banco SQLite, sessões, e-mails pessoais, telefones de suporte ou senhas padrão.

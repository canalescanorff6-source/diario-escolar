# Validação final — versão 2.0.0

## Verificações executadas neste pacote

- Todos os arquivos Python foram analisados/compilados sintaticamente sem erro.
- Todas as referências literais de templates (`render`, `extends` e `include`) apontam para arquivos existentes.
- Todas as referências literais `{% url %}`, `redirect()` e `reverse()` verificadas apontam para nomes de rota existentes.
- Não há nomes ou caminhos duplicados no `apps/core/urls.py`.
- Referências estáticas literais dos templates apontam para arquivos existentes.
- `manifest.webmanifest` é JSON válido.
- XML do Android e `AndroidManifest.xml` são bem formados.
- `render.yaml` e os workflows do GitHub Actions são YAML válidos.
- Caches Python, banco SQLite, `.env`, `staticfiles/` e arquivos de build não fazem parte do pacote final.

## Redução estrutural

Comparação com o pacote completo originalmente recebido:

| Item | Antes | 2.0.0 |
|---|---:|---:|
| Rotas web principais | 231 | 73 |
| Templates HTML | 235 | 77 |
| CSS principal | ~2.496 linhas / ~1.660 `!important` | 374 linhas / 1 `!important` |
| Arquivos Python do backend | 79 | 67 |

A redução remove principalmente páginas e rotas de etapa/checkup/render, duplicações visuais e módulos de desenvolvimento que não deveriam aparecer no produto.

## Validação que deve rodar no GitHub

O ambiente usado para preparar este ZIP não possui Django nem Android SDK/Gradle instalados. Por isso, os checks de runtime/build foram colocados nos workflows do GitHub e devem ficar verdes após o push:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- migrations em banco limpo
- testes automatizados
- `collectstatic`
- build do APK Android com SDK 36

Não libere a nova versão em produção se o workflow **Backend quality** falhar. Consulte `MIGRACAO_V2.md` antes de apontar o novo código para o banco existente.

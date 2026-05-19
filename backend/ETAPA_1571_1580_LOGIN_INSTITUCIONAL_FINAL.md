# ETAPA 1571–1580 — Login institucional final + e-mail autorizado

Alterações:
- Refinado o layout do login institucional para ficar mais preenchido e premium.
- A tela passa a mostrar todos os campos institucionais mesmo com banco limpo: Escola, Aldeia, Terra Indígena e Gestão Escolar.
- Mensagens de campo vazio agora usam “Configurar no painel da gestão”.
- Mantida a logo fixa em `static/img/logo_escola_login.png` para Render.
- Definido e-mail autorizado padrão para receber código da gestão: `thiago01268230@gmail.com`.
- Mantida compatibilidade com variável de ambiente `GESTAO_AUTORIZACAO_EMAIL` no Render.
- Removidos rastros antigos da raiz e caches Python.

Validações executadas:
- `python manage.py check`
- `python manage.py visual_unico_check_diario --strict`
- `python manage.py validar_polimento_final_1341_1360 --strict`
- `python manage.py validar_diario_classe_1281_1340 --strict`
- `python manage.py validar_fluxo_real_diario --strict`
- `python manage.py mega_checkup_diario --strict --show-skipped`
- `python manage.py render_prontidao_diario`
- `DEBUG=False RENDER=true python manage.py check --deploy`
- `python manage.py collectstatic --noinput --dry-run`

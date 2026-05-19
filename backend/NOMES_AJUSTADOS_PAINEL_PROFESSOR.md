# Nomes ajustados no Painel do Professor

Este pacote recebeu uma revisão específica nas telas do professor para tirar termos com cara de desenvolvimento, etapa técnica ou operação interna.

## Principais alterações

| Antes | Agora |
|---|---|
| Fluxo operacional premium | Rotina do Professor |
| Centro/central escolar no painel do professor | Central do Professor |
| Professor • operação real | Professor • rotina de aula |
| Conferência gigante | Conferência do diário |
| Minha rotina operacional | Minha rotina de aula |
| Conferência limpo do meu Diário Escolar | Conferência do meu Diário de Classe |
| Fluxo oficial preservado | Organização dos lançamentos |
| Saúde do sistema final | Conferência do Diário do Professor |
| Minha operação | Minha rotina |
| Rotas críticas | Acessos do professor |
| Blindagem final | Conferência final |
| Roteiro final do professor | Roteiro do professor |
| Meus Horários Reais | Meus Horários |
| Estação operacional do professor | Rotina do Professor |
| Pendências operacionais | Pendências do diário |
| Professor • Diário Oficial premium | Professor • Diário de Classe |
| Meu diário em fluxo único | Meu Diário de Classe |
| Aula rápida oficial | Aula rápida |
| Lançamento Oficial P/F/FJ | Lançamento de Frequência P/F/FJ |
| RELEASE FINAL · PROFESSOR | DIÁRIO ESCOLAR · PROFESSOR |
| Checklist mensal turma/disciplina | Conferência mensal da turma |
| Meu consolidado mensal / Minha Matriz Mensal | Meu resumo mensal |
| Minha trilha mensal do Diário | Linha do tempo mensal do Diário |

## Observação técnica

Não foram renomeados arquivos, rotas Django, funções Python, nomes de templates, nomes internos com `diario_real`, `checkup`, `render`, `premium` ou URLs. Isso evita quebrar imports, `{% url %}`, migrations e telas antigas. A mudança foi focada nos textos visíveis para o professor.

## Conferência feita

- `python manage.py check` passou sem erros.
- `/professor/` abriu com status 200.
- `/professor/centro-operacional/` abriu com status 200.
- `/professor/carga-horaria/` abriu com status 200.
- `/professor/diario-oficial/` abriu com status 200.
- `/professor/diario/prontidao-lancamentos-163/` abriu com status 200.
- `/professor/checkup/etapas-861-900/` abriu com status 200.
- `/professor/checkup/etapas-901-960/` abriu com status 200.
- `/professor/checkup/etapas-961-1000/` abriu com status 200.
- `/professor/checkup/etapas-1001-1080/` abriu com status 200.
- `/professor/aula-rapida/` redirecionou corretamente quando não havia aula/horário selecionado.

# Nomes ajustados para ficar com cara de Diário Escolar

Este pacote recebeu uma revisão nos textos visíveis do sistema para tirar termos técnicos, estranhos ou com cara de desenvolvimento, mantendo as URLs e nomes internos para não quebrar o projeto.

## Principais alterações

| Antes | Agora |
|---|---|
| Consolidação gigante da operação escolar | Painel de Prontidão Escolar |
| Prontidão real da escola antes do Diário Oficial documental e do fluxo do professor | Acompanhe o que já está configurado e o que falta para liberar o Diário Escolar |
| Gestão premium | Gestão escolar |
| Centro operacional da gestão | Central da Gestão Escolar |
| Centro operacional do professor | Central do Professor |
| Diário Real | Diário Escolar |
| Diário real | Diário escolar |
| Meu Diário oficial | Meu Diário de Classe |
| Operação real de aula | Registro de aula |
| Diário Operacional do Aluno | Diário do Aluno |
| Mapa Operacional do Diário Real | Mapa de Lançamentos do Diário Escolar |
| Dossiê do aluno no Diário Real | Dossiê Escolar do Aluno |
| Analytics Executivo Avançado | Indicadores da Gestão |
| Painel Executivo | Painel da Gestão |
| PAINEL EXECUTIVO OFICIAL | PAINEL DA GESTÃO ESCOLAR |
| Qualidade final | Conferência final |
| Homologação do Diário Real | Validação do Diário Escolar |
| Lacunas do Diário Real | Pendências do Diário Escolar |
| Rotas oficiais do Diário Real | Acessos do Diário Escolar |
| Tela consolidada no padrão premium | Tela integrada ao Diário Escolar |
| Render/PostgreSQL | Publicação/Banco de dados |
| Prontidão Render | Publicação do sistema |

## Observação técnica

Não foram renomeados arquivos, rotas Django, funções Python ou nomes internos com `premium`, `render`, `diario_real`, `checkup` etc., porque isso poderia quebrar imports, URLs e templates. A mudança foi focada nos textos que aparecem para gestão, professor e tela de login.

## Conferência feita

- `python manage.py check` passou sem erros.
- `/gestao/` abriu com status 200.
- `/gestao/centro-operacional/` abriu com status 200.
- `/gestao/diario-oficial/` abriu com status 200.
- `/gestao/checkup/etapas-861-900/` abriu com status 200.
- `/professor/` abriu com status 200.
- `/turmas/` abriu com status 200.
- `/professor/centro-operacional/` abriu com status 200.
- `/solicitar-codigo-gestao/` abriu com status 200.

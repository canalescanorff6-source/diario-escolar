from django.urls import path

from . import views


urlpatterns = [
    path('healthz/', views.healthz, name='healthz'),
    path('criar-conta-gestao/', views.criar_conta_gestao_autorizada, name='criar_conta_gestao_autorizada'),
    path('solicitar-codigo-gestao/', views.solicitar_codigo_gestao, name='solicitar_codigo_gestao'),
    path('ativar-acesso-gestao/', views.ativar_acesso_gestao, name='ativar_acesso_gestao'),

    path(
        'professor/',
        views.dashboard_professor_home,
        name='dashboard_professor_home'
    ),


    # =====================================================
    # CORREÇÃO FUNCIONAL — atalhos do professor
    # =====================================================
    path('professor/alunos/', views.professor_alunos, name='professor_alunos'),
    path('professor/relatorios/', views.professor_relatorios, name='professor_relatorios'),
    path('professor/configuracoes/', views.professor_configuracoes, name='professor_configuracoes'),


    path(
        'gestao/',
        views.dashboard_gestao,
        name='dashboard_gestao'
    ),

    # =====================================================
    # GESTÃO ESCOLAR ADMINISTRATIVA
    # =====================================================

    path(
        'gestao/escola/',
        views.gestao_escola,
        name='gestao_escola'
    ),

    path(
        'gestao/professores/',
        views.gestao_professores,
        name='gestao_professores'
    ),

    path(
        'gestao/vinculos/',
        views.gestao_vinculos,
        name='gestao_vinculos'
    ),

    path(
        'gestao/horarios/',
        views.gestao_horarios,
        name='gestao_horarios'
    ),


    path(
        'gestao/inteligencia/',
        views.gestao_inteligencia,
        name='gestao_inteligencia'
    ),

    path(
        'gestao/relatorios/',
        views.gestao_relatorios,
        name='gestao_relatorios'
    ),



    path(
        'gestao/calendario/',
        views.gestao_calendario,
        name='gestao_calendario'
    ),

    path(
        'gestao/fechamentos/',
        views.gestao_fechamentos,
        name='gestao_fechamentos'
    ),

    path(
        'gestao/pareceres/',
        views.gestao_pareceres,
        name='gestao_pareceres'
    ),

    path(
        'gestao/assinaturas/',
        views.gestao_assinaturas,
        name='gestao_assinaturas'
    ),

    path(
        'gestao/alunos/',
        views.gestao_alunos,
        name='gestao_alunos'
    ),




    path(
        'gestao/historico-alunos/',
        views.gestao_historico_alunos,
        name='gestao_historico_alunos'
    ),

    path(
        'gestao/aluno/<int:aluno_id>/ficha/',
        views.gestao_ficha_aluno,
        name='gestao_ficha_aluno'
    ),

    path(
        'gestao/auditoria/',
        views.gestao_auditoria,
        name='gestao_auditoria'
    ),

    path(
        'gestao/documentos/',
        views.gestao_documentos,
        name='gestao_documentos'
    ),

    path(
        'gestao/notificacoes/',
        views.gestao_notificacoes,
        name='gestao_notificacoes'
    ),

    path(
        'gestao/notificacoes/<int:notificacao_id>/resolver/',
        views.gestao_notificacao_resolver,
        name='gestao_notificacao_resolver'
    ),

    path(
        '',
        views.dashboard_professor,
        name='dashboard_professor'
    ),

    path(
        'turmas/',
        views.turmas,
        name='turmas'
    ),

    path(
        'diario/',
        views.diario,
        name='diario'
    ),

    # =====================================================
    # PÁGINA FREQUÊNCIA
    # =====================================================

    path(
        'frequencia/',
        views.frequencia,
        name='frequencia'
    ),

    # =====================================================
    # DETALHE DA TURMA
    # =====================================================

    path(
        'turma/<int:turma_id>/diario/',
        views.turma_detalhe,
        name='turma_detalhe'
    ),

    # =====================================================
    # FREQUÊNCIA DA TURMA
    # =====================================================

    path(
        'turma/<int:turma_id>/frequencia/',
        views.frequencia_turma,
        name='frequencia_turma'
    ),


    path(
        'turma/<int:turma_id>/frequencia-mensal/',
        views.frequencia_mensal_turma,
        name='frequencia_mensal_turma'
    ),


    path(
        'turma/<int:turma_id>/registro-aulas-mensal/',
        views.registro_aulas_mensal_turma,
        name='registro_aulas_mensal_turma'
    ),

    path(
        'turma/<int:turma_id>/notas/',
        views.notas_turma,
        name='notas_turma'
    ),


    path(
        'aluno/<int:aluno_id>/boletim/',
        views.boletim_aluno,
        name='boletim_aluno'
    ),


    path(
        'turma/<int:turma_id>/diario-classe/',
        views.diario_classe_turma,
        name='diario_classe_turma'
    ),

    path(
        'turma/<int:turma_id>/boletim-ia/',
        views.boletim_ia,
        name='boletim_ia'
    ),

    path('gestao/executivo/', views.gestao_executivo, name='gestao_executivo'),
    path('gestao/backups/', views.gestao_backups, name='gestao_backups'),
    path('gestao/integracoes/', views.gestao_integracoes, name='gestao_integracoes'),
    path('gestao/configuracoes/', views.gestao_configuracoes, name='gestao_configuracoes'),

    path('professor/ia-pedagogica/', views.professor_ia_pedagogica, name='professor_ia_pedagogica'),
    path('gestao/ia-pedagogica/', views.gestao_ia_pedagogica, name='gestao_ia_pedagogica'),

    # =====================================================
    # ETAPA 13 — Exportações oficiais e alertas inteligentes
    # =====================================================
    path('gestao/documentos/boletim/<int:aluno_id>/oficial/', views.gestao_documento_boletim_oficial, name='gestao_documento_boletim_oficial'),
    path('gestao/documentos/diario/<int:turma_id>/oficial/', views.gestao_documento_diario_oficial, name='gestao_documento_diario_oficial'),
    path('gestao/relatorios/executivo/oficial/', views.gestao_relatorio_executivo_oficial, name='gestao_relatorio_executivo_oficial'),
    path('gestao/notificacoes/gerar-inteligentes/', views.gestao_notificacoes_gerar_inteligentes, name='gestao_notificacoes_gerar_inteligentes'),
    path('gestao/calendario/impressao/', views.gestao_calendario_impressao, name='gestao_calendario_impressao'),


    # =====================================================
    # ETAPA 14 — Governança escolar, fechamento anual e relatórios avançados
    # =====================================================
    path('gestao/fechamento-anual/', views.gestao_fechamento_anual, name='gestao_fechamento_anual'),
    path('gestao/relatorios/avancado/', views.gestao_relatorio_avancado, name='gestao_relatorio_avancado'),
    path('gestao/auditoria/exportacao/', views.gestao_auditoria_exportacao, name='gestao_auditoria_exportacao'),
    path('gestao/assinaturas/pendentes/', views.gestao_assinaturas_pendentes, name='gestao_assinaturas_pendentes'),
    path('gestao/calendario/validacao/', views.gestao_calendario_validacao, name='gestao_calendario_validacao'),
    path('professor/alertas-inteligentes/', views.professor_alertas_inteligentes, name='professor_alertas_inteligentes'),


    # =====================================================
    # ETAPA 15 — Conselho de classe, recuperação e intervenção pedagógica
    # =====================================================
    path('gestao/fechamentos/checklist/', views.gestao_checklist_fechamento, name='gestao_checklist_fechamento'),
    path('gestao/recuperacao/mapa/', views.gestao_mapa_recuperacao, name='gestao_mapa_recuperacao'),
    path('gestao/conselho-classe/ata/', views.gestao_ata_conselho_classe, name='gestao_ata_conselho_classe'),
    path('gestao/turma/<int:turma_id>/dossie/', views.gestao_dossie_turma, name='gestao_dossie_turma'),
    path('professor/plano-intervencao/', views.professor_plano_intervencao, name='professor_plano_intervencao'),


    # =====================================================
    # ETAPA 16 — Analytics, permissões e preparação para executáveis
    # =====================================================
    path('gestao/analytics/avancado/', views.gestao_analytics_avancado, name='gestao_analytics_avancado'),
    path('gestao/ranking-pedagogico/', views.gestao_ranking_pedagogico, name='gestao_ranking_pedagogico'),
    path('gestao/permissoes/centro/', views.gestao_centro_permissoes, name='gestao_centro_permissoes'),
    path('gestao/executaveis/preparacao/', views.gestao_preparacao_executaveis, name='gestao_preparacao_executaveis'),
    path('gestao/logs/avancados/', views.gestao_logs_avancados, name='gestao_logs_avancados'),


    # =====================================================
    # ETAPA 17 — Busca global, saúde SaaS, comunicação e pendências
    # =====================================================
    path('gestao/busca-global/', views.gestao_busca_global, name='gestao_busca_global'),
    path('gestao/saude-sistema/', views.gestao_saude_sistema, name='gestao_saude_sistema'),
    path('gestao/comunicacao/responsaveis/', views.gestao_comunicacao_responsaveis, name='gestao_comunicacao_responsaveis'),
    path('gestao/documentos/declaracao/<int:aluno_id>/', views.gestao_documento_declaracao_matricula, name='gestao_documento_declaracao_matricula'),
    path('gestao/pendencias/professores/', views.gestao_pendencias_professores, name='gestao_pendencias_professores'),
    path('professor/pendencias/', views.professor_central_pendencias, name='professor_central_pendencias'),



    # =====================================================
    # ETAPAS 97–108 — Fechamento acelerado seguro
    # =====================================================
    path('gestao/final/consolidacao-tecnica/', views.gestao_consolidacao_final_tecnica, name='gestao_consolidacao_final_tecnica'),
    path('gestao/final/publicacao-comercial/', views.gestao_publicacao_comercial, name='gestao_publicacao_comercial'),
    path('gestao/final/testes/', views.gestao_testes_finais, name='gestao_testes_finais'),
    path('gestao/final/migracao-dados/', views.gestao_migracao_dados_producao, name='gestao_migracao_dados_producao'),
    path('gestao/final/congelamento-release/', views.gestao_congelamento_release, name='gestao_congelamento_release'),
    path('gestao/final/pronto-lancamento/', views.gestao_centro_pronto_lancamento, name='gestao_centro_pronto_lancamento'),
    path('gestao/final/ultima-milha/', views.gestao_ultima_milha, name='gestao_ultima_milha'),
    path('gestao/final/pos-final/', views.gestao_mapa_pos_final, name='gestao_mapa_pos_final'),
    path('gestao/final/projeto-concluido/', views.gestao_status_projeto_concluido, name='gestao_status_projeto_concluido'),
    path('professor/final/release/', views.professor_modo_release_final, name='professor_modo_release_final'),
    path('professor/final/checklist/', views.professor_checklist_lancamento, name='professor_checklist_lancamento'),
    path('professor/final/assistente-producao/', views.professor_assistente_producao, name='professor_assistente_producao'),

    # =====================================================
    # CHECKUP FINAL — aliases seguros para links legados
    # =====================================================
    path('gestao/central-documental-premium/', views.gestao_pagina_legada_segura, {'slug': 'central-documental'}, name='gestao_central_documental_premium'),
    path('gestao/indicadores-institucionais-avancados/', views.gestao_pagina_legada_segura, {'slug': 'indicadores-institucionais'}, name='gestao_indicadores_institucionais_avancados'),
    path('gestao/monitoramento-evasao-escolar/', views.gestao_pagina_legada_segura, {'slug': 'monitoramento-evasao'}, name='gestao_monitoramento_evasao_escolar'),
    path('gestao/fluxo-aprovacao-reprovacao/', views.gestao_pagina_legada_segura, {'slug': 'fluxo-aprovacao'}, name='gestao_fluxo_aprovacao_reprovacao'),
    path('gestao/painel-consolidado-desempenho/', views.gestao_pagina_legada_segura, {'slug': 'desempenho-consolidado'}, name='gestao_painel_consolidado_desempenho'),
    path('gestao/inteligencia-fechamento-anual/', views.gestao_pagina_legada_segura, {'slug': 'inteligencia-fechamento'}, name='gestao_inteligencia_fechamento_anual'),


    # =====================================================
    # DIÁRIO OFICIAL REAL — central consolidada
    # =====================================================
    path('gestao/diario-oficial/', views.gestao_diario_oficial, name='gestao_diario_oficial'),
    path('professor/diario-oficial/', views.professor_diario_oficial, name='professor_diario_oficial'),
    path('gestao/aluno/<int:aluno_id>/ficha-oficial/', views.gestao_ficha_aluno_oficial, name='gestao_ficha_aluno_oficial'),

    # =====================================================
    # DIÁRIO OFICIAL REAL — detalhe completo e atalhos funcionais
    # =====================================================
    path('turma/<int:turma_id>/diario-oficial-completo/', views.diario_oficial_turma_completo, name='diario_oficial_turma_completo'),
    path('turma/<int:turma_id>/disciplina/<int:disciplina_id>/frequencia-mensal/', views.frequencia_disciplina_mensal, name='frequencia_disciplina_mensal'),
    path('gestao/aluno/<int:aluno_id>/painel-integrado/', views.gestao_aluno_painel_integrado, name='gestao_aluno_painel_integrado'),



    # =====================================================
    # ETAPAS 67–78 — Diário real avançado e atalhos funcionais
    # =====================================================
    path('gestao/diario-oficial/matriz-turnos/', views.gestao_diario_matriz_turnos, name='gestao_diario_matriz_turnos'),
    path('gestao/diario-oficial/consolidado-anual/', views.gestao_diario_consolidado_anual, name='gestao_diario_consolidado_anual'),
    path('gestao/frequencia/conferencia-mensal/', views.gestao_conferencia_frequencia_mensal, name='gestao_conferencia_frequencia_mensal'),
    path('gestao/aluno/<int:aluno_id>/dossie-completo/', views.gestao_aluno_dossie_completo, name='gestao_aluno_dossie_completo'),
    path('professor/registro-rapido-aula/', views.professor_registro_rapido_aula, name='professor_registro_rapido_aula'),
    path('professor/frequencia-rapida/', views.professor_frequencia_rapida, name='professor_frequencia_rapida'),


    # =====================================================
    # DIÁRIO REAL — validação completa e fluxos oficiais solicitados
    # =====================================================
    path('gestao/diario-oficial/validacao-completa/', views.gestao_diario_validacao_completa, name='gestao_diario_validacao_completa'),
    path('gestao/diario-oficial/estrutura-turnos-reais/', views.gestao_estrutura_turnos_reais, name='gestao_estrutura_turnos_reais'),
    path('gestao/professor/<int:professor_id>/diario-real/', views.gestao_professor_diario_real, name='gestao_professor_diario_real'),
    path('gestao/aluno/<int:aluno_id>/diario-completo/', views.gestao_aluno_diario_completo, name='gestao_aluno_diario_completo'),
    path('professor/matriz-mensal/', views.professor_minha_matriz_mensal, name='professor_minha_matriz_mensal'),


    # =====================================================
    # ETAPAS 109–114 — Diário real operacional por aluno
    # =====================================================
    path('gestao/diario-oficial/mapa-operacional/', views.gestao_diario_mapa_operacional, name='gestao_diario_mapa_operacional'),
    path('gestao/aluno/<int:aluno_id>/diario-operacional/', views.gestao_aluno_diario_operacional, name='gestao_aluno_diario_operacional'),
    path('gestao/diario-oficial/conferencia-vinculos-horarios/', views.gestao_conferencia_vinculos_horarios, name='gestao_conferencia_vinculos_horarios'),
    path('professor/horarios-reais/', views.professor_meus_horarios_reais, name='professor_meus_horarios_reais'),
    path('professor/turma/<int:turma_id>/aluno/<int:aluno_id>/diario-operacional/', views.professor_aluno_diario_operacional, name='professor_aluno_diario_operacional'),
    path('professor/turma/<int:turma_id>/aluno/<int:aluno_id>/frequencia-oficial/', views.professor_lancamento_frequencia_aluno, name='professor_lancamento_frequencia_aluno'),



    # =====================================================
    # ETAPAS 115–120 — Checkup geral e continuidade oficial
    # =====================================================
    path('gestao/diario-oficial/checkup-geral/', views.gestao_checkup_diario_real, name='gestao_checkup_diario_real'),
    path('gestao/diario-oficial/matriz-turnos-oficial/', views.gestao_matriz_turnos_oficial, name='gestao_matriz_turnos_oficial'),
    path('gestao/diario-oficial/lacunas/', views.gestao_lacunas_diario_real, name='gestao_lacunas_diario_real'),
    path('professor/checkup-meu-diario/', views.professor_checkup_meu_diario, name='professor_checkup_meu_diario'),

    # =====================================================
    # ETAPAS 121–126 — Consolidação oficial mensal/anual do Diário Escolar
    # =====================================================
    path('gestao/diario-oficial/consolidado-mensal-real/', views.gestao_consolidado_mensal_diario_real, name='gestao_consolidado_mensal_diario_real'),
    path('gestao/professores/auto-admin/', views.gestao_professores_auto_admin, name='gestao_professores_auto_admin'),
    path('gestao/aluno/<int:aluno_id>/linha-do-tempo-oficial/', views.gestao_aluno_linha_do_tempo_oficial, name='gestao_aluno_linha_do_tempo_oficial'),
    path('gestao/diario-oficial/checkup-121-126/', views.gestao_checkup_etapas_121_126, name='gestao_checkup_etapas_121_126'),
    path('professor/consolidado-mensal/', views.professor_consolidado_mensal, name='professor_consolidado_mensal'),
    path('professor/registro-aula-mensal-oficial/', views.professor_registro_aula_mensal_oficial, name='professor_registro_aula_mensal_oficial'),


    # =====================================================
    # ETAPAS 127–132 — Auditoria, pendências e impressão oficial
    # =====================================================
    path('gestao/diario-oficial/checkup-127/', views.gestao_checkup_geral_diario_real_127, name='gestao_checkup_geral_diario_real_127'),
    path('gestao/diario-oficial/turma/<int:turma_id>/auditoria/', views.gestao_auditoria_diario_turma, name='gestao_auditoria_diario_turma'),
    path('gestao/diario-oficial/pendencias-oficiais/', views.gestao_pendencias_diario_oficial, name='gestao_pendencias_diario_oficial'),
    path('gestao/aluno/<int:aluno_id>/pacote-diario-oficial/', views.gestao_pacote_oficial_aluno_diario, name='gestao_pacote_oficial_aluno_diario'),
    path('gestao/diario-oficial/checkup-127-132/', views.gestao_checkup_etapas_127_132, name='gestao_checkup_etapas_127_132'),
    path('professor/diario-classe/impressao-oficial/', views.professor_diario_classe_impressao_oficial, name='professor_diario_classe_impressao_oficial'),


    # =====================================================
    # ETAPAS 133–138 — Checkup geral, conferência anual e continuidade segura
    # =====================================================
    path('gestao/diario-oficial/checkup-133/', views.gestao_checkup_geral_diario_real_133, name='gestao_checkup_geral_diario_real_133'),
    path('gestao/aluno/<int:aluno_id>/conferencia-anual-diario/', views.gestao_conferencia_anual_aluno_diario, name='gestao_conferencia_anual_aluno_diario'),
    path('gestao/diario-oficial/validador-vinculos-horarios-133/', views.gestao_validador_vinculos_horarios_133, name='gestao_validador_vinculos_horarios_133'),
    path('gestao/diario-oficial/checkup-133-138/', views.gestao_checkup_etapas_133_138, name='gestao_checkup_etapas_133_138'),
    path('professor/frequencia/mapa-anual-disciplina/', views.professor_mapa_frequencia_anual_disciplina, name='professor_mapa_frequencia_anual_disciplina'),
    path('professor/lancamentos/relatorio-mes-oficial/', views.professor_relatorio_lancamentos_mes_oficial, name='professor_relatorio_lancamentos_mes_oficial'),


    # =====================================================
    # ETAPAS 139–144 — Prontidão, fechamento mensal e extrato oficial
    # =====================================================
    path('gestao/diario-oficial/prontidao-139/', views.gestao_prontidao_diario_real_139, name='gestao_prontidao_diario_real_139'),
    path('gestao/aluno/<int:aluno_id>/extrato-mensal-139/', views.gestao_aluno_extrato_mensal_139, name='gestao_aluno_extrato_mensal_139'),
    path('gestao/diario-oficial/checkup-139-144/', views.gestao_checkup_etapas_139_144, name='gestao_checkup_etapas_139_144'),
    path('professor/diario/prontidao-139/', views.professor_prontidao_diario_139, name='professor_prontidao_diario_139'),
    path('professor/diario/fechamento-mensal-139/', views.professor_fechamento_mensal_diario_139, name='professor_fechamento_mensal_diario_139'),


    # =====================================================
    # ETAPAS 145–150 — Consolidação oficial, entrega e auditoria final do Diário Escolar
    # =====================================================
    path('gestao/diario/fechamento-oficial-145/', views.gestao_fechamento_oficial_diario_145, name='gestao_fechamento_oficial_diario_145'),
    path('professor/diario/entrega-mensal-145/', views.professor_entrega_mensal_diario_145, name='professor_entrega_mensal_diario_145'),
    path('gestao/aluno/<int:aluno_id>/prontuario-anual-diario-145/', views.gestao_aluno_prontuario_anual_diario_145, name='gestao_aluno_prontuario_anual_diario_145'),
    path('gestao/diario/matriz-turnos-conferencia-145/', views.gestao_matriz_turnos_conferencia_145, name='gestao_matriz_turnos_conferencia_145'),
    path('gestao/diario/rotas-145/', views.gestao_rotas_diario_real_145, name='gestao_rotas_diario_real_145'),
    path('gestao/diario/checkup-145-150/', views.gestao_checkup_etapas_145_150, name='gestao_checkup_etapas_145_150'),


    # =====================================================
    # ETAPAS 151–156 — Homologação final, trilha de lançamentos e painel do aluno
    # =====================================================
    path('gestao/diario/homologacao-151/', views.gestao_homologacao_diario_real_151, name='gestao_homologacao_diario_real_151'),
    path('gestao/diario/trilha-lancamentos-151/', views.gestao_trilha_lancamentos_diario_151, name='gestao_trilha_lancamentos_diario_151'),
    path('gestao/aluno/<int:aluno_id>/painel-diario-real-151/', views.gestao_painel_aluno_diario_real_151, name='gestao_painel_aluno_diario_real_151'),
    path('professor/diario/trilha-mensal-151/', views.professor_trilha_mensal_diario_151, name='professor_trilha_mensal_diario_151'),
    path('professor/diario/resumo-anual-151/', views.professor_resumo_anual_diario_151, name='professor_resumo_anual_diario_151'),
    path('gestao/diario/checkup-151-156/', views.gestao_checkup_etapas_151_156, name='gestao_checkup_etapas_151_156'),


    # =====================================================
    # ETAPAS 157–162 — Integridade final, matriz de turnos, agenda e checklist
    # =====================================================
    path('gestao/diario/integridade-157/', views.gestao_integridade_diario_real_157, name='gestao_integridade_diario_real_157'),
    path('gestao/diario/matriz-turnos-157/', views.gestao_matriz_turnos_diario_real_157, name='gestao_matriz_turnos_diario_real_157'),
    path('gestao/diario/auditoria-fj-157/', views.gestao_auditoria_fj_diario_real_157, name='gestao_auditoria_fj_diario_real_157'),
    path('professor/diario/agenda-semanal-157/', views.professor_agenda_semanal_diario_real_157, name='professor_agenda_semanal_diario_real_157'),
    path('professor/diario/checklist-turma-disciplina-157/', views.professor_checklist_turma_disciplina_157, name='professor_checklist_turma_disciplina_157'),
    path('gestao/diario/checkup-157-162/', views.gestao_checkup_etapas_157_162, name='gestao_checkup_etapas_157_162'),


    # =====================================================
    # ETAPAS 163–168 — Conferência final, livro oficial e prontidão de lançamento
    # =====================================================
    path('gestao/diario/conferencia-final-163/', views.gestao_conferencia_final_diario_real_163, name='gestao_conferencia_final_diario_real_163'),
    path('gestao/diario/turma/<int:turma_id>/livro-163/', views.gestao_livro_diario_turma_163, name='gestao_livro_diario_turma_163'),
    path('gestao/aluno/<int:aluno_id>/frequencia-anual-disciplina-163/', views.gestao_aluno_frequencia_anual_disciplina_163, name='gestao_aluno_frequencia_anual_disciplina_163'),
    path('professor/diario/prontidao-lancamentos-163/', views.professor_prontidao_lancamentos_163, name='professor_prontidao_lancamentos_163'),
    path('professor/diario/livro-mensal-163/', views.professor_livro_diario_mensal_163, name='professor_livro_diario_mensal_163'),
    path('gestao/diario/checkup-163-168/', views.gestao_checkup_etapas_163_168, name='gestao_checkup_etapas_163_168'),


    # =====================================================
    # ETAPAS 169–174 — Revisão, espelho e dossiê do Diário Escolar
    # =====================================================
    path('gestao/diario/revisao-oficial-169/', views.gestao_revisao_oficial_diario_real_169, name='gestao_revisao_oficial_diario_real_169'),
    path('gestao/diario/turma/<int:turma_id>/disciplina/<int:disciplina_id>/espelho-169/', views.gestao_espelho_mensal_turma_disciplina_169, name='gestao_espelho_mensal_turma_disciplina_169'),
    path('gestao/aluno/<int:aluno_id>/dossie-diario-real-169/', views.gestao_aluno_dossie_diario_real_169, name='gestao_aluno_dossie_diario_real_169'),
    path('professor/diario/mapa-lancamento-169/', views.professor_mapa_lancamento_diario_169, name='professor_mapa_lancamento_diario_169'),
    path('professor/diario/turma/<int:turma_id>/disciplina/<int:disciplina_id>/espelho-169/', views.professor_espelho_mensal_disciplina_169, name='professor_espelho_mensal_disciplina_169'),
    path('gestao/diario/checkup-169-174/', views.gestao_checkup_etapas_169_174, name='gestao_checkup_etapas_169_174'),

]
# =====================================================
# ETAPAS 181–186 — Checkup de limpeza dos painéis
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-181-186/', views.gestao_checkup_etapas_181_186, name='gestao_checkup_etapas_181_186'),
]

# =====================================================
# ETAPAS 187–192 — Saneamento final dos painéis
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-187-192/', views.gestao_checkup_etapas_187_192, name='gestao_checkup_etapas_187_192'),
]


# =====================================================
# ETAPAS 199–204 — Checkup final dos painéis unificados
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-199-204/', views.gestao_checkup_etapas_199_204, name='gestao_checkup_etapas_199_204'),
]


# =====================================================
# ETAPAS 217–222 — Checkup geral e continuidade dos painéis oficiais
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-217-222/', views.gestao_checkup_etapas_217_222, name='gestao_checkup_etapas_217_222'),
]

# =====================================================
# ETAPAS 223–228 — Limpeza técnica real e status oficial P/F/FJ
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-223-228/', views.gestao_checkup_etapas_223_228, name='gestao_checkup_etapas_223_228'),
]

# =====================================================
# ETAPAS 229–234 — Organização técnica, duplicidades e fluxo oficial
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-229-234/', views.gestao_checkup_etapas_229_234, name='gestao_checkup_etapas_229_234'),
]


# =====================================================
# ETAPAS 235–240 — Auditoria técnica e continuidade limpa
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-235-240/', views.gestao_checkup_etapas_235_240, name='gestao_checkup_etapas_235_240'),
]


# =====================================================
# ETAPAS 241–246 — Fluxo único e painéis limpos
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-241-246/', views.gestao_checkup_etapas_241_246, name='gestao_checkup_etapas_241_246'),
]

# =====================================================
# ETAPAS 247–252 — Consolidação técnica e validação oficial
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-247-252/', views.gestao_checkup_etapas_247_252, name='gestao_checkup_etapas_247_252'),
]



# =====================================================
# ETAPAS 253–258 — Higienização de painéis e mapa mestre sem duplicidade
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-253-258/', views.gestao_checkup_etapas_253_258, name='gestao_checkup_etapas_253_258'),
]


# =====================================================
# ETAPAS 259–264 — Cobertura dos requisitos do Diário Escolar
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-259-264/', views.gestao_checkup_etapas_259_264, name='gestao_checkup_etapas_259_264'),
    path('gestao/checkup/etapas-265-270/', views.gestao_checkup_etapas_265_270, name='gestao_checkup_etapas_265_270'),
]


# =====================================================
# ETAPAS 271–276 — Navegação contextual e visual premium
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-271-276/', views.gestao_checkup_etapas_271_276, name='gestao_checkup_etapas_271_276'),
]

# =====================================================
# ETAPAS 277–282 — bloqueio total de navegação cruzada e acabamento premium
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-277-282/', views.gestao_checkup_etapas_277_282, name='gestao_checkup_etapas_277_282'),
]

# =====================================================
# ETAPAS 301–320 — Operação real, carga horária e gestão sem admin
# =====================================================
urlpatterns += [
    path('professor/operacao-real/', views.professor_operacao_real_301, name='professor_operacao_real_301'),
    path('professor/carga-horaria/', views.professor_carga_horaria_301, name='professor_carga_horaria_301'),
    path('gestao/cadastros-operacionais/', views.gestao_cadastros_operacionais_301, name='gestao_cadastros_operacionais_301'),
    path('gestao/carga-horaria-professores/', views.gestao_carga_horaria_professores_301, name='gestao_carga_horaria_professores_301'),
    path('gestao/checkup/etapas-301-320/', views.checkup_etapas_301_320, name='checkup_etapas_301_320'),
]

# =====================================================
# ETAPAS 321–340 — Fluxo vivo, aula rápida e acabamento premium total
# =====================================================
urlpatterns += [
    path('professor/centro-operacional/', views.professor_centro_operacional_321, name='professor_centro_operacional_321'),
    path('professor/aula-rapida/', views.professor_aula_rapida_321, name='professor_aula_rapida_321'),
    path('professor/aula-rapida/<int:horario_id>/', views.professor_aula_rapida_321, name='professor_aula_rapida_321_horario'),
    path('gestao/centro-operacional/', views.gestao_centro_operacional_321, name='gestao_centro_operacional_321'),
    path('gestao/turnos/normalizar/', views.gestao_turnos_normalizar_321, name='gestao_turnos_normalizar_321'),
    path('gestao/checkup/etapas-321-340/', views.checkup_etapas_321_340, name='checkup_etapas_321_340'),
]

# =====================================================
# ETAPAS 361–380 — Render, UI premium e qualidade operacional
# =====================================================
urlpatterns += [
    path('gestao/publicacao-online/', views.gestao_publicacao_render_361, name='gestao_publicacao_render_361'),
    path('gestao/qualidade-operacional/', views.gestao_qualidade_operacional_361, name='gestao_qualidade_operacional_361'),
    path('professor/rotina-semanal/', views.professor_rotina_semanal_361, name='professor_rotina_semanal_361'),
    path('gestao/checkup/etapas-361-380/', views.checkup_etapas_361_380, name='checkup_etapas_361_380'),

    # =====================================================
    # ETAPAS 381–400 — Checkup funcional e estabilização real
    # =====================================================
    path('gestao/checkup-funcional-381/', views.gestao_checkup_funcional_381, name='gestao_checkup_funcional_381'),
    path('professor/checkup-funcional-381/', views.professor_checkup_funcional_381, name='professor_checkup_funcional_381'),
    path('gestao/roteiro-correcao-381/', views.gestao_roteiro_correcao_381, name='gestao_roteiro_correcao_381'),

]

# =====================================================
# ETAPAS 861–900 — Consolidação gigante premium
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-861-900/', views.gestao_checkup_etapas_861_900, name='gestao_checkup_etapas_861_900'),
    path('professor/checkup/etapas-861-900/', views.professor_checkup_etapas_861_900, name='professor_checkup_etapas_861_900'),
]

# =====================================================
# ETAPAS 901–960 — Finalização gigante premium
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-901-960/', views.gestao_checkup_etapas_901_960, name='gestao_checkup_etapas_901_960'),
    path('professor/checkup/etapas-901-960/', views.professor_checkup_etapas_901_960, name='professor_checkup_etapas_901_960'),
    path('gestao/fechamento-mensal-final/', views.gestao_fechamento_mensal_901, name='gestao_fechamento_mensal_901'),
    path('professor/fechamento-mensal-final/', views.professor_fechamento_mensal_901, name='professor_fechamento_mensal_901'),
    path('gestao/ia-pedagogica-final/', views.gestao_ia_pedagogica_901, name='gestao_ia_pedagogica_901'),
    path('professor/ia-pedagogica-final/', views.professor_ia_pedagogica_901, name='professor_ia_pedagogica_901'),
    path('gestao/relatorios-final/', views.gestao_relatorios_901, name='gestao_relatorios_901'),
    path('professor/relatorios-final/', views.professor_relatorios_901, name='professor_relatorios_901'),
]


# =====================================================
# ETAPAS 961–1000 — Mega checkup, blindagem final e qualidade
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-961-1000/', views.gestao_checkup_etapas_961_1000, name='gestao_checkup_etapas_961_1000'),
    path('professor/checkup/etapas-961-1000/', views.professor_checkup_etapas_961_1000, name='professor_checkup_etapas_961_1000'),
    path('gestao/qualidade-final/', views.gestao_qualidade_final_961, name='gestao_qualidade_final_961'),
    path('professor/qualidade-final/', views.professor_qualidade_final_961, name='professor_qualidade_final_961'),
]


# =====================================================
# ETAPAS 1001–1080 — Cobertura total dos pedidos e conclusão segura
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-1001-1080/', views.gestao_checkup_etapas_1001_1080, name='gestao_checkup_etapas_1001_1080'),
    path('professor/checkup/etapas-1001-1080/', views.professor_checkup_etapas_1001_1080, name='professor_checkup_etapas_1001_1080'),
    path('gestao/finalizacao-total/', views.gestao_finalizacao_total_1001, name='gestao_finalizacao_total_1001'),
    path('professor/finalizacao-total/', views.professor_finalizacao_total_1001, name='professor_finalizacao_total_1001'),
]


# =====================================================
# ETAPAS 1081–1160 — Publicação pronta, capacidade e mega checkup final
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-1081-1160/', views.gestao_checkup_etapas_1081_1160, name='gestao_checkup_etapas_1081_1160'),
    path('professor/checkup/etapas-1081-1160/', views.professor_checkup_etapas_1081_1160, name='professor_checkup_etapas_1081_1160'),
    path('gestao/render-ready/', views.gestao_render_ready_1081, name='gestao_render_ready_1081'),
    path('professor/render-ready/', views.professor_render_ready_1081, name='professor_render_ready_1081'),
    path('gestao/capacidade-render/', views.gestao_capacidade_render_1081, name='gestao_capacidade_render_1081'),
]

# =====================================================
# ETAPAS 1281–1340 — Diário de Classe Oficial Real Completo
# Gestão é a fonte única dos dados. Fluxo Excel/importador antigo removido.
# =====================================================
urlpatterns += [
    path('gestao/checkup/etapas-1281-1340/', views.gestao_checkup_etapas_1281_1340, name='gestao_checkup_etapas_1281_1340'),
    path('gestao/diario-classe-oficial-completo/', views.gestao_diario_classe_oficial_1281, name='gestao_diario_classe_oficial_1281'),
    path('professor/diario-classe-oficial-completo/', views.professor_diario_classe_oficial_1281, name='professor_diario_classe_oficial_1281'),
]


# =====================================================
# EXPORTAÇÃO GERAL — PDF / EXCEL
# =====================================================
urlpatterns += [
    path('gestao/exportar/geral/excel/', views.gestao_exportar_geral_excel, name='gestao_exportar_geral_excel'),
    path('gestao/exportar/geral/pdf/', views.gestao_exportar_geral_pdf, name='gestao_exportar_geral_pdf'),
    path('professor/exportar/geral/excel/', views.professor_exportar_geral_excel, name='professor_exportar_geral_excel'),
    path('professor/exportar/geral/pdf/', views.professor_exportar_geral_pdf, name='professor_exportar_geral_pdf'),
]

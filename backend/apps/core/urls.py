"""Rotas públicas do Diário Escolar Pro.

A versão 2.0 expõe somente os fluxos necessários às áreas de professor e gestão.
"""
from django.urls import path

from . import views_diario, views_gestao, views_academico, views_operacional, views_professor, views_relatorios, views_shared

urlpatterns = [
    # Serviço e acesso institucional
    path("healthz/", views_operacional.healthz, name="healthz"),
    path("media/<path:path>", views_operacional.media_arquivo, name="media_arquivo"),
    path("service-worker.js", views_operacional.service_worker, name="service_worker"),
    path("criar-conta-gestao/", views_shared.criar_conta_gestao_autorizada, name="criar_conta_gestao_autorizada"),
    path("solicitar-codigo-gestao/", views_shared.solicitar_codigo_gestao, name="solicitar_codigo_gestao"),
    path("ativar-acesso-gestao/", views_shared.ativar_acesso_gestao, name="ativar_acesso_gestao"),

    # Professor — início e rotina diária
    path("", views_professor.dashboard_professor, name="dashboard_professor"),
    path("professor/", views_professor.dashboard_professor_home, name="dashboard_professor_home"),
    path("professor/aulas/nova/", views_diario.professor_registrar_aula, name="professor_registrar_aula"),
    path("professor/aulas/nova/<int:horario_id>/", views_diario.professor_registrar_aula, name="professor_registrar_aula_horario"),
    path("professor/agenda/", views_professor.professor_meus_horarios_reais, name="professor_agenda"),
    path("professor/alunos/", views_professor.professor_alunos, name="professor_alunos"),
    path("professor/pendencias/", views_academico.professor_central_pendencias, name="professor_central_pendencias"),
    path("professor/consolidado-mensal/", views_professor.professor_consolidado_mensal, name="professor_consolidado_mensal"),
    path("professor/intervencoes/", views_professor.professor_plano_intervencao, name="professor_plano_intervencao"),
    path("professor/assistente-pedagogico/", views_academico.professor_ia_pedagogica, name="professor_assistente_pedagogico"),
    path("professor/relatorios/", views_relatorios.professor_relatorios, name="professor_relatorios"),
    path("professor/configuracoes/", views_professor.professor_configuracoes, name="professor_configuracoes"),

    # Professor — turmas, diário, notas e frequência
    path("professor/turmas/", views_professor.turmas, name="turmas"),
    path("professor/diario/", views_academico.diario, name="diario"),
    path("professor/diario-oficial/", views_academico.professor_diario_oficial, name="professor_diario_oficial"),
    path("professor/frequencia/", views_academico.frequencia, name="frequencia"),
    path("professor/turmas/<int:turma_id>/", views_professor.turma_detalhe, name="turma_detalhe"),
    path("professor/turmas/<int:turma_id>/frequencia/", views_academico.frequencia_turma, name="frequencia_turma"),
    path("professor/turmas/<int:turma_id>/frequencia-mensal/", views_academico.frequencia_mensal_turma, name="frequencia_mensal_turma"),
    path("professor/turmas/<int:turma_id>/registro-aulas/", views_diario.registro_aulas_mensal_turma, name="registro_aulas_mensal_turma"),
    path("professor/turmas/<int:turma_id>/notas/", views_professor.notas_turma, name="notas_turma"),
    path("professor/turmas/<int:turma_id>/diario-classe/", views_academico.diario_classe_turma, name="diario_classe_turma"),
    path("professor/turmas/<int:turma_id>/diario-completo/", views_academico.diario_oficial_turma_completo, name="diario_oficial_turma_completo"),
    path("professor/turmas/<int:turma_id>/disciplinas/<int:disciplina_id>/frequencia-mensal/", views_academico.frequencia_disciplina_mensal, name="frequencia_disciplina_mensal"),
    path("professor/alunos/<int:aluno_id>/boletim/", views_relatorios.boletim_aluno, name="boletim_aluno"),
    path("professor/turmas/<int:turma_id>/analise/", views_relatorios.boletim_ia, name="boletim_ia"),
    path("professor/registro-aulas-mensal/", views_academico.professor_registro_aula_mensal_oficial, name="professor_registro_aula_mensal_oficial"),

    # Exportações do professor
    path("professor/exportar/excel/", views_relatorios.professor_exportar_geral_excel, name="professor_exportar_geral_excel"),
    path("professor/exportar/pdf/", views_relatorios.professor_exportar_geral_pdf, name="professor_exportar_geral_pdf"),

    # Gestão — visão geral e cadastro estrutural
    path("gestao/", views_operacional.dashboard_gestao, name="dashboard_gestao"),
    path("gestao/escola/", views_gestao.gestao_escola, name="gestao_escola"),
    path("gestao/cadastros/", views_gestao.gestao_cadastros, name="gestao_cadastros"),
    path("gestao/professores/", views_gestao.gestao_professores, name="gestao_professores"),
    path("gestao/alunos/", views_gestao.gestao_alunos, name="gestao_alunos"),
    path("gestao/alunos/historico/", views_gestao.gestao_historico_alunos, name="gestao_historico_alunos"),
    path("gestao/alunos/<int:aluno_id>/", views_academico.gestao_ficha_aluno_oficial, name="gestao_ficha_aluno"),
    path("gestao/alunos/<int:aluno_id>/painel/", views_gestao.gestao_aluno_painel_integrado, name="gestao_aluno_painel_integrado"),
    path("gestao/vinculos/", views_gestao.gestao_vinculos, name="gestao_vinculos"),
    path("gestao/horarios/", views_gestao.gestao_horarios, name="gestao_horarios"),
    path("gestao/carga-horaria/", views_academico.gestao_carga_horaria_professores, name="gestao_carga_horaria"),
    path("gestao/calendario/", views_gestao.gestao_calendario, name="gestao_calendario"),

    # Gestão — diário, acompanhamento e fechamento
    path("gestao/diario/", views_academico.gestao_diario_oficial, name="gestao_diario_oficial"),
    path("gestao/diario/conferencia-frequencia/", views_academico.gestao_conferencia_frequencia_mensal, name="gestao_conferencia_frequencia_mensal"),
    path("gestao/diario/validacao/", views_academico.gestao_diario_validacao_completa, name="gestao_diario_validacao_completa"),
    path("gestao/turmas/<int:turma_id>/dossie/", views_gestao.gestao_dossie_turma, name="gestao_dossie_turma"),
    path("gestao/fechamentos/", views_diario.gestao_fechamentos, name="gestao_fechamentos"),
    path("gestao/fechamento-anual/", views_diario.gestao_fechamento_anual, name="gestao_fechamento_anual"),
    path("gestao/fechamentos/checklist/", views_diario.gestao_checklist_fechamento, name="gestao_checklist_fechamento"),
    path("gestao/recuperacao/", views_gestao.gestao_mapa_recuperacao, name="gestao_mapa_recuperacao"),
    path("gestao/conselho-classe/", views_gestao.gestao_ata_conselho_classe, name="gestao_ata_conselho_classe"),

    # Gestão — relatórios, documentos e auditoria
    path("gestao/relatorios/", views_relatorios.gestao_relatorios, name="gestao_relatorios"),
    path("gestao/documentos/", views_relatorios.gestao_documentos, name="gestao_documentos"),
    path("gestao/documentos/boletim/<int:aluno_id>/", views_relatorios.gestao_documento_boletim_oficial, name="gestao_documento_boletim_oficial"),
    path("gestao/documentos/diario/<int:turma_id>/", views_relatorios.gestao_documento_diario_oficial, name="gestao_documento_diario_oficial"),
    path("gestao/documentos/declaracao/<int:aluno_id>/", views_relatorios.gestao_documento_declaracao_matricula, name="gestao_documento_declaracao_matricula"),
    path("gestao/relatorios/executivo/", views_relatorios.gestao_relatorio_executivo_oficial, name="gestao_relatorio_executivo_oficial"),
    path("gestao/auditoria/", views_academico.gestao_auditoria, name="gestao_auditoria"),
    path("gestao/auditoria/exportar/", views_relatorios.gestao_auditoria_exportacao, name="gestao_auditoria_exportacao"),
    path("gestao/exportar/excel/", views_relatorios.gestao_exportar_geral_excel, name="gestao_exportar_geral_excel"),
    path("gestao/exportar/pdf/", views_relatorios.gestao_exportar_geral_pdf, name="gestao_exportar_geral_pdf"),

    # Gestão — comunicação, documentos pendentes e assistência pedagógica
    path("gestao/notificacoes/", views_gestao.gestao_notificacoes, name="gestao_notificacoes"),
    path("gestao/notificacoes/<int:notificacao_id>/resolver/", views_gestao.gestao_notificacao_resolver, name="gestao_notificacao_resolver"),
    path("gestao/notificacoes/gerar/", views_gestao.gestao_notificacoes_gerar_inteligentes, name="gestao_notificacoes_gerar_inteligentes"),
    path("gestao/assinaturas/", views_gestao.gestao_assinaturas, name="gestao_assinaturas"),
    path("gestao/assistente-pedagogico/", views_academico.gestao_ia_pedagogica, name="gestao_assistente_pedagogico"),
    path("gestao/busca/", views_gestao.gestao_busca_global, name="gestao_busca_global"),
    path("gestao/configuracoes/", views_gestao.gestao_configuracoes, name="gestao_configuracoes"),
]

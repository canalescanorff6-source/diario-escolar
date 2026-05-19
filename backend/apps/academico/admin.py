from django.contrib import admin

from .models import (
    AnoLetivo,
    Disciplina,
    Turma,
    Aluno,
    Nota,
    Frequencia,
    ConteudoAula,
    AlertaIA,
    Escola,
    ProfessorPerfil,
    ProfessorTurmaDisciplina,
    HorarioAula,
    CalendarioEvento,
    FechamentoBimestre,
    ParecerAluno,
    AssinaturaDocumento,
    HistoricoAluno,
    AuditoriaSistema,
    DocumentoGerado,
    NotificacaoGestao,
)


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ("nome", "aldeia", "terra_indigena", "gestor_nome", "municipio", "estado", "ano_letivo_ativo", "ativa")
    list_filter = ("ativa", "estado", "ano_letivo_ativo")
    search_fields = ("nome", "aldeia", "terra_indigena", "gestor_nome", "municipio")
    fieldsets = (
        ("Identificação", {"fields": ("nome", "brasao_logo", "aldeia", "terra_indigena", "municipio", "estado", "ativa")}),
        ("Login institucional", {"fields": ("estado_nome", "secretaria", "gestor_nome", "gestor_cargo", "texto_institucional")}),
        ("Operação escolar", {"fields": ("ano_letivo_ativo",)}),
    )


@admin.register(AnoLetivo)
class AnoLetivoAdmin(admin.ModelAdmin):
    list_display = ("ano", "ativo")
    list_filter = ("ativo",)
    search_fields = ("ano",)


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor")
    search_fields = ("nome",)


@admin.register(ProfessorPerfil)
class ProfessorPerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "escola", "telefone", "ativo")
    list_filter = ("ativo", "escola")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name", "telefone")


@admin.register(ProfessorTurmaDisciplina)
class ProfessorTurmaDisciplinaAdmin(admin.ModelAdmin):
    list_display = ("professor", "turma", "disciplina", "ano_letivo", "ativo")
    list_filter = ("ativo", "ano_letivo", "turma", "disciplina")
    search_fields = ("professor__username", "professor__first_name", "professor__last_name", "turma__nome", "disciplina__nome")


@admin.register(HorarioAula)
class HorarioAulaAdmin(admin.ModelAdmin):
    list_display = ("professor", "turma", "disciplina", "get_dia_semana_display", "ordem", "hora_inicio", "hora_fim", "turno", "ativo")
    list_filter = ("ativo", "turno", "dia_semana", "turma", "disciplina")
    search_fields = ("professor__username", "professor__first_name", "professor__last_name", "turma__nome", "disciplina__nome")


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ano_letivo", "professor", "turno", "ativa")
    list_filter = ("ano_letivo", "turno", "ativa")
    search_fields = ("nome", "professor__username", "professor__first_name", "professor__last_name")


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "turma", "ativo")
    list_filter = ("turma", "ativo")
    search_fields = ("nome", "matricula")


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "turma", "disciplina", "bimestre", "nota1", "nota2", "nota3", "valor")
    list_filter = ("bimestre", "turma", "disciplina")
    search_fields = ("aluno__nome", "turma__nome", "disciplina__nome")


@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "turma", "disciplina", "data", "status", "presente")
    list_filter = ("status", "presente", "data", "turma", "disciplina")
    search_fields = ("aluno__nome", "turma__nome", "disciplina__nome")


@admin.register(ConteudoAula)
class ConteudoAulaAdmin(admin.ModelAdmin):
    list_display = ("turma", "disciplina", "professor", "data")
    list_filter = ("data", "turma", "disciplina")
    search_fields = ("turma__nome", "disciplina__nome", "professor__username")


@admin.register(AlertaIA)
class AlertaIAAdmin(admin.ModelAdmin):
    list_display = ("aluno", "titulo", "nivel", "resolvido", "criado_em")
    list_filter = ("nivel", "resolvido", "criado_em")
    search_fields = ("aluno__nome", "titulo", "descricao")

@admin.register(CalendarioEvento)
class CalendarioEventoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "data_inicio", "data_fim", "ano_letivo", "escola")
    list_filter = ("tipo", "ano_letivo", "escola")
    search_fields = ("titulo", "descricao", "escola__nome")


@admin.register(FechamentoBimestre)
class FechamentoBimestreAdmin(admin.ModelAdmin):
    list_display = ("turma", "disciplina", "bimestre", "status", "fechado_por", "fechado_em")
    list_filter = ("status", "bimestre", "turma", "disciplina")
    search_fields = ("turma__nome", "disciplina__nome", "observacoes")


@admin.register(ParecerAluno)
class ParecerAlunoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "turma", "bimestre", "professor", "criado_em")
    list_filter = ("bimestre", "turma", "professor")
    search_fields = ("aluno__nome", "texto", "encaminhamentos")


@admin.register(AssinaturaDocumento)
class AssinaturaDocumentoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "turma", "aluno", "assinado_por", "cargo", "criado_em")
    list_filter = ("tipo", "turma", "assinado_por")
    search_fields = ("aluno__nome", "turma__nome", "cargo", "observacoes")



@admin.register(HistoricoAluno)
class HistoricoAlunoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "turma", "ano_letivo", "situacao", "data", "registrado_por")
    list_filter = ("situacao", "ano_letivo", "turma", "data")
    search_fields = ("aluno__nome", "descricao", "turma__nome")


@admin.register(AuditoriaSistema)
class AuditoriaSistemaAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "usuario", "modulo", "acao", "objeto")
    list_filter = ("modulo", "acao", "criado_em")
    search_fields = ("usuario__username", "modulo", "acao", "objeto", "descricao")
    readonly_fields = ("criado_em",)


@admin.register(DocumentoGerado)
class DocumentoGeradoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "titulo", "status", "turma", "aluno", "gerado_por", "criado_em")
    list_filter = ("tipo", "status", "turma", "criado_em")
    search_fields = ("titulo", "turma__nome", "aluno__nome", "observacoes")


@admin.register(NotificacaoGestao)
class NotificacaoGestaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "nivel", "turma", "aluno", "destino", "resolvida", "criado_em")
    list_filter = ("nivel", "resolvida", "turma", "criado_em")
    search_fields = ("titulo", "mensagem", "aluno__nome", "turma__nome")


# Etapa 11 — Gestão executiva
try:
    from .models import BackupSistema, IntegracaoEscolar, IndicadorGestao

    @admin.register(BackupSistema)
    class BackupSistemaAdmin(admin.ModelAdmin):
        list_display = ("titulo", "status", "criado_por", "criado_em")
        search_fields = ("titulo", "arquivo")
        list_filter = ("status", "criado_em")

    @admin.register(IntegracaoEscolar)
    class IntegracaoEscolarAdmin(admin.ModelAdmin):
        list_display = ("nome", "tipo", "ativa", "criado_em")
        search_fields = ("nome", "descricao")
        list_filter = ("tipo", "ativa")

    @admin.register(IndicadorGestao)
    class IndicadorGestaoAdmin(admin.ModelAdmin):
        list_display = ("nome", "valor", "referencia", "criado_em")
        search_fields = ("nome", "descricao")
except (admin.sites.AlreadyRegistered, ImportError):
    pass

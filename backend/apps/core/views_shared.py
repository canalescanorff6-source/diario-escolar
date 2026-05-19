from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, Count
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import logout

import json
import os
import secrets
import calendar
from pathlib import Path

from apps.academico.models import (
    Turma,
    Frequencia,
    Disciplina,
    Nota,
    Aluno,
    AnoLetivo,
    ConteudoAula,
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
    BackupSistema,
    IntegracaoEscolar,
    IndicadorGestao,
)

from apps.ia.services import AnaliseInteligenteService
from apps.diario.models import Diario
from apps.core.operacao_861_900 import (
    resumo_aula_861_900,
    resumo_gestao_861_900,
    resumo_professor_861_900,
    auditoria_visual_861_900,
)
from apps.core.operacao_901_960 import (
    finalizacao_901_960,
    fechamento_mensal_901_960,
    inteligencia_pedagogica_901_960,
    relatorios_901_960,
    carga_horaria_901_960,
    auditoria_visual_901_960,
)
from apps.core.operacao_961_1000 import (
    mega_checkup_961_1000,
    prontidao_operacional_961_1000,
    roteiro_final_961_1000,
)
from apps.core.operacao_1001_1080 import (
    mega_checkup_1001_1080,
    plano_conclusao_1001_1080,
)
from apps.core.operacao_1081_1160 import (
    mega_checkup_1081_1160,
    plano_render_1081_1160,
    estimativa_acessos_render_1081_1160,
)

from apps.core.diario_real_utils import (
    auditoria_tecnica_pacote,
    diagnostico_tecnico_diario_real,
    disciplinas_do_professor,
    horarios_do_professor,
    pendencias_diario_real_essenciais,
    resumo_fluxo_diario_real,
    templates_duplicados_exatos,
    turmas_do_professor,
    fluxo_professor_unificado,
    fluxo_gestao_unificado,
    regras_turnos_oficiais,
    painel_duplicidades_visuais,
    auditoria_matriz_turnos_oficial,
    rotas_principais_diario_real,
    pendencias_operacionais_diario_real,
    inventario_templates_legados,
    manifesto_fluxo_unico_diario_real,
    auditoria_views_urls_diario_real,
    checklist_253_258,
    cobertura_requisitos_diario_real_259_264,
    duplicidades_operacionais_259_264,
    checklist_259_264,
)

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from apps.core.licenca_gestao import (
    dias_restantes_gestao,
    dias_teste_gestao,
    garantir_periodo_teste,
    usuario_eh_gestao,
    validar_serial_gestao,
)


# =====================================================
# HELPERS COMPARTILHADOS DA CAMADA DE VIEWS REFATORADA
# Gerado na etapa 1221-1280 para retirar o monolito de views.py.
# =====================================================

def get_disciplina_padrao():
    """Garante uma disciplina para telas de frequência/notas sem alterar o design."""
    disciplina = Disciplina.objects.first()
    if disciplina is None:
        disciplina = Disciplina.objects.create(nome="Geral")
    return disciplina


def registrar_auditoria(usuario, modulo, acao, objeto=None, descricao=None):
    """Registra ação administrativa sem interromper o fluxo se a auditoria falhar."""
    try:
        AuditoriaSistema.objects.create(
            usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
            modulo=modulo,
            acao=acao,
            objeto=objeto,
            descricao=descricao,
        )
    except Exception:
        pass


# =====================================================
# PERMISSÕES SEPARADAS
# =====================================================

def usuario_gestor(user):
    return user.is_authenticated and user.tipo in ["ADMIN", "COORD", "SEC"]


def usuario_professor(user):
    return user.is_authenticated and user.tipo == "PROF"


# =====================================================
# FREQUÊNCIA MENSAL — MODELO DIÁRIO REAL
# =====================================================

def _status_frequencia(freq):
    """Retorna P, F ou FJ usando o campo oficial e mantendo compatibilidade com registros antigos."""
    if not freq:
        return ""
    status = getattr(freq, "status", None)
    if status in {"P", "F", "FJ"}:
        return status
    obs = (freq.observacao or "").strip().lower()
    if "falta justificada" in obs or obs == "fj" or "justificada" in obs:
        return "FJ"
    return "P" if freq.presente else "F"


def _classe_status_frequencia(status):
    return {
        "P": "status-presente",
        "F": "status-falta",
        "FJ": "status-justificada",
    }.get(status, "status-vazio")


def _frequencia_e_falta(status):
    # FJ é falta justificada: aparece separada no diário e também compõe faltas oficiais.
    return status in ["F", "FJ"]


# =====================================================
# ETAPA 12 — IA pedagógica avançada e alertas inteligentes
# Análises aditivas sem alterar o dashboard do professor.
# =====================================================

def montar_analise_pedagogica_avancada(turmas_queryset=None):
    """Monta uma leitura pedagógica executiva usando dados já existentes.
    Mantém a lógica simples e segura: não grava nada no banco e não exige migration.
    """
    turmas_base = turmas_queryset if turmas_queryset is not None else Turma.objects.filter(ativa=True)
    alunos_base = Aluno.objects.filter(ativo=True, turma__in=turmas_base).select_related('turma')

    total_alunos = alunos_base.count()
    total_turmas = turmas_base.count()
    total_notas = Nota.objects.filter(aluno__in=alunos_base).count()
    total_faltas = Frequencia.objects.filter(aluno__in=alunos_base, presente=False).count()
    media_geral = Nota.objects.filter(aluno__in=alunos_base, valor__isnull=False).aggregate(media=Avg('valor')).get('media')

    alunos_risco = []
    for aluno in alunos_base[:300]:
        notas_aluno = Nota.objects.filter(aluno=aluno, valor__isnull=False)
        frequencias_aluno = Frequencia.objects.filter(aluno=aluno)
        media_aluno = notas_aluno.aggregate(media=Avg('valor')).get('media')
        faltas_aluno = frequencias_aluno.filter(presente=False).count()
        total_freq = frequencias_aluno.count()
        percentual_faltas = round((faltas_aluno / total_freq) * 100, 1) if total_freq else 0

        motivos = []
        nivel = 'BAIXO'
        if media_aluno is not None and media_aluno < 6:
            motivos.append('média abaixo de 6,0')
            nivel = 'ALTO'
        elif media_aluno is not None and media_aluno < 7:
            motivos.append('média em atenção')
            nivel = 'MEDIO'

        if percentual_faltas >= 25:
            motivos.append('frequência crítica')
            nivel = 'ALTO'
        elif percentual_faltas >= 15:
            motivos.append('frequência em atenção')
            if nivel == 'BAIXO':
                nivel = 'MEDIO'

        if motivos:
            alunos_risco.append({
                'aluno': aluno,
                'media': media_aluno,
                'faltas': faltas_aluno,
                'percentual_faltas': percentual_faltas,
                'nivel': nivel,
                'motivos': ', '.join(motivos),
            })

    alunos_risco = sorted(
        alunos_risco,
        key=lambda item: (0 if item['nivel'] == 'ALTO' else 1, -(item['percentual_faltas'] or 0))
    )[:20]

    recomendacoes = []
    if total_alunos == 0:
        recomendacoes.append('Cadastre alunos ativos para liberar análises pedagógicas mais completas.')
    if total_notas == 0:
        recomendacoes.append('Lance notas T1/T2/T3 para a IA calcular risco de aprendizagem e média anual.')
    if total_faltas > 0:
        recomendacoes.append('Verificar alunos com faltas recorrentes e registrar intervenção pedagógica no histórico/ficha individual.')
    if alunos_risco:
        recomendacoes.append('Priorizar recuperação paralela, contato com responsáveis e parecer descritivo para alunos em nível alto.')
    if not recomendacoes:
        recomendacoes.append('Base pedagógica estável. Continue acompanhando frequência, avaliações e registros de aula mensalmente.')

    return {
        'total_alunos': total_alunos,
        'total_turmas': total_turmas,
        'total_notas': total_notas,
        'total_faltas': total_faltas,
        'media_geral': media_geral,
        'alunos_risco': alunos_risco,
        'recomendacoes': recomendacoes,
    }


# =====================================================
# ETAPA 13 — DOCUMENTOS OFICIAIS, EXPORTAÇÃO, ALERTAS E AUDITORIA
# Recursos aditivos: não substituem telas anteriores e usam HTML imprimível/PDF.
# =====================================================

def _media_decimal(valores):
    valores_validos = [v for v in valores if v is not None]
    if not valores_validos:
        return None
    return round(sum(valores_validos) / len(valores_validos), 2)


def _percentual_frequencia(aluno=None, turma=None, disciplina=None):
    qs = Frequencia.objects.all()
    if aluno is not None:
        qs = qs.filter(aluno=aluno)
    if turma is not None:
        qs = qs.filter(turma=turma)
    if disciplina is not None:
        qs = qs.filter(disciplina=disciplina)
    total = qs.count()
    if not total:
        return 100
    presencas = qs.filter(presente=True).count()
    return round((presencas / total) * 100, 1)


def _nome_usuario(usuario):
    if not usuario:
        return "-"
    return usuario.get_full_name() or usuario.username


def _protocolo_documento(prefixo, identificador):
    hoje = timezone.now()
    return f"{prefixo}-{hoje:%Y%m%d%H%M}-{identificador}"


def _indicadores_aluno(aluno):
    notas_aluno = Nota.objects.filter(aluno=aluno)
    medias = [float(n.valor) for n in notas_aluno if n.valor is not None]
    media = round(sum(medias) / len(medias), 1) if medias else 0
    registros = Frequencia.objects.filter(aluno=aluno).count()
    presencas = Frequencia.objects.filter(aluno=aluno, presente=True).count()
    faltas = registros - presencas
    frequencia = round((presencas / registros) * 100, 1) if registros else 0
    situacao = "Aprovado" if media >= 6 and (frequencia >= 75 or registros == 0) else "Atenção"
    if media < 5 or (registros and frequencia < 70):
        situacao = "Risco alto"
    return {
        "media": media,
        "registros": registros,
        "presencas": presencas,
        "faltas": faltas,
        "frequencia": frequencia,
        "situacao": situacao,
    }


# =====================================================
# ETAPA 15 — Conselho de classe, recuperação e intervenção pedagógica
# Recursos aditivos: não removem lógica, não alteram dashboard premium existente.
# =====================================================

def _media_anual_aluno(aluno):
    notas = Nota.objects.filter(aluno=aluno, valor__isnull=False).select_related("disciplina")
    valores = [float(n.valor) for n in notas if n.valor is not None]
    return round(sum(valores) / len(valores), 1) if valores else 0


# [Etapas 223-228] Função duplicada removida para preservar definição final: _faltas_aluno


def _diagnostico_recuperacao(aluno):
    media = _media_anual_aluno(aluno)
    faltas = _faltas_aluno(aluno)
    notas_baixas = Nota.objects.filter(aluno=aluno, valor__lt=6).select_related("disciplina")
    disciplinas = sorted({n.disciplina.nome for n in notas_baixas if n.disciplina})
    if media < 5 or faltas >= 20:
        nivel = "CRÍTICO"
    elif media < 6 or faltas >= 10:
        nivel = "ATENÇÃO"
    else:
        nivel = "ACOMPANHAR"
    acoes = []
    if media < 6:
        acoes.append("recuperação paralela com retomada dos descritores essenciais")
    if faltas >= 10:
        acoes.append("busca ativa e contato com responsável")
    if disciplinas:
        acoes.append("plano focal por componente curricular")
    if not acoes:
        acoes.append("monitoramento preventivo")
    return {
        "media": media,
        "faltas": faltas,
        "disciplinas": disciplinas,
        "nivel": nivel,
        "acoes": acoes,
    }


# =====================================================
# ETAPA 16 — Analytics, permissões blindadas e executáveis separados
# =====================================================

def _media_aluno(aluno):
    notas = Nota.objects.filter(aluno=aluno).values_list("valor", flat=True)
    vals = [float(n or 0) for n in notas]
    return round(sum(vals) / len(vals), 1) if vals else 0


def _faltas_aluno(aluno):
    return Frequencia.objects.filter(aluno=aluno, presente=False).count()


# =====================================================
# ETAPA 17 — Busca global, saúde SaaS, comunicação e pendências
# Camada aditiva: não altera dashboards existentes nem remove funcionalidades.
# =====================================================

def _status_badge_por_media(media, faltas=0):
    if media < 6 or faltas >= 20:
        return "Crítico"
    if media < 7 or faltas >= 10:
        return "Atenção"
    return "Estável"


def _ultimos_conteudos_professor(professor, limite=8):
    return ConteudoAula.objects.filter(professor=professor).select_related("turma", "disciplina").order_by("-data")[:limite]


# =====================================================
# ETAPAS 97–108 — Fechamento acelerado sem quebra
# Camada final aditiva: não altera models, migrations, dashboards nem CSS existente.
# =====================================================

def _safe_count(model):
    try:
        return model.objects.count()
    except Exception:
        return 0


def _gestao_final_contexto(titulo, subtitulo, etapa, cards=None, checklist=None, proximos=None):
    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "etapa": etapa,
        "hoje": date.today(),
        "cards": cards or [],
        "checklist": checklist or [],
        "proximos": proximos or [],
        "totais": {
            "alunos": _safe_count(Aluno),
            "turmas": _safe_count(Turma),
            "disciplinas": _safe_count(Disciplina),
            "notas": _safe_count(Nota),
            "frequencias": _safe_count(Frequencia),
            "documentos": _safe_count(DocumentoGerado),
            "auditorias": _safe_count(AuditoriaSistema),
        },
    }


# =====================================================
# CORREÇÃO FUNCIONAL — menus do professor sem links vazios
# =====================================================

def _turmas_do_professor(usuario):
    """Retorna turmas vinculadas ao professor sem quebrar bases antigas."""
    if not getattr(usuario, "is_authenticated", False):
        return Turma.objects.none()

    if usuario_gestor(usuario):
        return Turma.objects.filter(ativa=True).distinct()

    ids_por_vinculo = ProfessorTurmaDisciplina.objects.filter(
        professor=usuario,
        ativo=True,
    ).values_list("turma_id", flat=True)

    return Turma.objects.filter(
        models.Q(professor=usuario) | models.Q(id__in=ids_por_vinculo),
        ativa=True,
    ).distinct()


# =====================================================
# DIÁRIO OFICIAL COMPLETO — consolidação real sem remover lógica existente
# =====================================================

def _turmas_visiveis_para_usuario(usuario):
    """Retorna turmas permitidas para professor ou gestão, preservando separação de painéis."""
    qs = Turma.objects.select_related("ano_letivo", "professor").prefetch_related("alunos")
    if usuario_gestor(usuario):
        return qs.all().order_by("turno", "nome")
    if usuario_professor(usuario):
        turmas_vinculadas = ProfessorTurmaDisciplina.objects.filter(
            professor=usuario,
            ativo=True,
        ).values_list("turma_id", flat=True)
        return qs.filter(
            models.Q(professor=usuario) | models.Q(id__in=turmas_vinculadas)
        ).distinct().order_by("turno", "nome")
    return qs.none()


def _disciplinas_da_turma(turma, professor=None):
    vinculos = ProfessorTurmaDisciplina.objects.filter(
        turma=turma,
        ativo=True,
    ).select_related("disciplina", "professor")
    if professor is not None and getattr(professor, "tipo", None) == "PROF":
        vinculos = vinculos.filter(professor=professor)
    ids = set(vinculos.values_list("disciplina_id", flat=True))
    if not ids:
        ids.update(Frequencia.objects.filter(turma=turma).values_list("disciplina_id", flat=True))
        ids.update(ConteudoAula.objects.filter(turma=turma).values_list("disciplina_id", flat=True))
        ids.update(Nota.objects.filter(turma=turma).values_list("disciplina_id", flat=True))
    ids.discard(None)
    return Disciplina.objects.filter(id__in=ids).distinct().order_by("nome")


def _resumo_diario_turma(turma, professor=None):
    disciplinas = _disciplinas_da_turma(turma, professor)
    horarios = HorarioAula.objects.filter(turma=turma, ativo=True).select_related("disciplina", "professor")
    if professor is not None and getattr(professor, "tipo", None) == "PROF":
        horarios = horarios.filter(professor=professor)
    frequencias = Frequencia.objects.filter(turma=turma)
    if disciplinas.exists():
        frequencias = frequencias.filter(disciplina__in=disciplinas)
    total_freq = frequencias.count()
    total_faltas = frequencias.filter(presente=False).count()
    total_presencas = total_freq - total_faltas
    percentual = round((total_presencas / total_freq) * 100, 1) if total_freq else 100
    return {
        "turma": turma,
        "disciplinas": disciplinas,
        "horarios": horarios.order_by("dia_semana", "ordem", "hora_inicio"),
        "total_alunos": turma.alunos.filter(ativo=True).count(),
        "total_disciplinas": disciplinas.count(),
        "total_horarios": horarios.count(),
        "total_faltas": total_faltas,
        "frequencia_percentual": percentual,
        "registros_aulas": ConteudoAula.objects.filter(turma=turma).count() + Diario.objects.filter(turma=turma).count(),
    }


def _usuario_pode_ver_turma(usuario, turma):
    if usuario_gestor(usuario):
        return True
    if usuario_professor(usuario):
        return turma.professor_id == usuario.id or ProfessorTurmaDisciplina.objects.filter(
            professor=usuario,
            turma=turma,
            ativo=True,
        ).exists()
    return False


def _montar_diario_oficial_turma(turma, usuario, request):
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    professor_filtro = usuario if usuario_professor(usuario) else None
    disciplinas = _disciplinas_da_turma(turma, professor_filtro)
    if not disciplinas.exists():
        disciplinas = Disciplina.objects.all().order_by("nome")
    ano, mes, mes_param, primeiro_dia, ultimo_dia, meses = _periodo_mes_por_parametro(request, turma)

    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related(
        "professor", "disciplina", "ano_letivo"
    )
    if professor_filtro:
        vinculos = vinculos.filter(professor=professor_filtro)

    horarios = HorarioAula.objects.filter(turma=turma, ativo=True).select_related("professor", "disciplina").order_by(
        "dia_semana", "ordem", "hora_inicio"
    )
    if professor_filtro:
        horarios = horarios.filter(professor=professor_filtro)

    grade = []
    for dia_valor, dia_label in HorarioAula.DIAS_SEMANA:
        grade.append({"dia": dia_label, "horarios": horarios.filter(dia_semana=dia_valor)})

    alunos = turma.alunos.filter(ativo=True).order_by("nome")
    disciplinas_dados = []
    for disciplina in disciplinas:
        frequencias = Frequencia.objects.filter(
            turma=turma,
            disciplina=disciplina,
            data__gte=primeiro_dia,
            data__lte=ultimo_dia,
        ).select_related("aluno").order_by("data")
        datas = list(frequencias.values_list("data", flat=True).distinct().order_by("data"))
        freq_map = {(f.aluno_id, f.data): f for f in frequencias}
        linhas = []
        faltas_disciplina = 0
        presencas_disciplina = 0
        for numero, aluno in enumerate(alunos, start=1):
            celulas = []
            faltas_aluno = 0
            for data_ref in datas:
                freq = freq_map.get((aluno.id, data_ref))
                if not freq:
                    status = ""
                    classe = "vazio"
                elif freq.presente and (freq.observacao or "").lower().startswith("falta justificada"):
                    status = "FJ"
                    classe = "justificada"
                    presencas_disciplina += 1
                elif freq.presente:
                    status = "P"
                    classe = "presente"
                    presencas_disciplina += 1
                else:
                    status = "F"
                    classe = "falta"
                    faltas_aluno += 1
                    faltas_disciplina += 1
                celulas.append({"data": data_ref, "status": status, "classe": classe})
            linhas.append({"numero": numero, "aluno": aluno, "celulas": celulas, "faltas": faltas_aluno})
        registros_conteudo = ConteudoAula.objects.filter(
            turma=turma,
            disciplina=disciplina,
            data__gte=primeiro_dia,
            data__lte=ultimo_dia,
        ).select_related("professor").order_by("data")
        diarios = Diario.objects.filter(
            turma=turma,
            disciplina=disciplina.nome,
            data__gte=primeiro_dia,
            data__lte=ultimo_dia,
        ).select_related("professor").order_by("data")
        total = frequencias.count()
        percentual = round((presencas_disciplina / total) * 100, 1) if total else 100
        disciplinas_dados.append({
            "disciplina": disciplina,
            "datas": datas,
            "linhas": linhas,
            "total_faltas": faltas_disciplina,
            "total_registros": total,
            "frequencia_percentual": percentual,
            "conteudos": registros_conteudo,
            "diarios": diarios,
        })

    professores = []
    for vinculo in vinculos:
        if vinculo.professor_id not in [p["professor"].id for p in professores]:
            professores.append({
                "professor": vinculo.professor,
                "disciplinas": vinculos.filter(professor=vinculo.professor).select_related("disciplina"),
            })

    return {
        "escola": escola,
        "turma": turma,
        "ano_letivo": turma.ano_letivo,
        "vinculos": vinculos,
        "professores": professores,
        "disciplinas": disciplinas,
        "disciplinas_dados": disciplinas_dados,
        "horarios": horarios,
        "grade": grade,
        "alunos": alunos,
        "ano": ano,
        "mes": mes,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "meses": meses,
        "hoje": date.today(),
        "is_professor": usuario_professor(usuario),
    }


# =====================================================
# ETAPAS 67–78 — Diário real avançado, gestão pedagógica e secretaria
# Bloco aditivo: não altera os fluxos antigos; cria centrais consolidadas e seguras.
# =====================================================

def _serie_turno_padrao():
    return {
        "manhã": ["1º ano", "2º ano", "3º ano", "4º ano", "5º ano"],
        "tarde": ["6º ano", "7º ano", "8º ano", "9º ano", "1ª série", "2ª série", "3ª série"],
        "noite": ["EJA I", "EJA II", "EJA III", "EJA IV", "EJA V"],
    }


def _turmas_por_turno_contexto():
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    grupos = []
    mapa = _serie_turno_padrao()
    for turno_nome, series in mapa.items():
        qs = turmas.filter(turno__icontains=turno_nome)
        if not qs.exists() and turno_nome == "manhã":
            qs = turmas.filter(turno__icontains="matutino")
        if not qs.exists() and turno_nome == "tarde":
            qs = turmas.filter(turno__icontains="vespertino")
        if not qs.exists() and turno_nome == "noite":
            qs = turmas.filter(turno__icontains="noturno")
        grupos.append({
            "turno": turno_nome.title(),
            "series_referencia": series,
            "turmas": qs.order_by("nome"),
            "total_turmas": qs.count(),
            "total_alunos": sum(t.alunos.filter(ativo=True).count() for t in qs),
        })
    return grupos


# =====================================================
# DIÁRIO REAL — etapas premium de consolidação pedagógica
# Mantém tudo existente e adiciona validações oficiais para o fluxo real.
# =====================================================

def _status_ok(valor):
    return "ok" if valor else "pendente"


def _linha_validacao_diario(turma):
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related("professor", "disciplina")
    horarios = HorarioAula.objects.filter(turma=turma, ativo=True).select_related("professor", "disciplina")
    alunos = turma.alunos.filter(ativo=True)
    disciplinas = Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct()
    frequencias = Frequencia.objects.filter(turma=turma)
    aulas = ConteudoAula.objects.filter(turma=turma).count() + Diario.objects.filter(turma=turma).count()
    professores = get_user_model().objects.filter(id__in=vinculos.values_list("professor_id", flat=True)).distinct()
    pendencias = []
    if not escola:
        pendencias.append("cadastro da escola")
    if not turma.ano_letivo_id:
        pendencias.append("ano letivo")
    if not turma.turno:
        pendencias.append("turno")
    if not vinculos.exists():
        pendencias.append("vínculo professor/turma/disciplina")
    if not horarios.exists():
        pendencias.append("grade semanal")
    if not alunos.exists():
        pendencias.append("alunos ativos")
    if not frequencias.exists():
        pendencias.append("frequência mensal")
    if aulas == 0:
        pendencias.append("registro mensal de aulas")
    return {
        "turma": turma,
        "escola": escola,
        "professores": professores,
        "disciplinas": disciplinas,
        "vinculos": vinculos,
        "horarios": horarios,
        "total_alunos": alunos.count(),
        "total_frequencias": frequencias.count(),
        "total_aulas": aulas,
        "pendencias": pendencias,
        "percentual": max(0, round(100 - (len(pendencias) * 12.5), 1)),
        "status": "Completo" if not pendencias else "Pendente",
    }


# =====================================================
# ETAPAS 109–114 — Diário real operacional por aluno
# Continuidade segura: não remove telas anteriores; adiciona fluxo oficial de conferência e lançamento.
# =====================================================

def _status_frequencia_oficial(registro):
    """Converte Frequencia para P/F/FJ usando status oficial e fallback legado."""
    if not registro:
        return ""
    status = getattr(registro, "status", None)
    if status in {"P", "F", "FJ"}:
        return status
    obs = (registro.observacao or "").lower()
    if "justificada" in obs or "fj" in obs:
        return "FJ"
    return "P" if registro.presente else "F"


def _contagens_oficiais_frequencia(qs):
    total = qs.count()
    try:
        fj = qs.filter(status="FJ").count()
        faltas = qs.filter(status="F").count()
        presencas = qs.filter(status="P").count()
    except Exception:
        criterio_fj = models.Q(observacao__icontains="justificada") | models.Q(observacao__icontains="fj")
        fj = qs.filter(criterio_fj).count()
        faltas = qs.filter(presente=False).exclude(criterio_fj).count()
        presencas = max(0, total - faltas - fj)
    return {"total": total, "presencas": presencas, "faltas": faltas, "fj": fj}


def _diario_aluno_contexto(aluno, usuario=None, somente_professor=False):
    turma = aluno.turma
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related("professor", "disciplina", "ano_letivo")
    if somente_professor and usuario:
        vinculos = vinculos.filter(professor=usuario)
    disciplinas = Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct().order_by("nome")
    if not disciplinas.exists():
        disciplinas = _disciplinas_da_turma(turma)
    hoje_ref = date.today()
    linhas = []
    for disciplina in disciplinas:
        freq = Frequencia.objects.filter(aluno=aluno, turma=turma, disciplina=disciplina).order_by("-data")
        contagens = _contagens_oficiais_frequencia(freq)
        aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina).order_by("-data")[:10]
        horarios = HorarioAula.objects.filter(turma=turma, disciplina=disciplina, ativo=True).select_related("professor").order_by("dia_semana", "ordem")
        linhas.append({
            "disciplina": disciplina,
            "frequencias": freq[:12],
            "contagens": contagens,
            "aulas": aulas,
            "horarios": horarios,
            "status_hoje": _status_frequencia_oficial(freq.filter(data=hoje_ref).first()),
        })
    return {
        "escola": escola,
        "aluno": aluno,
        "turma": turma,
        "vinculos": vinculos,
        "linhas": linhas,
        "hoje": hoje_ref,
    }


# =====================================================
# ETAPAS 115–120 — Checkup geral e continuidade oficial
# Continuidade segura após 109–114: auditoria visual/operacional sem quebrar telas anteriores.
# =====================================================

def _nome_turno_real(valor):
    bruto = (valor or "").upper()
    if bruto in ["MATUTINO", "MANHA", "MANHÃ"]:
        return "Manhã"
    if bruto in ["VESPERTINO", "TARDE"]:
        return "Tarde"
    if bruto in ["NOTURNO", "NOITE", "EJA"]:
        return "Noite/EJA"
    return valor or "Turno pendente"


def _meta_turno_real(turma):
    nome = (getattr(turma, "nome", "") or "").lower()
    turno = (getattr(turma, "turno", "") or "").upper()
    if turno in ["MATUTINO", "MANHA", "MANHÃ"] or "1" in nome or "2" in nome or "3" in nome or "4" in nome or "5" in nome:
        return "Manhã: 1º ao 5º ano"
    if turno in ["VESPERTINO", "TARDE"] or any(x in nome for x in ["6", "7", "8", "9", "1ª", "2ª", "3ª", "medio", "médio"]):
        return "Tarde: 6º ao 9º + Ensino Médio"
    if turno in ["NOTURNO", "NOITE", "EJA"] or "eja" in nome:
        return "Noite: turmas EJA"
    return "Classificação pendente"


def _checkup_diario_real():
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").order_by("turno", "nome")
    professores = get_user_model().objects.filter(tipo="PROF").order_by("first_name", "username")
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).select_related("professor", "turma", "disciplina")
    horarios = HorarioAula.objects.filter(ativo=True).select_related("professor", "turma", "disciplina")
    frequencias = Frequencia.objects.select_related("aluno", "turma", "disciplina")
    aulas = ConteudoAula.objects.select_related("turma", "disciplina")
    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    pendencias = []
    if not escola:
        pendencias.append("Cadastrar escola ativa para o cabeçalho oficial do diário.")
    elif not escola.ano_letivo_ativo:
        pendencias.append("Definir ano letivo ativo na escola.")
    if not professores.exists():
        pendencias.append("Cadastrar professores com tipo PROF para vínculo automático da gestão.")
    if not vinculos.exists():
        pendencias.append("Vincular professor + turma + disciplina na gestão/admin.")
    if not horarios.exists():
        pendencias.append("Cadastrar horários semanais por professor, turma e disciplina.")
    if not alunos.exists():
        pendencias.append("Cadastrar alunos ativos nas turmas.")
    linhas_turmas = []
    for turma in turmas:
        vinculos_turma = vinculos.filter(turma=turma)
        horarios_turma = horarios.filter(turma=turma)
        alunos_turma = alunos.filter(turma=turma)
        freq_turma = frequencias.filter(turma=turma)
        aulas_turma = aulas.filter(turma=turma)
        faltas = freq_turma.filter(presente=False).exclude(observacao__icontains="justificada").count()
        fj = freq_turma.filter(observacao__icontains="justificada").count()
        linhas_turmas.append({
            "turma": turma,
            "turno_real": _nome_turno_real(getattr(turma, "turno", "")),
            "meta_turno": _meta_turno_real(turma),
            "alunos": alunos_turma.count(),
            "vinculos": vinculos_turma.count(),
            "professores": get_user_model().objects.filter(id__in=vinculos_turma.values_list("professor_id", flat=True)).distinct(),
            "disciplinas": Disciplina.objects.filter(id__in=vinculos_turma.values_list("disciplina_id", flat=True)).distinct(),
            "horarios": horarios_turma.count(),
            "frequencias": freq_turma.count(),
            "faltas": faltas,
            "fj": fj,
            "aulas": aulas_turma.count(),
            "ok": alunos_turma.exists() and vinculos_turma.exists() and horarios_turma.exists(),
        })
    resumo = {
        "escola": escola,
        "turmas": turmas.count(),
        "professores": professores.count(),
        "alunos": alunos.count(),
        "vinculos": vinculos.count(),
        "horarios": horarios.count(),
        "frequencias": frequencias.count(),
        "aulas": aulas.count(),
        "pendencias": pendencias,
    }
    return resumo, linhas_turmas


# =====================================================
# ETAPAS 121–126 — Consolidação oficial mensal/anual do Diário Escolar
# Aditivo seguro: não remove lógica existente; cria conferência, impressão e continuidade operacional.
# =====================================================

def _ano_letivo_ativo_oficial():
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    ano_letivo = escola.ano_letivo_ativo if escola and escola.ano_letivo_ativo else AnoLetivo.objects.filter(ativo=True).first()
    return escola, ano_letivo


def _nome_professor(usuario):
    if not usuario:
        return "Sem professor"
    return usuario.get_full_name() or usuario.username


def _turma_turno_normalizado(turma):
    turno = (turma.turno or "").strip().lower()
    nome = turma.nome.lower()
    if "mat" in turno or "man" in turno:
        return "MANHÃ"
    if "ves" in turno or "tar" in turno:
        return "TARDE"
    if "not" in turno or "noi" in turno or "eja" in turno or "eja" in nome:
        return "NOITE/EJA"
    return turma.turno or "Não informado"


def _disciplinas_vinculadas_por_turma_professor(turma, professor=None):
    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related("disciplina", "professor")
    if professor is not None:
        vinculos = vinculos.filter(professor=professor)
    disciplinas = Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct().order_by("nome")
    if not disciplinas.exists():
        disciplinas = _disciplinas_da_turma(turma, professor)
    return disciplinas, vinculos


def _linha_consolidado_mensal(turma, disciplina, inicio, fim, professor=None):
    freq = Frequencia.objects.filter(turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
    if professor is not None:
        alunos_ids = turma.alunos.filter(ativo=True).values_list("id", flat=True)
        freq = freq.filter(aluno_id__in=alunos_ids)
    contagens = _contagens_oficiais_frequencia(freq)
    aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
    if professor is not None:
        aulas = aulas.filter(professor=professor)
    horarios = HorarioAula.objects.filter(turma=turma, disciplina=disciplina, ativo=True)
    if professor is not None:
        horarios = horarios.filter(professor=professor)
    return {
        "disciplina": disciplina,
        "frequencia": contagens,
        "aulas": aulas.order_by("-data")[:12],
        "total_aulas": aulas.count(),
        "horarios": horarios.order_by("dia_semana", "ordem", "hora_inicio"),
        "sem_aula": aulas.count() == 0,
        "sem_frequencia": contagens["total"] == 0,
    }


# =====================================================
# ETAPAS 127–132 — Auditoria oficial, pendências e impressão do Diário Escolar
# =====================================================

def _resumo_integridade_diario_turma(turma, inicio=None, fim=None):
    """Monta uma leitura segura da turma sem alterar cadastros nem registros existentes."""
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    disciplinas, vinculos = _disciplinas_vinculadas_por_turma_professor(turma)
    alunos = turma.alunos.filter(ativo=True).order_by("nome")
    blocos = []
    total_pendencias = 0
    for disciplina in disciplinas:
        vinculos_disc = vinculos.filter(disciplina=disciplina)
        professores = []
        for vinculo in vinculos_disc:
            professores.append(vinculo.professor)
        horarios = HorarioAula.objects.filter(turma=turma, disciplina=disciplina, ativo=True).select_related("professor").order_by("dia_semana", "ordem", "hora_inicio")
        freq = Frequencia.objects.filter(turma=turma, disciplina=disciplina)
        aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina).select_related("professor").order_by("-data")
        if inicio and fim:
            freq = freq.filter(data__gte=inicio, data__lte=fim)
            aulas = aulas.filter(data__gte=inicio, data__lte=fim)
        contagens = _contagens_oficiais_frequencia(freq)
        pendencias = []
        if not professores:
            pendencias.append("Sem professor vinculado pela gestão")
        if not horarios.exists():
            pendencias.append("Sem horário semanal oficial")
        if alunos.exists() and contagens["total"] == 0:
            pendencias.append("Sem frequência lançada no período")
        if aulas.count() == 0:
            pendencias.append("Sem registro mensal de aula")
        total_pendencias += len(pendencias)
        blocos.append({
            "disciplina": disciplina,
            "professores": professores,
            "horarios": horarios,
            "frequencia": contagens,
            "aulas": aulas[:10],
            "total_aulas": aulas.count(),
            "pendencias": pendencias,
            "ok": not pendencias,
        })
    if not disciplinas:
        total_pendencias += 1
    return {
        "escola": escola,
        "ano_letivo": ano_letivo or turma.ano_letivo,
        "turma": turma,
        "turno_oficial": _turma_turno_normalizado(turma),
        "alunos": alunos,
        "disciplinas": blocos,
        "total_alunos": alunos.count(),
        "total_pendencias": total_pendencias,
        "sem_disciplinas": not bool(disciplinas),
    }


def _linhas_pendencias_diario(inicio=None, fim=None):
    linhas = []
    for turma in Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").order_by("turno", "nome"):
        resumo = _resumo_integridade_diario_turma(turma, inicio, fim)
        if resumo["total_pendencias"] or resumo["sem_disciplinas"]:
            linhas.append(resumo)
    return linhas


# =====================================================
# ETAPAS 133–138 — Checkup geral, conferência anual e continuidade segura
# Aditivo seguro: preserva Diário Escolar, professor automático, P/F/FJ, horários e ficha do aluno.
# =====================================================

def _resumo_checkup_diario_real_atual():
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    turmas = Turma.objects.filter(ativa=True)
    if ano_letivo:
        turmas = turmas.filter(ano_letivo=ano_letivo)
    professores = get_user_model().objects.filter(tipo="PROF")
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios = HorarioAula.objects.filter(ativo=True)
    alunos = Aluno.objects.filter(ativo=True)
    freq = Frequencia.objects.all()
    aulas = ConteudoAula.objects.all()
    return {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "turmas": turmas.count(),
        "professores": professores.count(),
        "vinculos": vinculos.count(),
        "horarios": horarios.count(),
        "alunos": alunos.count(),
        "frequencias": freq.count(),
        "aulas": aulas.count(),
        "sem_escola": escola is None,
        "sem_ano": ano_letivo is None,
        "turmas_sem_turno": turmas.filter(models.Q(turno__isnull=True) | models.Q(turno__exact="")).count(),
        "turmas_sem_professor": turmas.filter(professor__isnull=True).count(),
        "vinculos_sem_horario": vinculos.exclude(
            turma_id__in=horarios.values_list("turma_id", flat=True),
            disciplina_id__in=horarios.values_list("disciplina_id", flat=True),
        ).count(),
    }


def _linhas_conferencia_anual_aluno(aluno, ano=None):
    turma = aluno.turma
    disciplinas, _ = _disciplinas_vinculadas_por_turma_professor(turma)
    linhas = []
    for disciplina in disciplinas:
        freq = Frequencia.objects.filter(aluno=aluno, turma=turma, disciplina=disciplina)
        aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina)
        if ano:
            freq = freq.filter(data__year=ano)
            aulas = aulas.filter(data__year=ano)
        linhas.append({
            "disciplina": disciplina,
            "frequencia": _contagens_oficiais_frequencia(freq),
            "aulas": aulas.count(),
            "ultimos_registros": freq.order_by("-data")[:8],
        })
    return linhas


# =====================================================
# ETAPAS 139–144 — Prontidão, fechamento mensal e extrato oficial
# =====================================================

def _resumo_turma_disciplina_mes(turma, disciplina, inicio, fim, professor=None):
    """Resumo seguro para auditoria: não cria dados, apenas consolida o que já existe."""
    freq = Frequencia.objects.filter(turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
    aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
    horarios = HorarioAula.objects.filter(turma=turma, disciplina=disciplina, ativo=True)
    if professor is not None:
        aulas = aulas.filter(professor=professor)
        horarios = horarios.filter(professor=professor)
    contagens = _contagens_oficiais_frequencia(freq)
    total_alunos = turma.alunos.filter(ativo=True).count()
    dias_lancados = freq.values("data").distinct().count()
    pendencias = []
    if total_alunos == 0:
        pendencias.append("Turma sem alunos ativos")
    if not horarios.exists():
        pendencias.append("Sem horário semanal cadastrado")
    if aulas.count() == 0:
        pendencias.append("Sem registro mensal de aula")
    if contagens["total"] == 0:
        pendencias.append("Sem frequência lançada no mês")
    return {
        "turma": turma,
        "disciplina": disciplina,
        "frequencia": contagens,
        "aulas_count": aulas.count(),
        "horarios_count": horarios.count(),
        "total_alunos": total_alunos,
        "dias_lancados": dias_lancados,
        "pendencias": pendencias,
        "ok": not pendencias,
        "aulas": aulas.order_by("data"),
        "horarios": horarios.order_by("dia_semana", "ordem", "hora_inicio"),
    }


def _resumo_prontidao_diario_real(ano_letivo=None, inicio=None, fim=None):
    if inicio is None or fim is None:
        hoje = date.today()
        inicio = date(hoje.year, hoje.month, 1)
        fim = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    if ano_letivo:
        turmas = turmas.filter(ano_letivo=ano_letivo)
    linhas = []
    totais = {"turmas": 0, "disciplinas": 0, "ok": 0, "pendentes": 0, "alunos": 0, "aulas": 0, "frequencias": 0}
    for turma in turmas.order_by("turno", "nome"):
        disciplinas, vinculos = _disciplinas_vinculadas_por_turma_professor(turma)
        blocos = []
        for disciplina in disciplinas:
            bloco = _resumo_turma_disciplina_mes(turma, disciplina, inicio, fim)
            blocos.append(bloco)
            totais["disciplinas"] += 1
            totais["aulas"] += bloco["aulas_count"]
            totais["frequencias"] += bloco["frequencia"]["total"]
            if bloco["ok"]:
                totais["ok"] += 1
            else:
                totais["pendentes"] += 1
        if not blocos:
            totais["pendentes"] += 1
        totais["turmas"] += 1
        totais["alunos"] += turma.alunos.filter(ativo=True).count()
        linhas.append({
            "turma": turma,
            "turno_oficial": _turma_turno_normalizado(turma),
            "professor_regente": turma.professor,
            "vinculos": vinculos,
            "blocos": blocos,
            "sem_vinculos": not vinculos.exists(),
            "ok": bool(blocos) and all(b["ok"] for b in blocos),
        })
    return linhas, totais


# =====================================================
# ETAPAS 145–150 — Consolidação oficial, entrega e auditoria final do Diário Escolar
# =====================================================

def _periodos_mensais_ano(ano=None):
    ano = ano or date.today().year
    return [
        {
            "numero": mes,
            "nome": calendar.month_name[mes].capitalize(),
            "inicio": date(ano, mes, 1),
            "fim": date(ano, mes, calendar.monthrange(ano, mes)[1]),
            "param": f"{ano}-{mes:02d}",
        }
        for mes in range(1, 13)
    ]


def _nome_usuario_oficial(user):
    if not user:
        return "Não informado"
    return user.get_full_name() or getattr(user, "username", "Não informado")


def _turnos_esperados_diario_real():
    return [
        {"turno": "MATUTINO", "nome": "Manhã", "esperado": 5, "descricao": "1º ao 5º ano"},
        {"turno": "VESPERTINO", "nome": "Tarde", "esperado": 8, "descricao": "6º ao 9º + 1ª, 2ª e 3ª série"},
        {"turno": "NOTURNO", "nome": "Noite", "esperado": 5, "descricao": "EJA"},
    ]


def _rotas_diario_real_status():
    return [
        {"grupo": "Gestão", "nome": "Diário Oficial", "url_name": "gestao_diario_oficial", "descricao": "Central oficial com escola, ano letivo, turmas, turnos e vínculos."},
        {"grupo": "Gestão", "nome": "Prontidão Mensal", "url_name": "gestao_prontidao_diario_real_139", "descricao": "Confere frequência, aulas, horários e pendências por mês."},
        {"grupo": "Gestão", "nome": "Fechamento Oficial", "url_name": "gestao_fechamento_oficial_diario_145", "descricao": "Fechamento mensal por turma, professor e disciplina."},
        {"grupo": "Gestão", "nome": "Matriz por Turno", "url_name": "gestao_matriz_turnos_conferencia_145", "descricao": "Confere manhã, tarde e noite conforme a regra da escola."},
        {"grupo": "Gestão", "nome": "Rotas do Diário", "url_name": "gestao_rotas_diario_real_145", "descricao": "Mapa dos botões e caminhos oficiais do módulo."},
        {"grupo": "Professor", "nome": "Meu Diário de Classe", "url_name": "professor_diario_oficial", "descricao": "Turmas e disciplinas vinculadas automaticamente pela gestão."},
        {"grupo": "Professor", "nome": "Prontidão do Diário", "url_name": "professor_prontidao_diario_139", "descricao": "O que falta lançar por disciplina, turma e mês."},
        {"grupo": "Professor", "nome": "Entrega Mensal", "url_name": "professor_entrega_mensal_diario_145", "descricao": "Conferência final do professor antes da entrega mensal."},
    ]


# =====================================================
# ETAPAS 151–156 — Homologação final do Diário Escolar e trilha oficial
# Continuação segura: só adiciona painéis/rotas, sem alterar modelos ou remover lógica existente.
# =====================================================

def _diario_real_saude_operacional(inicio=None, fim=None):
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    if inicio is None or fim is None:
        hoje = date.today()
        inicio = date(hoje.year, hoje.month, 1)
        fim = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
    turmas = Turma.objects.filter(ativa=True).select_related('ano_letivo', 'professor')
    if ano_letivo:
        turmas = turmas.filter(ano_letivo=ano_letivo)
    professores = get_user_model().objects.filter(tipo='PROF')
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).select_related('professor', 'turma', 'disciplina')
    horarios = HorarioAula.objects.filter(ativo=True)
    frequencias = Frequencia.objects.filter(data__gte=inicio, data__lte=fim)
    aulas = ConteudoAula.objects.filter(data__gte=inicio, data__lte=fim)
    turnos = []
    for regra in _turnos_esperados_diario_real():
        turmas_turno = [t for t in turmas if _turma_turno_normalizado(t) == regra['turno']]
        turnos.append({
            'regra': regra,
            'total': len(turmas_turno),
            'ok': len(turmas_turno) == regra['esperado'],
            'turmas': turmas_turno,
        })
    pendencias = []
    if not escola:
        pendencias.append('Identificação da escola pendente')
    if not ano_letivo:
        pendencias.append('Ano letivo ativo pendente')
    if not turmas.exists():
        pendencias.append('Nenhuma turma ativa cadastrada')
    if not professores.exists():
        pendencias.append('Nenhum professor cadastrado pela gestão')
    if not vinculos.exists():
        pendencias.append('Nenhum vínculo professor/turma/disciplina ativo')
    if not horarios.exists():
        pendencias.append('Nenhum horário semanal ativo cadastrado')
    if not frequencias.exists():
        pendencias.append('Nenhuma frequência lançada no mês')
    if not aulas.exists():
        pendencias.append('Nenhum registro mensal de aula lançado')
    return {
        'escola': escola,
        'ano_letivo': ano_letivo,
        'turmas': turmas,
        'professores': professores,
        'vinculos': vinculos,
        'horarios': horarios,
        'frequencias': frequencias,
        'aulas': aulas,
        'turnos': turnos,
        'pendencias': pendencias,
        'ok': not pendencias,
        'inicio': inicio,
        'fim': fim,
    }


def _dias_com_lancamento_por_vinculo(vinculo, inicio, fim, professor=None):
    freq = Frequencia.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, data__gte=inicio, data__lte=fim)
    aulas = ConteudoAula.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, data__gte=inicio, data__lte=fim)
    if professor:
        aulas = aulas.filter(professor=professor)
    datas_freq = set(freq.values_list('data', flat=True))
    datas_aulas = set(aulas.values_list('data', flat=True))
    datas = sorted(datas_freq | datas_aulas)
    return [{
        'data': data_item,
        'tem_frequencia': data_item in datas_freq,
        'tem_aula': data_item in datas_aulas,
        'frequencia': _contagens_oficiais_frequencia(freq.filter(data=data_item)),
        'aulas': aulas.filter(data=data_item),
    } for data_item in datas]


# =====================================================
# ETAPAS 157–162 — Integridade final, agenda semanal e checklist oficial
# Continuação segura: consolida dados existentes sem criar models nem alterar banco.
# =====================================================

def _nome_professor_oficial(usuario):
    if not usuario:
        return "Professor não vinculado"
    return usuario.get_full_name() or usuario.username


def _resumo_turnos_diario_real(inicio, fim):
    turnos = ["MATUTINO", "VESPERTINO", "NOTURNO", "SEM TURNO"]
    linhas = []
    for turno in turnos:
        filtro_turno = {} if turno == "SEM TURNO" else {"turno__icontains": turno[:4]}
        if turno == "SEM TURNO":
            turmas = Turma.objects.filter(ativa=True).filter(models.Q(turno__isnull=True) | models.Q(turno=""))
        else:
            turmas = Turma.objects.filter(ativa=True, **filtro_turno)
        vinculos = ProfessorTurmaDisciplina.objects.filter(turma__in=turmas, ativo=True)
        horarios = HorarioAula.objects.filter(turma__in=turmas, ativo=True)
        frequencias = Frequencia.objects.filter(turma__in=turmas, data__gte=inicio, data__lte=fim)
        aulas = ConteudoAula.objects.filter(turma__in=turmas, data__gte=inicio, data__lte=fim)
        linhas.append({
            "turno": turno,
            "turmas": turmas.order_by("nome"),
            "turmas_count": turmas.count(),
            "vinculos_count": vinculos.count(),
            "horarios_count": horarios.count(),
            "frequencias": _contagens_oficiais_frequencia(frequencias),
            "aulas_count": aulas.count(),
            "ok": turmas.exists() and vinculos.exists() and horarios.exists(),
        })
    return linhas


# =====================================================
# ETAPAS 163–168 — Conferência final, livro oficial e prontidão de lançamento
# Continuação segura: usa models existentes, sem alterar banco e sem reduzir arquivos.
# =====================================================

def _linhas_livro_diario_turma(turma, inicio, fim):
    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related('professor', 'disciplina', 'ano_letivo').order_by('disciplina__nome', 'professor__first_name')
    linhas = []
    for vinculo in vinculos:
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=vinculo.professor)
        professor_nome = _nome_professor_oficial(vinculo.professor)
        linhas.append({
            'vinculo': vinculo,
            'professor_nome': professor_nome,
            'bloco': bloco,
            'ok': not bloco.get('pendencias'),
        })
    return linhas


def _painel_prontidao_lancamento_professor(professor, inicio, fim):
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related('turma', 'disciplina', 'ano_letivo').order_by('turma__turno', 'turma__nome', 'disciplina__nome')
    linhas = []
    for vinculo in vinculos:
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=professor)
        frequencias = Frequencia.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, data__gte=inicio, data__lte=fim)
        if frequencias.exists():
            ultima_freq = frequencias.order_by('-data', '-id').first().data
        else:
            ultima_freq = None
        aulas = ConteudoAula.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, professor=professor, data__gte=inicio, data__lte=fim)
        ultima_aula = aulas.order_by('-data', '-id').first().data if aulas.exists() else None
        pendencias = list(bloco.get('pendencias') or [])
        if not ultima_freq:
            pendencias.append('Sem lançamento de frequência no mês')
        if not ultima_aula:
            pendencias.append('Sem registro de aula no mês')
        linhas.append({
            'vinculo': vinculo,
            'turno': _turma_turno_normalizado(vinculo.turma),
            'bloco': bloco,
            'ultima_freq': ultima_freq,
            'ultima_aula': ultima_aula,
            'pendencias': pendencias,
            'ok': not pendencias,
        })
    return linhas


# =====================================================
# ETAPAS 169–174 — Revisão oficial, espelho mensal e rastreio clicável
# Continuação segura: não altera banco, não remove lógica e reaproveita Diário Escolar existente.
# =====================================================

def _dias_com_lancamento_turma_disciplina(turma, disciplina, inicio, fim, professor=None):
    """Datas oficiais do mês com frequência e aula, mantendo P/F/FJ separados."""
    dias = []
    atual = inicio
    while atual <= fim:
        freq = Frequencia.objects.filter(turma=turma, disciplina=disciplina, data=atual)
        aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina, data=atual)
        if professor is not None:
            aulas = aulas.filter(professor=professor)
        resumo_freq = _contagens_oficiais_frequencia(freq)
        dias.append({
            'data': atual,
            'frequencia': resumo_freq,
            'aulas': aulas.order_by('id'),
            'aulas_count': aulas.count(),
            'tem_lancamento': resumo_freq['total'] > 0 or aulas.exists(),
            'ok': resumo_freq['total'] > 0 and aulas.exists(),
        })
        atual = atual + timedelta(days=1)
    return dias


def _espelho_mensal_turma_disciplina(turma, disciplina, inicio, fim, professor=None):
    bloco = _resumo_turma_disciplina_mes(turma, disciplina, inicio, fim, professor=professor)
    alunos = turma.alunos.filter(ativo=True).order_by('nome')
    linhas_alunos = []
    for aluno in alunos:
        freq = Frequencia.objects.filter(aluno=aluno, turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
        linhas_alunos.append({
            'aluno': aluno,
            'frequencia': _contagens_oficiais_frequencia(freq),
            'ultimos': freq.order_by('-data')[:6],
            'sem_lancamento': not freq.exists(),
        })
    return {
        'turma': turma,
        'disciplina': disciplina,
        'turno': _turma_turno_normalizado(turma),
        'bloco': bloco,
        'alunos': linhas_alunos,
        'dias': _dias_com_lancamento_turma_disciplina(turma, disciplina, inicio, fim, professor=professor),
    }


# =====================================================
# ETAPAS 199–204 — Checkup final de painéis e continuidade sem duplicidade
# =====================================================

def _contar_templates_pos_limpesa():
    """Resumo seguro para auditoria visual; não remove templates legados que ainda possam ter rotas."""
    from pathlib import Path
    base = Path(__file__).resolve().parents[2] / 'templates'
    professor = list((base / 'core').glob('professor_*.html')) if (base / 'core').exists() else []
    gestao = list((base / 'gestao').glob('*.html')) if (base / 'gestao').exists() else []
    return {'professor': len(professor), 'gestao': len(gestao)}


# =====================================================
# ETAPAS 301–320 — Operação real, carga horária e gestão sem admin
# =====================================================

def _nome_pessoa(usuario):
    if not usuario:
        return "—"
    return usuario.get_full_name() or getattr(usuario, "username", "—")


def _duracao_horas(horario):
    try:
        inicio = datetime.combine(date.today(), horario.hora_inicio)
        fim = datetime.combine(date.today(), horario.hora_fim)
        minutos = max(0, int((fim - inicio).total_seconds() // 60))
        return round(minutos / 60, 2)
    except Exception:
        return 0


def carga_horaria_professor_semana(professor):
    """Calcula carga horária semanal real a partir da grade cadastrada pela gestão."""
    horarios = HorarioAula.objects.select_related("turma", "disciplina").filter(
        professor=professor,
        ativo=True,
    ).order_by("dia_semana", "ordem", "hora_inicio")
    dias = []
    total_horas = 0
    total_aulas = 0
    for dia_valor, dia_nome in HorarioAula.DIAS_SEMANA:
        aulas = [h for h in horarios if h.dia_semana == dia_valor]
        horas = sum(_duracao_horas(h) for h in aulas)
        total_horas += horas
        total_aulas += len(aulas)
        dias.append({"dia": dia_nome, "aulas": aulas, "horas": round(horas, 2), "total": len(aulas)})
    return {"dias": dias, "horas": round(total_horas, 2), "aulas": total_aulas}


def aulas_professor_hoje(professor):
    dia = date.today().isoweekday()
    return HorarioAula.objects.select_related("turma", "disciplina").filter(
        professor=professor,
        ativo=True,
        dia_semana=dia,
    ).order_by("ordem", "hora_inicio")


def carga_horaria_professores_resumo():
    User = get_user_model()
    linhas = []
    for professor in User.objects.filter(tipo="PROF").order_by("first_name", "username"):
        resumo = carga_horaria_professor_semana(professor)
        linhas.append({
            "professor": professor,
            "nome": _nome_pessoa(professor),
            "horas": resumo["horas"],
            "aulas": resumo["aulas"],
            "turmas": Turma.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct().count(),
            "disciplinas": Disciplina.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct().count(),
        })
    return linhas


def _parse_hora(valor, padrao="07:00"):
    valor = valor or padrao
    try:
        return datetime.strptime(valor, "%H:%M").time()
    except Exception:
        return datetime.strptime(padrao, "%H:%M").time()


def _turno_oficial_para_turma(nome, turno_manual=None):
    turno = (turno_manual or "").upper().strip()
    if turno:
        return turno
    texto = (nome or "").lower()
    if "eja" in texto or "noite" in texto:
        return "NOTURNO"
    if "6" in texto or "7" in texto or "8" in texto or "9" in texto or "1ª" in texto or "2ª" in texto or "3ª" in texto or "ensino médio" in texto or "medio" in texto:
        return "VESPERTINO"
    return "MATUTINO"


# =====================================================
# ETAPAS 321–340 — Fluxo vivo, aula rápida e acabamento premium total
# =====================================================

def _safe_count(qs):
    try:
        return qs.count()
    except Exception:
        return 0


def _status_label(valor):
    return {"P": "Presença", "F": "Falta", "FJ": "Falta justificada"}.get(valor, valor or "—")


def _professor_pendencias_operacionais(professor):
    turmas = turmas_do_professor(professor)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True)
    horarios = HorarioAula.objects.filter(professor=professor, ativo=True)
    pendencias = []
    if not turmas.exists():
        pendencias.append({"tipo": "Vínculos", "texto": "A gestão ainda não vinculou turmas a este professor.", "nivel": "ALTO"})
    if not vinculos.exists():
        pendencias.append({"tipo": "Disciplinas", "texto": "A gestão ainda não vinculou disciplinas oficiais.", "nivel": "ALTO"})
    if not horarios.exists():
        pendencias.append({"tipo": "Carga horária", "texto": "A grade semanal do professor ainda não foi cadastrada.", "nivel": "MEDIO"})
    hoje = date.today()
    aulas_hoje_qs = aulas_professor_hoje(professor)
    for aula in aulas_hoje_qs:
        tem_conteudo = ConteudoAula.objects.filter(
            professor=professor,
            turma=aula.turma,
            disciplina=aula.disciplina,
            data=hoje,
        ).exists()
        total_alunos = aula.turma.alunos.filter(ativo=True).count()
        lancados = Frequencia.objects.filter(
            turma=aula.turma,
            disciplina=aula.disciplina,
            data=hoje,
        ).count()
        if total_alunos and lancados < total_alunos:
            pendencias.append({
                "tipo": "Chamada",
                "texto": f"{aula.turma.nome} • {aula.disciplina.nome}: {lancados}/{total_alunos} frequência(s) lançada(s) hoje.",
                "nivel": "MEDIO",
            })
        if not tem_conteudo:
            pendencias.append({
                "tipo": "Conteúdo",
                "texto": f"{aula.turma.nome} • {aula.disciplina.nome}: conteúdo da aula de hoje ainda não registrado.",
                "nivel": "MEDIO",
            })
    return pendencias


def _gestao_pendencias_operacionais():
    User = get_user_model()
    pendencias = []
    professores = User.objects.filter(tipo="PROF")
    for prof in professores:
        nome = _nome_pessoa(prof)
        if not ProfessorTurmaDisciplina.objects.filter(professor=prof, ativo=True).exists():
            pendencias.append({"area": "Professor", "texto": f"{nome} ainda não possui vínculo professor/turma/disciplina.", "nivel": "ALTO"})
        if not HorarioAula.objects.filter(professor=prof, ativo=True).exists():
            pendencias.append({"area": "Carga horária", "texto": f"{nome} ainda não possui grade semanal cadastrada.", "nivel": "MEDIO"})
    for turma in Turma.objects.filter(ativa=True):
        turno = (turma.turno or "").strip()
        if not turno:
            pendencias.append({"area": "Turmas", "texto": f"{turma.nome} está sem turno definido.", "nivel": "MEDIO"})
        if not turma.alunos.filter(ativo=True).exists():
            pendencias.append({"area": "Alunos", "texto": f"{turma.nome} ainda não possui alunos ativos.", "nivel": "BAIXO"})
    return pendencias


def _resolver_horario_do_professor(professor, horario_id=None):
    qs = HorarioAula.objects.select_related("turma", "disciplina").filter(professor=professor, ativo=True)
    if horario_id:
        return get_object_or_404(qs, pk=horario_id)

    # Etapas 831–860: quando o professor abre a aula rápida sem escolher
    # horário, prioriza a aula do dia. Isso deixa o fluxo operacional
    # contínuo: abrir aula -> chamada -> conteúdo -> fechamento.
    hoje_semana = date.today().isoweekday()
    aula_hoje = qs.filter(dia_semana=hoje_semana).order_by("ordem", "hora_inicio").first()
    if aula_hoje:
        return aula_hoje
    return qs.order_by("dia_semana", "ordem", "hora_inicio").first()


# =====================================================
# ETAPAS 361–380 — Render, UI premium e qualidade operacional
# =====================================================

def _arquivo_existe(relativo):
    try:
        return (Path(__file__).resolve().parents[2] / relativo).exists()
    except Exception:
        return False


def _saude_deploy_render():
    raiz = Path(__file__).resolve().parents[2]
    arquivos = [
        ("requirements.txt", "Dependências do projeto"),
        ("build.sh", "Build automático"),
        ("Procfile", "Start command alternativo"),
        ("render.yaml", "Blueprint Render"),
        ("runtime.txt", "Versão Python"),
        ("config/settings.py", "Configuração por variáveis de ambiente"),
    ]
    linhas = []
    for nome, descricao in arquivos:
        existe = (raiz / nome).exists()
        linhas.append({"arquivo": nome, "descricao": descricao, "status": "OK" if existe else "PENDENTE"})
    return linhas


def _qualidade_operacional_escola():
    User = get_user_model()
    turmas = Turma.objects.filter(ativa=True)
    professores = User.objects.filter(tipo="PROF")
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios = HorarioAula.objects.filter(ativo=True)
    pendencias = []
    sem_turno = turmas.filter(models.Q(turno__isnull=True) | models.Q(turno="")).count()
    if sem_turno:
        pendencias.append({"area": "Turnos", "texto": f"{sem_turno} turma(s) sem turno oficial.", "acao": "Normalizar turnos", "url": "gestao_turnos_normalizar_321"})
    sem_vinculo = professores.exclude(id__in=vinculos.values("professor_id")).count()
    if sem_vinculo:
        pendencias.append({"area": "Professores", "texto": f"{sem_vinculo} professor(es) sem vínculo turma/disciplina.", "acao": "Criar vínculo", "url": "gestao_cadastros_operacionais_301"})
    sem_horario = professores.exclude(id__in=horarios.values("professor_id")).count()
    if sem_horario:
        pendencias.append({"area": "Carga horária", "texto": f"{sem_horario} professor(es) sem grade semanal.", "acao": "Cadastrar horários", "url": "gestao_cadastros_operacionais_301"})
    turmas_sem_alunos = [t for t in turmas.prefetch_related("alunos") if not t.alunos.filter(ativo=True).exists()]
    if turmas_sem_alunos:
        pendencias.append({"area": "Alunos", "texto": f"{len(turmas_sem_alunos)} turma(s) sem alunos ativos.", "acao": "Cadastrar alunos", "url": "gestao_cadastros_operacionais_301"})
    cards = [
        {"label": "Turmas ativas", "valor": turmas.count(), "detalhe": "base do Diário Escolar"},
        {"label": "Professores", "valor": professores.count(), "detalhe": "usuários docentes"},
        {"label": "Vínculos", "valor": vinculos.count(), "detalhe": "professor/turma/disciplina"},
        {"label": "Horários", "valor": horarios.count(), "detalhe": "aulas semanais"},
    ]
    return cards, pendencias


# =====================================================
# ETAPAS 381–400 — Checkup funcional, botões e estabilização real
# =====================================================

def _reverse_status_nome(nome):
    """Tenta validar se uma rota nomeada existe sem derrubar a tela de auditoria."""
    from django.urls import reverse, NoReverseMatch
    try:
        url = reverse(nome)
        return {"nome": nome, "ok": True, "url": url, "erro": ""}
    except NoReverseMatch as exc:
        return {"nome": nome, "ok": False, "url": "", "erro": str(exc)}
    except Exception as exc:
        return {"nome": nome, "ok": False, "url": "", "erro": str(exc)}


def _auditoria_templates_botoes():
    """Varredura leve para localizar links crus e rotas cruzadas nos templates."""
    base = Path(__file__).resolve().parents[2]
    templates = base / "templates"
    problemas = []
    totais = {"templates": 0, "links_admin": 0, "links_cruzados": 0, "links_crus": 0}
    if not templates.exists():
        return totais, problemas
    for arquivo in templates.rglob("*.html"):
        rel = str(arquivo.relative_to(templates))
        try:
            texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        totais["templates"] += 1
        if "href=\"/admin" in texto or "href='/admin" in texto:
            totais["links_admin"] += 1
            problemas.append({"tipo": "Admin direto", "arquivo": rel, "detalhe": "Tem link direto para /admin/; deve virar ação da gestão."})
        if rel.startswith("gestao/") and ("{% url 'dashboard_professor" in texto or "href=\"/professor" in texto):
            totais["links_cruzados"] += 1
            problemas.append({"tipo": "Gestão → professor", "arquivo": rel, "detalhe": "Template da gestão contém atalho para área do professor."})
        if rel.startswith("core/professor") and ("{% url 'dashboard_gestao" in texto or "href=\"/gestao" in texto):
            totais["links_cruzados"] += 1
            problemas.append({"tipo": "Professor → gestão", "arquivo": rel, "detalhe": "Template do professor contém atalho para área da gestão."})
        # Detecta links sem classe visual em templates atuais principais.
        if (rel.startswith("gestao/") or rel.startswith("core/professor")) and "<a " in texto:
            crus = [linha.strip() for linha in texto.splitlines() if "<a " in linha and "class=" not in linha and "sidebar" not in linha]
            if crus:
                totais["links_crus"] += len(crus)
                problemas.append({"tipo": "Link sem classe", "arquivo": rel, "detalhe": f"{len(crus)} link(s) sem classe premium explícita."})
    return totais, problemas[:80]


def _rotas_essenciais_status():
    rotas = [
        "dashboard_gestao", "gestao_centro_operacional_321", "gestao_cadastros_operacionais_301",
        "gestao_carga_horaria_professores_301", "gestao_diario_oficial", "gestao_alunos",
        "gestao_professores", "gestao_vinculos", "gestao_horarios", "gestao_relatorios",
        "gestao_qualidade_operacional_361", "gestao_publicacao_render_361",
        "dashboard_professor", "professor_centro_operacional_321", "professor_aula_rapida_321",
        "professor_carga_horaria_301", "professor_diario_oficial", "professor_alunos",
        "professor_rotina_semanal_361", "professor_central_pendencias", "professor_ia_pedagogica",
    ]
    return [_reverse_status_nome(nome) for nome in rotas]


def _saude_operacional_381():
    User = get_user_model()
    professores = User.objects.filter(tipo="PROF")
    turmas = Turma.objects.filter(ativa=True)
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios = HorarioAula.objects.filter(ativo=True)
    alunos = Aluno.objects.filter(ativo=True)
    status_freq = {
        "p": Frequencia.objects.filter(status="P").count(),
        "f": Frequencia.objects.filter(status="F").count(),
        "fj": Frequencia.objects.filter(status="FJ").count(),
    }
    pendencias = []
    sem_vinculo = professores.exclude(id__in=vinculos.values("professor_id")).count()
    sem_horario = professores.exclude(id__in=horarios.values("professor_id")).count()
    turmas_sem_turno = turmas.filter(models.Q(turno__isnull=True) | models.Q(turno="")).count()
    turmas_sem_alunos = sum(1 for t in turmas.prefetch_related("alunos") if not t.alunos.filter(ativo=True).exists())
    if sem_vinculo:
        pendencias.append({"area": "Professor", "texto": f"{sem_vinculo} professor(es) sem vínculo oficial com turma/disciplina.", "acao": "Criar vínculo na gestão."})
    if sem_horario:
        pendencias.append({"area": "Carga horária", "texto": f"{sem_horario} professor(es) sem horário semanal cadastrado.", "acao": "Cadastrar grade semanal."})
    if turmas_sem_turno:
        pendencias.append({"area": "Turnos", "texto": f"{turmas_sem_turno} turma(s) sem turno oficial.", "acao": "Normalizar manhã/tarde/noite/EJA."})
    if turmas_sem_alunos:
        pendencias.append({"area": "Alunos", "texto": f"{turmas_sem_alunos} turma(s) sem alunos ativos.", "acao": "Conferir matrículas."})
    cards = [
        {"label": "Professores", "valor": professores.count(), "detalhe": "cadastrados"},
        {"label": "Turmas", "valor": turmas.count(), "detalhe": "ativas"},
        {"label": "Alunos", "valor": alunos.count(), "detalhe": "ativos"},
        {"label": "Vínculos", "valor": vinculos.count(), "detalhe": "professor/turma/disciplina"},
        {"label": "Horários", "valor": horarios.count(), "detalhe": "aulas semanais"},
        {"label": "P/F/FJ", "valor": f"{status_freq['p']}/{status_freq['f']}/{status_freq['fj']}", "detalhe": "frequência oficial"},
    ]
    return cards, pendencias


# =====================================================
# HELPERS COM REQUEST MOVIDOS DOS MÓDULOS REFATORADOS
# =====================================================

# Origem: views_ia.py
def _mes_ano_oficial(request):
    hoje = date.today()
    mes_param = request.GET.get("mes") or f"{hoje.year}-{hoje.month:02d}"
    try:
        ano, mes = [int(p) for p in mes_param.split("-")[:2]]
        if mes < 1 or mes > 12:
            raise ValueError
    except Exception:
        ano, mes = hoje.year, hoje.month
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
    return mes_param, ano, mes, primeiro, ultimo


# Origem: views_operacional.py
# =====================================================
# DIÁRIO OFICIAL REAL — detalhe da turma, frequência por disciplina/mês e ficha integrada
# =====================================================

def _periodo_mes_por_parametro(request, turma=None):
    hoje = date.today()
    ano_padrao = None
    try:
        ano_padrao = turma.ano_letivo.ano if turma and turma.ano_letivo else None
    except Exception:
        ano_padrao = None
    mes_param = request.GET.get("mes") or f"{ano_padrao or hoje.year}-{hoje.month:02d}"
    try:
        ano, mes = [int(parte) for parte in mes_param.split("-")]
        primeiro_dia = date(ano, mes, 1)
    except Exception:
        ano, mes = ano_padrao or hoje.year, hoje.month
        primeiro_dia = date(ano, mes, 1)
        mes_param = f"{ano}-{mes:02d}"
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
    meses = [{"valor": f"{ano}-{n:02d}", "nome": calendar.month_name[n].capitalize(), "ativo": n == mes} for n in range(1, 13)]
    return ano, mes, mes_param, primeiro_dia, ultimo_dia, meses


# Permite que os módulos refatorados importem também helpers internos com _.
__all__ = [name for name in globals() if not name.startswith('__')]



CODIGO_GESTAO_SESSION_KEY = "codigo_autorizacao_gestao_6_digitos"
CODIGO_GESTAO_EXPIRA_SESSION_KEY = "codigo_autorizacao_gestao_expira_em"
CODIGO_GESTAO_VALIDADE_MINUTOS = 15


def _emails_autorizados_gestao():
    bruto = str(getattr(settings, "GESTAO_AUTORIZACAO_EMAIL", "") or "")
    return {email.strip().lower() for email in bruto.replace(";", ",").split(",") if email.strip()}


def _gerar_codigo_gestao_6_digitos():
    """Gera um código numérico seguro, sempre com 6 dígitos."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _salvar_codigo_gestao_na_sessao(request, codigo):
    expira_em = timezone.now() + timedelta(minutes=CODIGO_GESTAO_VALIDADE_MINUTOS)
    request.session[CODIGO_GESTAO_SESSION_KEY] = codigo
    request.session[CODIGO_GESTAO_EXPIRA_SESSION_KEY] = expira_em.isoformat()
    request.session.modified = True
    return expira_em


def _limpar_codigo_gestao_da_sessao(request):
    request.session.pop(CODIGO_GESTAO_SESSION_KEY, None)
    request.session.pop(CODIGO_GESTAO_EXPIRA_SESSION_KEY, None)
    request.session.modified = True


def _codigo_gestao_sessao_valido(request, codigo_digitado):
    codigo_digitado = (codigo_digitado or "").strip()
    codigo_salvo = str(request.session.get(CODIGO_GESTAO_SESSION_KEY, "") or "").strip()
    expira_iso = str(request.session.get(CODIGO_GESTAO_EXPIRA_SESSION_KEY, "") or "").strip()

    if not codigo_digitado.isdigit() or len(codigo_digitado) != 6:
        return False
    if not codigo_salvo or codigo_digitado != codigo_salvo:
        return False

    if expira_iso:
        try:
            expira_em = datetime.fromisoformat(expira_iso)
            if timezone.is_naive(expira_em):
                expira_em = timezone.make_aware(expira_em, timezone.get_current_timezone())
        except Exception:
            _limpar_codigo_gestao_da_sessao(request)
            return False

        if timezone.now() > expira_em:
            _limpar_codigo_gestao_da_sessao(request)
            return False

    return True


def solicitar_codigo_gestao(request):
    """Envia um código numérico de 6 dígitos ao e-mail autorizado da direção.

    A tela não permite trocar o e-mail: por segurança, o sistema usa apenas o
    e-mail autorizado configurado na implantação/local settings.
    """
    emails_autorizados = sorted(_emails_autorizados_gestao())
    email_autorizado = emails_autorizados[0] if emails_autorizados else "thiago01268230@gmail.com"

    if request.method == "POST":
        if not email_autorizado:
            messages.error(request, "O e-mail autorizado da gestão ainda não foi configurado.")
        else:
            codigo = _gerar_codigo_gestao_6_digitos()
            try:
                send_mail(
                    subject="Código de autorização — Diário IA Escolar",
                    message=(
                        "Código de autorização para criar a conta da gestão:\n\n"
                        f"{codigo}\n\n"
                        f"Este código tem {CODIGO_GESTAO_VALIDADE_MINUTOS} minutos de validade.\n\n"
                        "Use este código somente na tela oficial do Diário IA Escolar. "
                        "Se você não solicitou este acesso, ignore esta mensagem."
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[email_autorizado],
                    fail_silently=False,
                )
            except Exception:
                messages.error(request, "Não foi possível enviar o e-mail agora. Confira a configuração de e-mail do sistema.")
                return render(request, "registration/solicitar_codigo_gestao.html", {"email_autorizado": email_autorizado, "validade_minutos": CODIGO_GESTAO_VALIDADE_MINUTOS})

            _salvar_codigo_gestao_na_sessao(request, codigo)
            email_backend = str(getattr(settings, "EMAIL_BACKEND", ""))
            if "console.EmailBackend" in email_backend:
                messages.warning(
                    request,
                    "Código numérico de 6 dígitos gerado no terminal porque o envio real ainda não está configurado. "
                    "No Render Free, use EMAIL_BACKEND=apps.core.email_backends.BrevoEmailBackend, BREVO_API_KEY e BREVO_SENDER_EMAIL."
                )
            else:
                messages.success(request, f"Código numérico de 6 dígitos enviado para {email_autorizado}.")

    return render(request, "registration/solicitar_codigo_gestao.html", {"email_autorizado": email_autorizado, "validade_minutos": CODIGO_GESTAO_VALIDADE_MINUTOS})

# =====================================================
# CADASTRO AUTORIZADO DA GESTÃO — LOGIN PÚBLICO
# =====================================================

def criar_conta_gestao_autorizada(request):
    """Cria uma conta de gestão somente com código numérico de 6 dígitos.

    O código é gerado na tela de solicitação, enviado ao e-mail autorizado da
    direção e validado na sessão do navegador por tempo limitado.
    """
    Usuario = get_user_model()

    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
        senha = request.POST.get("senha") or ""
        confirmar = request.POST.get("confirmar_senha") or ""
        codigo = (request.POST.get("codigo_autorizacao") or "").strip()
        erros = []

        if not nome:
            erros.append("Informe o nome da gestão responsável.")
        if not username:
            erros.append("Informe um usuário de acesso.")
        if Usuario.objects.filter(username=username).exists():
            erros.append("Esse usuário já existe.")
        if len(senha) < 6:
            erros.append("A senha precisa ter pelo menos 6 caracteres.")
        if senha != confirmar:
            erros.append("A confirmação da senha não confere.")
        if not codigo.isdigit() or len(codigo) != 6:
            erros.append("Informe o código numérico de 6 dígitos recebido por e-mail.")
        elif not _codigo_gestao_sessao_valido(request, codigo):
            erros.append("Código de autorização inválido ou expirado. Solicite um novo código por e-mail.")

        if erros:
            for erro in erros:
                messages.error(request, erro)
        else:
            partes = nome.split()
            first_name = partes[0]
            last_name = " ".join(partes[1:])
            agora = timezone.now()
            user = Usuario.objects.create_user(
                username=username,
                password=senha,
                email=email,
                first_name=first_name,
                last_name=last_name,
                tipo="ADMIN",
                is_staff=True,
                is_active=True,
                gestao_teste_inicio=agora,
                gestao_acesso_expira_em=agora + timedelta(days=dias_teste_gestao()),
                gestao_acesso_bloqueado=False,
            )
            _limpar_codigo_gestao_da_sessao(request)
            messages.success(request, "Conta da gestão criada com sucesso. Você já pode acessar o sistema.")
            login(request, user)
            return redirect("dashboard_gestao")

    return render(request, "registration/criar_conta_gestao.html")


@login_required
def ativar_acesso_gestao(request):
    """Tela de ativação comercial da gestão por serial/key.

    A gestão consegue abrir esta tela mesmo com o teste vencido. Ao aplicar
    um serial válido, o acesso é liberado pela quantidade de dias do serial.
    """
    if not usuario_eh_gestao(request.user):
        return redirect("dashboard_professor_home")

    garantir_periodo_teste(request.user)

    if request.method == "POST":
        serial = (request.POST.get("serial") or "").strip()
        ok, mensagem = validar_serial_gestao(serial, request.user)
        if ok:
            messages.success(request, mensagem)
            return redirect("dashboard_gestao")
        messages.error(request, mensagem)

    return render(
        request,
        "registration/ativar_acesso_gestao.html",
        {
            "dias_teste": dias_teste_gestao(),
            "dias_restantes": dias_restantes_gestao(request.user),
            "expira_em": getattr(request.user, "gestao_acesso_expira_em", None),
            "whatsapp": getattr(settings, "GESTAO_LICENCA_CONTATO_WHATSAPP", "98996127032"),
            "email_autorizado": getattr(settings, "GESTAO_AUTORIZACAO_EMAIL", "thiago01268230@gmail.com"),
        },
    )


# Atualiza exportação após views públicas adicionadas.
__all__ = [name for name in globals() if not name.startswith("__")]

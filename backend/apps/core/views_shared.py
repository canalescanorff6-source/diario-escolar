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
import logging
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

from .academic_analysis import AnaliseInteligenteService
from apps.academico.regras import obter_regras_academicas, classificar_situacao
from apps.diario.models import Diario

logger = logging.getLogger(__name__)
from apps.core.academic_queries import (
    disciplinas_do_professor,
    horarios_do_professor,
    turmas_do_professor,
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


def get_disciplina_padrao():
    """Compatibilidade: retorna a primeira disciplina existente, sem criar dados fictícios."""
    return Disciplina.objects.order_by("nome").first()


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
        recomendacoes.append('Lance notas T1/T2/T3 para calcular indicadores de aprendizagem e média anual.')
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
    notas_aluno = Nota.objects.filter(aluno=aluno, valor__isnull=False)
    medias = [float(n.valor) for n in notas_aluno]
    media = round(sum(medias) / len(medias), 1) if medias else None
    frequencias = Frequencia.objects.filter(aluno=aluno)
    registros = frequencias.count()
    presencas = frequencias.filter(status="P").count()
    faltas = frequencias.filter(status__in=["F", "FJ"]).count()
    frequencia = round((presencas / registros) * 100, 1) if registros else None
    situacao = classificar_situacao(
        media,
        frequencia,
        tem_notas=bool(medias),
        tem_frequencia=bool(registros),
    )
    return {
        "media": media,
        "registros": registros,
        "presencas": presencas,
        "faltas": faltas,
        "frequencia": frequencia,
        "situacao": situacao,
    }


def _media_anual_aluno(aluno):
    notas = Nota.objects.filter(aluno=aluno, valor__isnull=False).select_related("disciplina")
    valores = [float(n.valor) for n in notas if n.valor is not None]
    return round(sum(valores) / len(valores), 1) if valores else 0


def _diagnostico_recuperacao(aluno):
    regras = obter_regras_academicas()
    media = _media_anual_aluno(aluno)
    faltas = _faltas_aluno(aluno)
    notas_baixas = Nota.objects.filter(
        aluno=aluno,
        valor__isnull=False,
        valor__lt=regras.media_aprovacao,
    ).select_related("disciplina")
    disciplinas = sorted({n.disciplina.nome for n in notas_baixas if n.disciplina})
    limite_critico = float(max(Decimal("0"), regras.media_aprovacao - Decimal("1")))
    if media < limite_critico or faltas >= 20:
        nivel = "CRÍTICO"
    elif media < float(regras.media_aprovacao) or faltas >= 10:
        nivel = "ATENÇÃO"
    else:
        nivel = "ACOMPANHAR"
    acoes = []
    if media < float(regras.media_aprovacao):
        acoes.append("recuperação paralela com retomada dos conteúdos essenciais")
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


def _faltas_aluno(aluno):
    return Frequencia.objects.filter(aluno=aluno, presente=False).count()


def _ultimos_conteudos_professor(professor, limite=8):
    return ConteudoAula.objects.filter(professor=professor).select_related("turma", "disciplina").order_by("-data")[:limite]


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
# DIÁRIO REAL — etapas premium de consolidação pedagógica
# Mantém tudo existente e adiciona validações oficiais para o fluxo real.
# =====================================================


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


def _ano_letivo_ativo_oficial():
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    ano_letivo = escola.ano_letivo_ativo if escola and escola.ano_letivo_ativo else AnoLetivo.objects.filter(ativo=True).first()
    return escola, ano_letivo


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


def _resolver_horario_do_professor(professor, horario_id=None):
    qs = HorarioAula.objects.select_related("turma", "disciplina").filter(professor=professor, ativo=True)
    if horario_id:
        return get_object_or_404(qs, pk=horario_id)

    # Ao abrir o registro sem um horário específico, tenta sugerir a próxima aula.
    # horário, prioriza a aula do dia. Isso deixa o fluxo operacional
    # contínuo: abrir aula -> chamada -> conteúdo -> fechamento.
    hoje_semana = date.today().isoweekday()
    aula_hoje = qs.filter(dia_semana=hoje_semana).order_by("ordem", "hora_inicio").first()
    if aula_hoje:
        return aula_hoje
    return qs.order_by("dia_semana", "ordem", "hora_inicio").first()


# =====================================================
# HELPERS COM REQUEST MOVIDOS DOS MÓDULOS REFATORADOS
# =====================================================

# Origem: views_academico.py
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
    for chave in (
        CODIGO_GESTAO_SESSION_KEY,
        CODIGO_GESTAO_EXPIRA_SESSION_KEY,
        "codigo_gestao_tentativas",
    ):
        request.session.pop(chave, None)
    request.session.modified = True


def _codigo_gestao_sessao_valido(request, codigo_digitado):
    codigo_digitado = (codigo_digitado or "").strip()
    codigo_salvo = str(request.session.get(CODIGO_GESTAO_SESSION_KEY, "") or "").strip()
    expira_iso = str(request.session.get(CODIGO_GESTAO_EXPIRA_SESSION_KEY, "") or "").strip()
    tentativas = int(request.session.get("codigo_gestao_tentativas", 0) or 0)

    if tentativas >= int(getattr(settings, "GESTAO_CODIGO_MAX_TENTATIVAS", 5)):
        _limpar_codigo_gestao_da_sessao(request)
        return False
    if not codigo_digitado.isdigit() or len(codigo_digitado) != 6:
        request.session["codigo_gestao_tentativas"] = tentativas + 1
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

    if not codigo_salvo or not secrets.compare_digest(codigo_digitado, codigo_salvo):
        request.session["codigo_gestao_tentativas"] = tentativas + 1
        request.session.modified = True
        return False
    return True


def _mensagem_erro_email_gestao(exc):
    """Traduz falhas comuns de e-mail sem expor segredo/API key na tela."""
    texto = str(exc or "")
    baixo = texto.lower()
    if "configure brevo_api_key" in baixo or "brevo_api_key" in baixo and "sender" in baixo:
        return "Não foi possível enviar o e-mail: faltam BREVO_API_KEY ou BREVO_SENDER_EMAIL nas variáveis do RunSite."
    if "401" in texto or "unauthorized" in baixo or "invalid api key" in baixo:
        return "Não foi possível enviar o e-mail: a chave BREVO_API_KEY está inválida ou foi copiada incorretamente."
    if "sender" in baixo or "remetente" in baixo or "not verified" in baixo or "unverified" in baixo:
        return "Não foi possível enviar o e-mail: o BREVO_SENDER_EMAIL não está verificado/autorizado na Brevo."
    if "timeout" in baixo or "timed out" in baixo:
        return "Não foi possível enviar o e-mail: a RunSite demorou demais para conectar na Brevo. Tente novamente ou aumente EMAIL_TIMEOUT."
    if "connection" in baixo or "name or service not known" in baixo or "temporary failure" in baixo:
        return "Não foi possível enviar o e-mail: a RunSite não conseguiu conectar na API da Brevo."
    return "Não foi possível enviar o e-mail agora. Confira os logs do RunSite; o erro técnico foi registrado no console."

def solicitar_codigo_gestao(request):
    """Envia o código inicial somente ao e-mail configurado no ambiente."""
    emails_autorizados = sorted(_emails_autorizados_gestao())
    email_autorizado = emails_autorizados[0] if emails_autorizados else ""

    if request.method == "POST":
        if not email_autorizado:
            messages.error(request, "O e-mail autorizado da gestão ainda não foi configurado no servidor.")
        else:
            agora = timezone.now()
            ultimo_iso = request.session.get("codigo_gestao_ultimo_envio_em")
            if ultimo_iso:
                try:
                    ultimo = datetime.fromisoformat(ultimo_iso)
                    if timezone.is_naive(ultimo):
                        ultimo = timezone.make_aware(ultimo, timezone.get_current_timezone())
                    espera = int(getattr(settings, "GESTAO_CODIGO_COOLDOWN_SEGUNDOS", 60))
                    if (agora - ultimo).total_seconds() < espera:
                        messages.warning(request, f"Aguarde {espera} segundos antes de solicitar outro código.")
                        return render(request, "registration/solicitar_codigo_gestao.html", {"email_autorizado": email_autorizado, "validade_minutos": CODIGO_GESTAO_VALIDADE_MINUTOS})
                except (TypeError, ValueError):
                    pass

            codigo = _gerar_codigo_gestao_6_digitos()
            try:
                send_mail(
                    subject="Código de autorização — Diário Escolar Pro",
                    message=(
                        "Código de autorização para criar a conta da gestão:\n\n"
                        f"{codigo}\n\n"
                        f"Este código expira em {CODIGO_GESTAO_VALIDADE_MINUTOS} minutos.\n"
                        "Se você não solicitou este acesso, ignore esta mensagem."
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[email_autorizado],
                    fail_silently=False,
                )
            except Exception as exc:
                logger.exception("Falha ao enviar código de autorização da gestão")
                messages.error(request, _mensagem_erro_email_gestao(exc))
            else:
                _salvar_codigo_gestao_na_sessao(request, codigo)
                request.session["codigo_gestao_tentativas"] = 0
                request.session["codigo_gestao_ultimo_envio_em"] = agora.isoformat()
                request.session.modified = True
                if "console.EmailBackend" in str(getattr(settings, "EMAIL_BACKEND", "")):
                    messages.warning(request, "O servidor de e-mail ainda está em modo de desenvolvimento. Configure o provedor de e-mail antes de publicar.")
                else:
                    messages.success(request, "Código enviado ao e-mail autorizado.")

    return render(request, "registration/solicitar_codigo_gestao.html", {
        "email_autorizado": email_autorizado,
        "validade_minutos": CODIGO_GESTAO_VALIDADE_MINUTOS,
    })


# =====================================================
# CADASTRO AUTORIZADO DA GESTÃO — LOGIN PÚBLICO
# =====================================================

def criar_conta_gestao_autorizada(request):
    """Cria a primeira conta de gestão mediante código temporário autorizado."""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

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
        if username and Usuario.objects.filter(username=username).exists():
            erros.append("Esse usuário já existe.")
        if senha != confirmar:
            erros.append("A confirmação da senha não confere.")
        if senha:
            try:
                validate_password(senha)
            except ValidationError as exc:
                erros.extend(exc.messages)
        else:
            erros.append("Informe uma senha segura.")
        if not codigo.isdigit() or len(codigo) != 6:
            erros.append("Informe o código numérico de 6 dígitos recebido por e-mail.")
        elif not _codigo_gestao_sessao_valido(request, codigo):
            erros.append("Código de autorização inválido, expirado ou bloqueado por excesso de tentativas.")

        if erros:
            for erro in erros:
                messages.error(request, erro)
        else:
            partes = nome.split()
            agora = timezone.now()
            user = Usuario.objects.create_user(
                username=username,
                password=senha,
                email=email,
                first_name=partes[0],
                last_name=" ".join(partes[1:]),
                tipo="ADMIN",
                is_staff=True,
                is_active=True,
                gestao_teste_inicio=agora,
                gestao_acesso_expira_em=agora + timedelta(days=dias_teste_gestao()),
                gestao_acesso_bloqueado=False,
            )
            _limpar_codigo_gestao_da_sessao(request)
            messages.success(request, "Conta da gestão criada com sucesso.")
            login(request, user)
            return redirect("dashboard_gestao")

    return render(request, "registration/criar_conta_gestao.html")


@login_required
def ativar_acesso_gestao(request):
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

    return render(request, "registration/ativar_acesso_gestao.html", {
        "dias_teste": dias_teste_gestao(),
        "dias_restantes": dias_restantes_gestao(request.user),
        "expira_em": getattr(request.user, "gestao_acesso_expira_em", None),
    })


# Atualiza exportação após views públicas adicionadas.
__all__ = [name for name in globals() if not name.startswith("__")]

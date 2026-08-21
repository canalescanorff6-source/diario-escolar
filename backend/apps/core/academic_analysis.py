"""Indicadores pedagógicos baseados nas regras acadêmicas da escola.

O módulo não inventa dados: trabalha apenas com notas e frequências registradas.
"""
from decimal import Decimal

from django.db.models import Avg

from apps.academico.models import Frequencia, Nota
from apps.academico.regras import classificar_situacao, obter_regras_academicas


class AnaliseInteligenteService:
    @staticmethod
    def resumo_turma(turma):
        media_geral = Nota.objects.filter(
            aluno__turma=turma,
            valor__isnull=False,
        ).aggregate(media=Avg("valor"))["media"]

        frequencias = Frequencia.objects.filter(aluno__turma=turma)
        total_registros = frequencias.count()
        presencas = frequencias.filter(status="P").count()
        faltas = frequencias.filter(status__in=["F", "FJ"]).count()
        percentual_presenca = round((presencas / total_registros) * 100, 2) if total_registros else 100

        return {
            "media_geral": round(float(media_geral), 2) if media_geral is not None else 0,
            "total_alunos": turma.alunos.filter(ativo=True).count(),
            "total_faltas": faltas,
            "percentual_presenca": percentual_presenca,
        }

    @staticmethod
    def alunos_em_risco(turma):
        alunos_risco = []
        for aluno in turma.alunos.filter(ativo=True).order_by("nome"):
            media_obj = Nota.objects.filter(
                aluno=aluno,
                valor__isnull=False,
            ).aggregate(media=Avg("valor"))["media"]
            tem_notas = media_obj is not None
            media = float(media_obj) if tem_notas else 0.0

            frequencias = Frequencia.objects.filter(aluno=aluno)
            total_registros = frequencias.count()
            presencas = frequencias.filter(status="P").count()
            faltas = frequencias.filter(status__in=["F", "FJ"]).count()
            percentual_presenca = round((presencas / total_registros) * 100, 2) if total_registros else 100

            risco = AnaliseInteligenteService.calcular_risco(
                media,
                percentual_presenca,
                tem_notas=tem_notas,
                tem_frequencia=bool(total_registros),
            )
            if risco in {"MÉDIO", "ALTO"}:
                alunos_risco.append({
                    "aluno": aluno,
                    "nome": aluno.nome,
                    "media": round(media, 2) if tem_notas else None,
                    "faltas": faltas,
                    "presenca_%": percentual_presenca if total_registros else None,
                    "status": AnaliseInteligenteService.status_final(
                        media,
                        percentual_presenca,
                        tem_notas=tem_notas,
                        tem_frequencia=bool(total_registros),
                    ),
                    "nivel_risco": risco,
                })
        return alunos_risco

    @staticmethod
    def calcular_risco(media, presenca_percentual, *, tem_notas=True, tem_frequencia=True):
        """Score simples e auditável, parametrizado pelas regras da escola."""
        regras = obter_regras_academicas()
        score = 0

        if tem_notas:
            media_d = Decimal(str(media or 0))
            limite_critico = max(Decimal("0"), regras.media_aprovacao - Decimal("1"))
            if media_d < limite_critico:
                score += 3
            elif media_d < regras.media_aprovacao:
                score += 2
            elif media_d < regras.media_atencao:
                score += 1

        if tem_frequencia:
            freq_d = Decimal(str(presenca_percentual or 0))
            limite_critico = max(Decimal("0"), regras.frequencia_minima - Decimal("15"))
            limite_atencao = min(Decimal("100"), regras.frequencia_minima + Decimal("10"))
            if freq_d < limite_critico:
                score += 3
            elif freq_d < regras.frequencia_minima:
                score += 2
            elif freq_d < limite_atencao:
                score += 1

        if score >= 5:
            return "ALTO"
        if score >= 3:
            return "MÉDIO"
        return "BAIXO"

    @staticmethod
    def status_final(media, presenca_percentual, *, tem_notas=True, tem_frequencia=True):
        situacao = classificar_situacao(
            media,
            presenca_percentual,
            tem_notas=tem_notas,
            tem_frequencia=tem_frequencia,
        )
        return situacao.upper()

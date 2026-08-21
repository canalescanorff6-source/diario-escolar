"""Fonte única das regras acadêmicas do Diário Escolar Pro."""
from dataclasses import dataclass
from decimal import Decimal

from .models import Escola


@dataclass(frozen=True)
class RegrasAcademicas:
    media_aprovacao: Decimal = Decimal("6.00")
    media_atencao: Decimal = Decimal("7.00")
    frequencia_minima: Decimal = Decimal("75.00")


def obter_regras_academicas() -> RegrasAcademicas:
    escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()
    if not escola:
        return RegrasAcademicas()
    return RegrasAcademicas(
        media_aprovacao=Decimal(escola.media_aprovacao),
        media_atencao=Decimal(escola.media_atencao),
        frequencia_minima=Decimal(escola.frequencia_minima),
    )


def classificar_situacao(media=None, frequencia=None, *, tem_notas=True, tem_frequencia=True):
    """Classificação consistente para dashboards, relatórios e assistente pedagógico."""
    regras = obter_regras_academicas()
    if not tem_notas:
        return "Sem notas"

    media_d = Decimal(str(media or 0))
    freq_d = Decimal(str(frequencia or 0))
    frequencia_ok = (not tem_frequencia) or freq_d >= regras.frequencia_minima

    if media_d >= regras.media_aprovacao and frequencia_ok:
        return "Aprovado"
    if tem_frequencia and not frequencia_ok:
        return "Frequência insuficiente"
    if media_d < regras.media_aprovacao:
        return "Recuperação"
    return "Atenção"

from decimal import Decimal

from django.test import TestCase

from apps.academico.models import Escola
from apps.academico.regras import classificar_situacao, obter_regras_academicas


class AcademicRulesTests(TestCase):
    def test_regras_vem_da_configuracao_da_escola(self):
        Escola.objects.create(
            nome="Escola Teste",
            media_aprovacao=Decimal("7.00"),
            media_atencao=Decimal("8.00"),
            frequencia_minima=Decimal("80.00"),
            ativa=True,
        )
        regras = obter_regras_academicas()
        self.assertEqual(regras.media_aprovacao, Decimal("7.00"))
        self.assertEqual(regras.frequencia_minima, Decimal("80.00"))
        self.assertEqual(classificar_situacao(Decimal("7.50"), Decimal("85.00")), "Aprovado")
        self.assertEqual(classificar_situacao(Decimal("6.50"), Decimal("90.00")), "Recuperação")
        self.assertEqual(classificar_situacao(Decimal("9.00"), Decimal("70.00")), "Frequência insuficiente")

    def test_sem_notas_nao_inventa_media(self):
        self.assertEqual(classificar_situacao(None, None, tem_notas=False, tem_frequencia=False), "Sem notas")

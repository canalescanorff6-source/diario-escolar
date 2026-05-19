from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.academico.models import (
    ConteudoAula,
    Escola,
    FechamentoMensal,
    Frequencia,
    HorarioAula,
    ProfessorTurmaDisciplina,
    Turma,
)
from apps.core.operacao_1281_1340 import auditoria_sem_excel_1281, cobertura_diario_classe_1281
from apps.diario.models import Diario


class Command(BaseCommand):
    help = "Valida a etapa 1281-1340: diário oficial completo, gestão como fonte única e sem Excel/importador antigo."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Falha se qualquer requisito obrigatório não estiver OK.")

    def handle(self, *args, **options):
        auditoria = auditoria_sem_excel_1281()
        cobertura = cobertura_diario_classe_1281()

        if not Escola.objects.exists() and not Turma.objects.exists():
            self.stdout.write(self.style.SUCCESS("Base manual vazia validada: a gestão vai cadastrar escola, turmas, horários e vínculos manualmente."))
            self.stdout.write(self.style.SUCCESS(f"AUDITORIA_SEM_EXCEL={auditoria['ok']}"))
            if not auditoria["ok"] and options.get("strict"):
                raise CommandError("Ainda há rastros de Excel/importador antigo.")
            return
        turnos = {t["codigo"]: t for t in cobertura["turnos"]}

        requisitos = {
            "sem_excel_importador": auditoria["ok"],
            "escola": Escola.objects.filter(ativa=True).exists(),
            "manhã_5_turmas": turnos.get("MATUTINO", {}).get("total", 0) >= 5,
            "tarde_8_turmas": turnos.get("VESPERTINO", {}).get("total", 0) >= 8,
            "noite_5_ejas": turnos.get("NOTURNO", {}).get("total", 0) >= 5,
            "vinculos": ProfessorTurmaDisciplina.objects.filter(ativo=True).exists(),
            "horarios": HorarioAula.objects.filter(ativo=True).exists(),
            "frequencia_pffj": Frequencia.objects.filter(status__in=["P", "F", "FJ"]).exists(),
            "registro_aulas": ConteudoAula.objects.exists() and Diario.objects.exists(),
            "fechamento_mensal": FechamentoMensal.objects.exists(),
        }

        rotas_nomeadas = [
            ("gestao_diario_classe_oficial_1281", []),
            ("gestao_checkup_etapas_1281_1340", []),
            ("gestao_diario_oficial", []),
            ("professor_diario_classe_oficial_1281", []),
            ("professor_diario_oficial", []),
        ]
        erros_rotas = []
        for nome_rota, args in rotas_nomeadas:
            try:
                url = reverse(nome_rota, args=args)
                self.stdout.write(f"ROTA OK {url}")
            except Exception as exc:
                erros_rotas.append(f"{nome_rota}: {exc}")
        self.stdout.write("REQUISITOS_1281_1340:")
        for nome, ok in requisitos.items():
            self.stdout.write((self.style.SUCCESS("OK ") if ok else self.style.ERROR("FALHA ")) + nome)
        self.stdout.write(f"TURNOS: Manhã={turnos.get('MATUTINO',{}).get('total',0)} | Tarde={turnos.get('VESPERTINO',{}).get('total',0)} | Noite={turnos.get('NOTURNO',{}).get('total',0)}")
        self.stdout.write(f"TOTAIS: {cobertura['totais']}")
        self.stdout.write(f"AUDITORIA_SEM_EXCEL: {auditoria['ok']}")

        falhas = [nome for nome, ok in requisitos.items() if not ok] + erros_rotas
        if falhas:
            msg = "Falhas na validação 1281-1340: " + "; ".join(falhas)
            if options.get("strict"):
                raise CommandError(msg)
            self.stdout.write(self.style.WARNING(msg))
        else:
            self.stdout.write(self.style.SUCCESS("Etapa 1281-1340 validada: Diário de Classe Oficial completo e sem Excel/importador."))
            return

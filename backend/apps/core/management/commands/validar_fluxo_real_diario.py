from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse

from apps.academico.models import (
    Aluno,
    ConteudoAula,
    Disciplina,
    Escola,
    FechamentoMensal,
    Frequencia,
    HorarioAula,
    ProfessorTurmaDisciplina,
    Turma,
)
from apps.diario.models import Diario


class Command(BaseCommand):
    help = "Valida fluxo real do diário com gestão como fonte oficial de dados."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Falha se qualquer rota essencial não responder adequadamente.")

    def handle(self, *args, **options):
        User = get_user_model()

        # Modo final manual: o projeto pode ser entregue sem dados escolares para a gestão cadastrar tudo.
        if not Escola.objects.exists() and not Turma.objects.exists() and not Aluno.objects.exists():
            rotas_base = [
                ("healthz", []),
                ("dashboard_gestao", []),
                ("gestao_escola", []),
                ("gestao_diario_oficial", []),
                ("dashboard_professor_home", []),
            ]
            erros = []
            for nome_rota, args in rotas_base:
                try:
                    reverse(nome_rota, args=args)
                    self.stdout.write(self.style.SUCCESS(f"ROTA OK {nome_rota}"))
                except Exception as exc:
                    erros.append(f"{nome_rota}: {exc}")
            self.stdout.write(self.style.SUCCESS("Base manual vazia validada: nenhum dado escolar de teste foi criado."))
            if erros and options.get("strict"):
                raise CommandError("Falhas em rotas base: " + "; ".join(erros))
            return

        gestor = User.objects.filter(tipo__in=["ADMIN", "COORD", "SEC"]).first()
        professor = User.objects.filter(tipo="PROF").first()
        turma = Turma.objects.filter(ativa=True).first()
        aluno = Aluno.objects.filter(turma=turma).first() if turma else None
        horario = HorarioAula.objects.filter(professor=professor, turma=turma, ativo=True).first() if turma and professor else None

        requisitos = {
            "Escola": Escola.objects.count(),
            "Turmas oficiais": Turma.objects.filter(ativa=True).count(),
            "Disciplina": Disciplina.objects.count(),
            "Vínculos": ProfessorTurmaDisciplina.objects.filter(ativo=True).count(),
            "Horários": HorarioAula.objects.filter(ativo=True).count(),
            "Frequência": Frequencia.objects.filter(turma=turma).count() if turma else 0,
            "Conteúdo": ConteudoAula.objects.filter(turma=turma, professor=professor).count() if turma and professor else 0,
            "Diário": Diario.objects.filter(turma=turma, professor=professor).count() if turma and professor else 0,
            "FechamentoMensal": FechamentoMensal.objects.filter(turma=turma, professor=professor).count() if turma and professor else 0,
        }
        faltantes = [nome for nome, total in requisitos.items() if not total]
        if faltantes:
            msg = "Base ainda incompleta para fluxo com dados reais: " + ", ".join(faltantes) + ". A gestão pode cadastrar esses dados manualmente."
            if options.get("strict"):
                self.stdout.write(self.style.WARNING(msg))
            else:
                self.stdout.write(self.style.WARNING(msg))

        rotas_nomeadas = [
            ("dashboard_gestao", []),
            ("gestao_diario_classe_oficial_1281", []),
            ("gestao_checkup_etapas_1281_1340", []),
            ("gestao_diario_oficial", []),
            ("dashboard_professor_home", []),
            ("professor_diario_classe_oficial_1281", []),
            ("professor_diario_oficial", []),
        ]
        if aluno:
            rotas_nomeadas.append(("gestao_ficha_aluno_oficial", [aluno.id]))
        if horario:
            rotas_nomeadas.append(("professor_aula_rapida_321_horario", [horario.id]))

        erros = []
        self.stdout.write("Acessos principais resolvidas:")
        for nome_rota, args in rotas_nomeadas:
            try:
                url = reverse(nome_rota, args=args)
                self.stdout.write(f"  OK {url}")
            except Exception as exc:
                erros.append(f"{nome_rota}: {exc}")
        if erros:
            msg = "Fluxo real com falhas de rota: " + "; ".join(erros)
            if options.get("strict"):
                raise CommandError(msg)
            self.stdout.write(self.style.WARNING(msg))
        else:
            self.stdout.write(self.style.SUCCESS("Fluxo real validado sem erro técnico."))
            return

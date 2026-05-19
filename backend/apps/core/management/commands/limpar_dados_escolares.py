from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.academico.models import (
    Aluno, AnoLetivo, AssinaturaDocumento, AuditoriaSistema, BackupSistema,
    CalendarioEvento, ConteudoAula, Disciplina, DocumentoGerado, Escola,
    FechamentoBimestre, Frequencia, HistoricoAluno, HorarioAula, IndicadorGestao,
    IntegracaoEscolar, Nota, NotificacaoGestao, ParecerAluno,
    ProfessorPerfil, ProfessorTurmaDisciplina, Turma,
)
from apps.diario.models import Diario
try:
    from apps.academico.models import FechamentoMensal
except Exception:
    FechamentoMensal = None


class Command(BaseCommand):
    help = "Remove dados escolares e de teste, mantendo migrations e estrutura do sistema."

    def add_arguments(self, parser):
        parser.add_argument("--usuarios", action="store_true", help="Também remove usuários cadastrados.")
        parser.add_argument("--confirmar", action="store_true", help="Confirma a limpeza.")

    def handle(self, *args, **options):
        if not options["confirmar"]:
            self.stdout.write(self.style.WARNING("Use --confirmar para executar a limpeza."))
            return
        models = [
            Diario, ConteudoAula, Frequencia, Nota,
            DocumentoGerado, AssinaturaDocumento, AuditoriaSistema, BackupSistema,
            CalendarioEvento, FechamentoBimestre, HistoricoAluno, IndicadorGestao,
            IntegracaoEscolar, NotificacaoGestao, ParecerAluno,
            HorarioAula, ProfessorTurmaDisciplina, ProfessorPerfil,
            Aluno, Turma, Disciplina, Escola, AnoLetivo,
        ]
        if FechamentoMensal:
            models.insert(0, FechamentoMensal)
        for model in models:
            try:
                total = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f"{model.__name__}: {total} removidos")
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"{model.__name__}: ignorado ({exc})"))
        if options["usuarios"]:
            User = get_user_model()
            total = User.objects.count()
            User.objects.all().delete()
            self.stdout.write(f"Usuários: {total} removidos")
        self.stdout.write(self.style.SUCCESS("Base limpa para cadastro manual pela gestão."))

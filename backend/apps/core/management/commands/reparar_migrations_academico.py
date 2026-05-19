from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

from apps.academico.models import BackupSistema, IntegracaoEscolar, IndicadorGestao


class Command(BaseCommand):
    help = (
        "Repara histórico antigo de migrations do app academico quando o banco local "
        "tem academico.0004 aplicado antes da cadeia compatível 0002/0003. "
        "Use apenas se `python manage.py migrate` acusar InconsistentMigrationHistory."
    )

    def table_exists(self, table_name):
        return table_name in connection.introspection.table_names()

    def create_table_if_missing(self, model):
        table_name = model._meta.db_table
        if self.table_exists(table_name):
            self.stdout.write(self.style.WARNING(f"Tabela já existe: {table_name}"))
            return False
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model)
        self.stdout.write(self.style.SUCCESS(f"Tabela criada: {table_name}"))
        return True

    def record_migration_if_missing(self, app, name):
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()
        if (app, name) in applied:
            self.stdout.write(self.style.WARNING(f"Migration já registrada: {app}.{name}"))
            return False
        recorder.record_applied(app, name)
        self.stdout.write(self.style.SUCCESS(f"Migration registrada: {app}.{name}"))
        return True

    def handle(self, *args, **options):
        self.stdout.write("Iniciando reparo seguro das migrations do app academico...")

        # Estas tabelas pertencem à migration atual academico.0002_painel_executivo_backup_integracoes.
        # Em bancos antigos, a linha de migration pode estar faltando e as tabelas também.
        for model in (BackupSistema, IntegracaoEscolar, IndicadorGestao):
            self.create_table_if_missing(model)

        self.record_migration_if_missing("academico", "0002_painel_executivo_backup_integracoes")
        self.record_migration_if_missing("academico", "0003_etapa11_compatibilidade")

        self.stdout.write(self.style.SUCCESS("Reparo concluído. Agora rode: python manage.py migrate"))

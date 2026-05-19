$ErrorActionPreference = "Stop"

# Este script pode ser executado na pasta raiz do repositorio:
# C:\Users\Administrator\Documents\GitHub\diario-escolar
# ou dentro da pasta backend:
# C:\Users\Administrator\Documents\GitHub\diario-escolar\backend

if (Test-Path "backend\apps\academico\migrations") {
    $MigrationDir = Join-Path (Get-Location).Path "backend\apps\academico\migrations"
} elseif (Test-Path "apps\academico\migrations") {
    $MigrationDir = Join-Path (Get-Location).Path "apps\academico\migrations"
} else {
    throw "Nao encontrei a pasta de migrations. Execute na pasta diario-escolar ou diario-escolar\backend."
}

Write-Host "Pasta de migrations encontrada: $MigrationDir"

$Migration0007 = @'
from django.db import migrations


def _table_exists(connection, cursor, table_name):
    return table_name in connection.introspection.table_names(cursor)


def _columns(connection, cursor, table_name):
    if not _table_exists(connection, cursor, table_name):
        return set()

    description = connection.introspection.get_table_description(cursor, table_name)
    columns = set()

    for column in description:
        name = getattr(column, "name", None)
        if not name and len(column) > 0:
            name = column[0]
        if name:
            columns.add(name)

    return columns


def _add_column_if_missing(connection, cursor, schema_editor, table_name, column_name, sql_fragment):
    if _table_exists(connection, cursor, table_name):
        if column_name not in _columns(connection, cursor, table_name):
            cursor.execute(
                f"ALTER TABLE {schema_editor.quote_name(table_name)} "
                f"ADD COLUMN {schema_editor.quote_name(column_name)} {sql_fragment}"
            )


def reparar_schema(apps, schema_editor):
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        _add_column_if_missing(
            connection,
            cursor,
            schema_editor,
            "academico_escola",
            "ano_letivo_ativo_id",
            "bigint NULL REFERENCES academico_anoletivo(id) DEFERRABLE INITIALLY DEFERRED",
        )

        _add_column_if_missing(
            connection,
            cursor,
            schema_editor,
            "academico_horarioaula",
            "ordem",
            "smallint NOT NULL DEFAULT 1",
        )

        _add_column_if_missing(
            connection,
            cursor,
            schema_editor,
            "academico_professorperfil",
            "usuario_id",
            "bigint NULL REFERENCES usuarios_usuario(id) DEFERRABLE INITIALLY DEFERRED",
        )

        if _table_exists(connection, cursor, "academico_professorperfil"):
            cols = _columns(connection, cursor, "academico_professorperfil")
            if "usuario_id" in cols and "professor_id" in cols:
                cursor.execute(
                    "UPDATE academico_professorperfil "
                    "SET usuario_id = professor_id "
                    "WHERE usuario_id IS NULL"
                )

        modelos_para_garantir = [
            "ProfessorTurmaDisciplina",
            "CalendarioEvento",
            "FechamentoBimestre",
            "ParecerAluno",
            "AssinaturaDocumento",
            "HistoricoAluno",
            "AuditoriaSistema",
            "DocumentoGerado",
            "NotificacaoGestao",
        ]

        for model_name in modelos_para_garantir:
            Model = apps.get_model("academico", model_name)
            if not _table_exists(connection, cursor, Model._meta.db_table):
                schema_editor.create_model(Model)


def reverter_reparo(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("academico", "0004_alter_nota_disciplina"),
    ]

    operations = [
        migrations.RunPython(reparar_schema, reverter_reparo),
    ]
'@

$Migration0008 = @'
from django.db import migrations


def _table_exists(connection, cursor, table_name):
    return table_name in connection.introspection.table_names(cursor)


def _columns(connection, cursor, table_name):
    if not _table_exists(connection, cursor, table_name):
        return set()

    description = connection.introspection.get_table_description(cursor, table_name)
    columns = set()

    for column in description:
        name = getattr(column, "name", None)
        if not name and len(column) > 0:
            name = column[0]
        if name:
            columns.add(name)

    return columns


def garantir_horario_numero(apps, schema_editor):
    connection = schema_editor.connection
    table = "academico_horarioaula"

    with connection.cursor() as cursor:
        if not _table_exists(connection, cursor, table):
            return

        if "numero" not in _columns(connection, cursor, table):
            cursor.execute(
                f"ALTER TABLE {schema_editor.quote_name(table)} "
                f"ADD COLUMN {schema_editor.quote_name('numero')} integer NOT NULL DEFAULT 1"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("academico", "0007_reparo_schema_banco_existente"),
    ]

    operations = [
        migrations.RunPython(garantir_horario_numero, migrations.RunPython.noop),
    ]
'@

$Migration0009 = @'
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _table_exists(connection, cursor, table_name):
    return table_name in connection.introspection.table_names(cursor)


def _columns(connection, cursor, table_name):
    if not _table_exists(connection, cursor, table_name):
        return set()

    description = connection.introspection.get_table_description(cursor, table_name)
    columns = set()

    for column in description:
        name = getattr(column, "name", None)
        if not name and len(column) > 0:
            name = column[0]
        if name:
            columns.add(name)

    return columns


def garantir_professor_id(apps, schema_editor):
    connection = schema_editor.connection
    table = "academico_professorperfil"

    with connection.cursor() as cursor:
        if not _table_exists(connection, cursor, table):
            return

        colunas = _columns(connection, cursor, table)

        if "professor_id" not in colunas:
            cursor.execute(
                f"ALTER TABLE {schema_editor.quote_name(table)} "
                f"ADD COLUMN {schema_editor.quote_name('professor_id')} "
                "bigint NULL REFERENCES usuarios_usuario(id) DEFERRABLE INITIALLY DEFERRED"
            )
            colunas.add("professor_id")

        if "usuario_id" in colunas and "professor_id" in colunas:
            cursor.execute(
                f"UPDATE {schema_editor.quote_name(table)} "
                f"SET {schema_editor.quote_name('professor_id')} = {schema_editor.quote_name('usuario_id')} "
                f"WHERE {schema_editor.quote_name('professor_id')} IS NULL "
                f"AND {schema_editor.quote_name('usuario_id')} IS NOT NULL"
            )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("academico", "0008_reparo_horario_numero"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(garantir_professor_id, migrations.RunPython.noop)
            ],
            state_operations=[
                migrations.AddField(
                    model_name="professorperfil",
                    name="professor",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="professor_id",
                        limit_choices_to={"tipo": "PROF"},
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
'@

Set-Content -Encoding UTF8 (Join-Path $MigrationDir "0007_reparo_schema_banco_existente.py") $Migration0007
Set-Content -Encoding UTF8 (Join-Path $MigrationDir "0008_reparo_horario_numero.py") $Migration0008
Set-Content -Encoding UTF8 (Join-Path $MigrationDir "0009_reparo_professorperfil_professor_id.py") $Migration0009

Write-Host "OK: migrations 0007, 0008 e 0009 corrigidas para PostgreSQL/Neon."

$Restantes = Select-String -Path (Join-Path $MigrationDir "*.py") -Pattern "sqlite_master|PRAGMA" -SimpleMatch -ErrorAction SilentlyContinue
if ($Restantes) {
    Write-Host "ATENCAO: ainda existem referencias a SQLite em outros arquivos:"
    $Restantes | ForEach-Object { Write-Host $_.Path ":" $_.LineNumber ":" $_.Line }
    Write-Host "Se o Render acusar outro erro, mande o log para corrigirmos a proxima migration."
} else {
    Write-Host "OK: nao encontrei sqlite_master nem PRAGMA nas migrations."
}

$ErrorActionPreference = "Stop"

function Find-MigrationsDir {
    $candidates = @()
    $current = (Get-Location).Path
    $candidates += $current
    $parent = Split-Path $current -Parent
    if ($parent) { $candidates += $parent }
    $grand = Split-Path $parent -Parent
    if ($grand) { $candidates += $grand }

    foreach ($base in $candidates) {
        $p1 = Join-Path $base "apps\academico\migrations"
        if (Test-Path $p1) { return $p1 }

        $p2 = Join-Path $base "backend\apps\academico\migrations"
        if (Test-Path $p2) { return $p2 }
    }

    throw "Não encontrei apps\academico\migrations. Rode este script dentro da pasta diario-escolar ou diario-escolar\backend."
}

$migrationsDir = Find-MigrationsDir
Write-Host "Pasta de migrations encontrada:" $migrationsDir

$arquivo0007 = Join-Path $migrationsDir "0007_reparo_schema_banco_existente.py"
$arquivo0008 = Join-Path $migrationsDir "0008_reparo_horario_numero.py"

@'
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
'@ | Set-Content -Encoding UTF8 $arquivo0007

@'
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
'@ | Set-Content -Encoding UTF8 $arquivo0008

Write-Host "OK: migrations corrigidas para PostgreSQL/Neon."
Write-Host "Arquivos atualizados:"
Write-Host $arquivo0007
Write-Host $arquivo0008

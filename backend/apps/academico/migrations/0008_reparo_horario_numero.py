from django.db import migrations, models


def _colunas(schema_editor, table):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        return {c.name for c in connection.introspection.get_table_description(cursor, table)}


def garantir_horario_numero(apps, schema_editor):
    table = "academico_horarioaula"
    connection = schema_editor.connection
    tables = set(connection.introspection.table_names())
    if table not in tables:
        return
    colunas = _colunas(schema_editor, table)
    qn = connection.ops.quote_name
    with connection.cursor() as cursor:
        if "horario_numero" not in colunas:
            cursor.execute(
                f"ALTER TABLE {qn(table)} ADD COLUMN {qn('horario_numero')} integer NOT NULL DEFAULT 1"
            )
        cursor.execute(
            f"UPDATE {qn(table)} SET {qn('horario_numero')} = {qn('ordem')} "
            f"WHERE {qn('horario_numero')} IS NULL OR {qn('horario_numero')} = 0"
        )


class Migration(migrations.Migration):
    dependencies = [("academico", "0007_reparo_schema_banco_existente")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(garantir_horario_numero, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name="horarioaula",
                    name="horario_numero",
                    field=models.PositiveSmallIntegerField(default=1, verbose_name="Número do horário"),
                ),
            ],
        ),
    ]

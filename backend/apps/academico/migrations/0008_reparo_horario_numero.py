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

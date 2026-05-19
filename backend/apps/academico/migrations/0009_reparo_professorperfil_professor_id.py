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

from django.db import migrations, models


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


def garantir_horario_numero_no_banco(apps, schema_editor):
    connection = schema_editor.connection
    table = "academico_horarioaula"
    with connection.cursor() as cursor:
        if not _table_exists(connection, cursor, table):
            return
        colunas = _columns(connection, cursor, table)
        if "horario_numero" not in colunas:
            cursor.execute(
                f"ALTER TABLE {schema_editor.quote_name(table)} "
                f"ADD COLUMN {schema_editor.quote_name('horario_numero')} integer NOT NULL DEFAULT 1"
            )
            colunas.add("horario_numero")
        if "ordem" in colunas:
            cursor.execute(
                f"UPDATE {schema_editor.quote_name(table)} "
                f"SET {schema_editor.quote_name('horario_numero')} = {schema_editor.quote_name('ordem')} "
                f"WHERE {schema_editor.quote_name('horario_numero')} IS NULL "
                f"OR {schema_editor.quote_name('horario_numero')} = 0"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("academico", "0013_escola_login_institucional"),
    ]
    operations = [
        migrations.RunPython(garantir_horario_numero_no_banco, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="escola",
            name="brasao_logo",
            field=models.ImageField(
                blank=True,
                help_text="Imagem institucional exibida na tela de login institucional.",
                null=True,
                upload_to="escolas/",
                verbose_name="Foto, logo ou brasão",
            ),
        ),
        migrations.AlterField(
            model_name="frequencia",
            name="status",
            field=models.CharField(
                choices=[("P", "Presença"), ("F", "Falta"), ("FJ", "Falta justificada")],
                db_index=True,
                default="P",
                help_text="Status oficial do Diário Escolar: P, F ou FJ.",
                max_length=2,
            ),
        ),
    ]

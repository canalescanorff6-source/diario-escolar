from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def garantir_professor_id(apps, schema_editor):
    table = "academico_professorperfil"
    connection = schema_editor.connection
    if table not in set(connection.introspection.table_names()):
        return
    qn = connection.ops.quote_name
    with connection.cursor() as cursor:
        colunas = {c.name for c in connection.introspection.get_table_description(cursor, table)}
        if "professor_id" not in colunas:
            cursor.execute(f"ALTER TABLE {qn(table)} ADD COLUMN {qn('professor_id')} bigint NULL")
            colunas.add("professor_id")
        if "usuario_id" in colunas:
            cursor.execute(
                f"UPDATE {qn(table)} SET {qn('professor_id')} = {qn('usuario_id')} "
                f"WHERE {qn('professor_id')} IS NULL AND {qn('usuario_id')} IS NOT NULL"
            )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("academico", "0008_reparo_horario_numero"),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(garantir_professor_id, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name="professorperfil",
                    name="professor",
                    field=models.ForeignKey(
                        blank=True, db_column="professor_id", limit_choices_to={"tipo": "PROF"},
                        null=True, on_delete=django.db.models.deletion.CASCADE, related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

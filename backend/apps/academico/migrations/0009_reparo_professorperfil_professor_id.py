from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def garantir_professor_id(apps, schema_editor):
    table = 'academico_professorperfil'
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=%s", [table])
        if cursor.fetchone() is None:
            return
        cursor.execute(f"PRAGMA table_info({table})")
        colunas = [row[1] for row in cursor.fetchall()]
        if 'professor_id' not in colunas:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN professor_id bigint NULL REFERENCES usuarios_usuario(id) DEFERRABLE INITIALLY DEFERRED")
        if 'usuario_id' in colunas or 'usuario_id' in [*colunas, 'usuario_id']:
            cursor.execute(f"UPDATE {table} SET professor_id = usuario_id WHERE professor_id IS NULL AND usuario_id IS NOT NULL")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academico', '0008_reparo_horario_numero'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(garantir_professor_id, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name='professorperfil',
                    name='professor',
                    field=models.ForeignKey(blank=True, db_column='professor_id', limit_choices_to={'tipo': 'PROF'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
    ]

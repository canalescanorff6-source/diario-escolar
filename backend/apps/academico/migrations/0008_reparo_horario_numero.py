from django.db import migrations, models


def garantir_horario_numero(apps, schema_editor):
    table = 'academico_horarioaula'
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"PRAGMA table_info({table})")
        colunas = [row[1] for row in cursor.fetchall()]
        if 'horario_numero' not in colunas:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN horario_numero integer NOT NULL DEFAULT 1")
        cursor.execute(f"UPDATE {table} SET horario_numero = ordem WHERE horario_numero IS NULL OR horario_numero = 0")


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0007_reparo_schema_banco_existente'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(garantir_horario_numero, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name='horarioaula',
                    name='horario_numero',
                    field=models.PositiveSmallIntegerField(default=1, verbose_name='Número do horário'),
                ),
            ],
        ),
    ]

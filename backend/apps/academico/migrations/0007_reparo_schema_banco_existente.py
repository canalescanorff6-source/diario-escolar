# Migration de reparo para bancos SQLite antigos do Diário Escolar Pro.
# Ela é idempotente: só cria colunas/tabelas ausentes, preservando dados existentes.

from django.db import migrations


def _table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=%s", [table_name])
    return cursor.fetchone() is not None


def _columns(cursor, table_name):
    if not _table_exists(cursor, table_name):
        return set()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _add_column_if_missing(cursor, table_name, column_name, sql_fragment):
    if _table_exists(cursor, table_name) and column_name not in _columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_fragment}")


def reparar_schema(apps, schema_editor):
    connection = schema_editor.connection
    # Esta migration existe apenas para reparar bases SQLite históricas.
    # Em PostgreSQL a estrutura já é criada pelas migrations declarativas anteriores.
    if connection.vendor != "sqlite":
        return
    cursor = connection.cursor()

    # Campos que versões antigas do banco podem não possuir.
    _add_column_if_missing(cursor, "academico_escola", "ano_letivo_ativo_id", "bigint NULL REFERENCES academico_anoletivo(id) DEFERRABLE INITIALLY DEFERRED")
    _add_column_if_missing(cursor, "academico_horarioaula", "ordem", "smallint unsigned NOT NULL DEFAULT 1")

    # ProfessorPerfil antigo usava professor_id; o model atual usa usuario_id.
    _add_column_if_missing(cursor, "academico_professorperfil", "usuario_id", "bigint NULL REFERENCES usuarios_usuario(id) DEFERRABLE INITIALLY DEFERRED")
    if _table_exists(cursor, "academico_professorperfil"):
        cols = _columns(cursor, "academico_professorperfil")
        if "usuario_id" in cols and "professor_id" in cols:
            cursor.execute("UPDATE academico_professorperfil SET usuario_id = professor_id WHERE usuario_id IS NULL")

    # Cria tabelas novas que podem existir no model/migration atual, mas não no banco antigo.
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
        if not _table_exists(cursor, Model._meta.db_table):
            schema_editor.create_model(Model)


def reverter_reparo(apps, schema_editor):
    # Não removemos colunas/tabelas para evitar perda de dados em rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("academico", "0004_alter_nota_disciplina"),
    ]

    operations = [
        migrations.RunPython(reparar_schema, reverter_reparo),
    ]

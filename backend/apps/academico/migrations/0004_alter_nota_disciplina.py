# Compatibility migration required by diario.0001_initial.
# Nota.disciplina is already nullable/blank in the current model state.
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('academico', '0003_etapa11_compatibilidade'),
    ]
    operations = []

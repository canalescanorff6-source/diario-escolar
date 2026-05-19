# Compatibility migration kept to preserve the historical dependency chain.
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('academico', '0002_painel_executivo_backup_integracoes'),
    ]
    operations = []

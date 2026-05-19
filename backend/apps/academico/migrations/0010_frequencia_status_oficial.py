# Generated for Diário IA Escolar Premium - Etapas 223-228
from django.db import migrations, models


def migrar_status_frequencia(apps, schema_editor):
    Frequencia = apps.get_model('academico', 'Frequencia')
    for freq in Frequencia.objects.all().iterator():
        obs = (freq.observacao or '').lower()
        if 'justificada' in obs or 'fj' in obs:
            freq.status = 'FJ'
            freq.presente = False
        elif freq.presente:
            freq.status = 'P'
        else:
            freq.status = 'F'
        freq.save(update_fields=['status', 'presente'])


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0009_reparo_professorperfil_professor_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='frequencia',
            name='status',
            field=models.CharField(choices=[('P', 'Presença'), ('F', 'Falta'), ('FJ', 'Falta justificada')], db_index=True, default='P', help_text='Status oficial do Diário Real: P, F ou FJ.', max_length=2),
        ),
        migrations.RunPython(migrar_status_frequencia, migrations.RunPython.noop),
    ]

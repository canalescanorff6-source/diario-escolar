from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0003_acesso_gestao_trial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chave_hash", models.CharField(db_index=True, max_length=64, unique=True)),
                ("prefixo", models.CharField(db_index=True, max_length=12)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("ultimo_uso_em", models.DateTimeField(blank=True, null=True)),
                ("expira_em", models.DateTimeField()),
                ("revogado", models.BooleanField(default=False)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="api_tokens", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Token do aplicativo",
                "verbose_name_plural": "Tokens do aplicativo",
                "ordering": ["-criado_em"],
            },
        )
    ]

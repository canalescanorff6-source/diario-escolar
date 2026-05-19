from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse


class Command(BaseCommand):
    help = "Valida prontidão para Render sem alterar dados."

    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR)
        root = base.parent
        checks = [
            ("render.yaml raiz", root / "render.yaml"),
            ("build.sh", base / "build.sh"),
            ("requirements.txt", base / "requirements.txt"),
            ("db.sqlite3 preservado", base / "db.sqlite3"),
            (".python-version", root / ".python-version"),
        ]
        erros = []
        for nome, path in checks:
            if path.exists():
                self.stdout.write(self.style.SUCCESS(f"OK {nome}: {path}"))
            else:
                erros.append(nome)
                self.stdout.write(self.style.ERROR(f"FALTA {nome}: {path}"))
        settings_text = (base / "config/settings.py").read_text(encoding="utf-8", errors="ignore")
        for token in ["DATABASE_URL", "whitenoise", "SECURE_SSL_REDIRECT", "CSRF_TRUSTED_ORIGINS"]:
            if token.lower() in settings_text.lower():
                self.stdout.write(self.style.SUCCESS(f"OK settings: {token}"))
            else:
                erros.append(f"settings:{token}")
                self.stdout.write(self.style.ERROR(f"FALTA settings: {token}"))
        try:
            self.stdout.write(self.style.SUCCESS(f"OK healthz: {reverse('healthz')}"))
        except Exception as exc:
            erros.append("healthz")
            self.stdout.write(self.style.ERROR(f"FALTA healthz: {exc}"))
        if erros:
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("Publicação do sistema validada."))

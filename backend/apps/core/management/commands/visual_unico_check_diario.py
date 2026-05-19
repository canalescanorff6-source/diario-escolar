from __future__ import annotations

import re
from pathlib import Path
from collections import Counter

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Audita se as telas do projeto estão usando somente as bases premium novas."

    PREMIUM_BASES = {"gestao/base_premium_gestao.html", "core/base_professor_premium.html", "registration/base_auth_premium.html", "registration/login.html"}
    LEGACY_TERMS = [
        "dashboard.css",
        "layout_premium_fix.css",
        "ui_premium_actions_421.css",
        "partials/sidebar_contextual.html",
        "<aside class=\"sidebar",
        "legacy-shell-premium",
    ]

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Falha se encontrar visual legado em templates usados.")

    def _used_templates(self):
        used = set()
        for py in list(Path("apps").rglob("*.py")) + list(Path("config").rglob("*.py")):
            text = py.read_text(errors="ignore")
            used.update(re.findall(r"render\s*\([^,]+,\s*['\"]([^'\"]+\.html)['\"]", text))
            used.update(re.findall(r"template_name\s*=\s*['\"]([^'\"]+\.html)['\"]", text))
        return sorted(used)

    def _extends(self, text):
        match = re.search(r"\{\%\s*extends\s+['\"]([^'\"]+)", text)
        return match.group(1) if match else None

    def handle(self, *args, **options):
        used = self._used_templates()
        base_counter = Counter()
        legacy_hits = []
        missing = []

        for rel in used:
            path = Path("templates") / rel
            if not path.exists():
                missing.append(rel)
                continue
            text = path.read_text(errors="ignore")
            base = self._extends(text)
            base_counter[base or "SEM_EXTENDS"] += 1
            if base not in self.PREMIUM_BASES:
                legacy_hits.append((rel, f"base não premium: {base or 'SEM_EXTENDS'}"))
            for term in self.LEGACY_TERMS:
                if term in text:
                    legacy_hits.append((rel, f"termo legado: {term}"))

        css_total = len(list(Path("static/css").glob("*.css")))
        self.stdout.write(f"TEMPLATES_USADOS={len(used)}")
        self.stdout.write(f"BASES={dict(base_counter)}")
        self.stdout.write(f"CSS_ATIVOS={css_total}")
        self.stdout.write(f"AUSENTES={len(missing)}")
        self.stdout.write(f"LEGADO_VISUAL={len(legacy_hits)}")
        for rel, reason in legacy_hits[:80]:
            self.stdout.write(self.style.ERROR(f"LEGADO {rel}: {reason}"))
        for rel in missing[:30]:
            self.stdout.write(self.style.WARNING(f"AUSENTE {rel}"))
        if legacy_hits and options.get("strict"):
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("Auditoria visual premium concluída."))

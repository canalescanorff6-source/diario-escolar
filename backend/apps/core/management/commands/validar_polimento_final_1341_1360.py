from __future__ import annotations

import re
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Valida o polimento final: sem rastros antigos visíveis, sem caches, CSS enxuto, scroll/UX final instalado."

    BANNED_VISIBLE = [
        "sem Excel/importador antigo",
        "Excel/importador antigo",
        "Publicação pronta",
        "render ready",
        "Etapas",
        "etapas",
        "Checkup",
        "checkup",
    ]

    REQUIRED_SNIPPETS = [
        (Path("static/css/premium_base_final.css"), "ETAPA FINALÍSSIMA 1341-1360"),
        (Path("static/js/premium_app_final.js"), "navegação sem salto"),
    ]

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Falha se encontrar pendências finais.")

    def _visible_text(self, html: str) -> str:
        html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
        html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
        html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
        html = re.sub(r"<[^>]+>", " ", html)
        html = re.sub(r"\{#[\s\S]*?#\}", " ", html)
        html = re.sub(r"\{%[\s\S]*?%\}", " ", html)
        html = re.sub(r"\{\{[\s\S]*?\}\}", " ", html)
        return re.sub(r"\s+", " ", html)

    def handle(self, *args, **options):
        errors = []
        warnings = []

        for old_dir in [Path("../frontend"), Path("../static")]:
            if old_dir.exists():
                errors.append(f"Rastro antigo na raiz: {old_dir}")

        pycache = list(Path(".").rglob("__pycache__"))
        pyc = list(Path(".").rglob("*.pyc"))
        if pycache:
            errors.append(f"__pycache__ restantes: {len(pycache)}")
        if pyc:
            errors.append(f".pyc restantes: {len(pyc)}")

        css_files = list(Path("static/css").glob("*.css"))
        js_files = list(Path("static/js").glob("*.js"))
        if len(css_files) > 4:
            warnings.append(f"CSS ativos acima do alvo: {len(css_files)}")
        if len(js_files) > 2:
            warnings.append(f"JS ativos acima do alvo: {len(js_files)}")

        for file_path, snippet in self.REQUIRED_SNIPPETS:
            if not file_path.exists() or snippet not in file_path.read_text(encoding="utf-8", errors="ignore"):
                errors.append(f"Reforço final ausente em {file_path}: {snippet}")

        visible_hits = []
        for tpl in Path("templates").rglob("*.html"):
            text = tpl.read_text(encoding="utf-8", errors="ignore")
            visible = self._visible_text(text)
            for term in self.BANNED_VISIBLE:
                if term in visible:
                    visible_hits.append((str(tpl), term))
        if visible_hits:
            for tpl, term in visible_hits[:40]:
                errors.append(f"Termo técnico visível em {tpl}: {term}")
            if len(visible_hits) > 40:
                errors.append(f"... mais {len(visible_hits)-40} ocorrências visíveis")

        href_jump = []
        for tpl in Path("templates").rglob("*.html"):
            text = tpl.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"href=['\"]\s*#\s*['\"]", text):
                href_jump.append(str(tpl))
        if href_jump:
            warnings.append(f"Links # restantes: {len(href_jump)}")

        self.stdout.write(f"CSS_ATIVOS={len(css_files)}")
        self.stdout.write(f"JS_ATIVOS={len(js_files)}")
        self.stdout.write(f"PYCACHE={len(pycache)}")
        self.stdout.write(f"PYC={len(pyc)}")
        self.stdout.write(f"TERMOS_TECNICOS_VISIVEIS={len(visible_hits)}")
        self.stdout.write(f"LINKS_HASH={len(href_jump)}")

        for w in warnings:
            self.stdout.write(self.style.WARNING(w))
        for e in errors:
            self.stdout.write(self.style.ERROR(e))

        if errors and options.get("strict"):
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("Polimento final 1341–1360 validado."))

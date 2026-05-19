from __future__ import annotations

import re
import traceback
from collections import Counter

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from apps.academico.models import Aluno, Disciplina, DocumentoGerado, HorarioAula, NotificacaoGestao, ProfessorTurmaDisciplina, Turma


class Command(BaseCommand):
    help = "Mega checkup seguro: resolve URLs do projeto e testa GET nas rotas críticas sem travar em telas antigas pesadas."

    CRITICAL_NAMES = {
        "healthz",
        "dashboard_gestao",
        "dashboard_professor_home",
        "gestao_escola",
        "gestao_professores",
        "gestao_alunos",
        "gestao_cadastros_operacionais_301",
        "gestao_carga_horaria_professores_301",
        "gestao_horarios",
        "gestao_diario_oficial",
        "gestao_diario_classe_oficial_1281",
        "gestao_checkup_etapas_1281_1340",
        "gestao_ficha_aluno_oficial",
        "diario_oficial_turma_completo",
        "frequencia_mensal_turma",
        "registro_aulas_mensal_turma",
        "professor_diario_oficial",
        "professor_diario_classe_oficial_1281",
        "professor_aula_rapida_321_horario",
        "professor_centro_operacional_321",
        "professor_fechamento_mensal_901",
        "professor_ia_pedagogica_901",
        "gestao_render_ready_1081",
        "professor_render_ready_1081",
    }

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Falha se encontrar erro crítico.")
        parser.add_argument("--show-skipped", action="store_true", help="Lista rotas ignoradas por falta de dados reais.")

    def _iter_patterns(self, patterns):
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                yield pattern
            elif isinstance(pattern, URLResolver):
                if str(pattern.pattern).startswith("admin/"):
                    continue
                yield from self._iter_patterns(pattern.url_patterns)

    def _pick_users_and_samples(self):
        User = get_user_model()
        vinculo = ProfessorTurmaDisciplina.objects.filter(ativo=True).select_related("turma", "disciplina", "professor").first()
        professor = vinculo.professor if vinculo else User.objects.filter(tipo="PROF").first()
        gestor = User.objects.filter(tipo__in=["ADMIN", "COORD", "SEC"]).first() or User.objects.exclude(tipo="PROF").first() or User.objects.first()
        aluno_do_vinculo = Aluno.objects.filter(turma=vinculo.turma, ativo=True).first() if vinculo else None
        horario_do_vinculo = None
        if vinculo:
            horario_do_vinculo = HorarioAula.objects.filter(professor=vinculo.professor, turma=vinculo.turma, ativo=True).first()
        sample = {
            "turma_id": getattr(vinculo.turma if vinculo else Turma.objects.first(), "id", None),
            "aluno_id": getattr(aluno_do_vinculo or Aluno.objects.filter(ativo=True).first(), "id", None),
            "disciplina_id": getattr(vinculo.disciplina if vinculo else Disciplina.objects.first(), "id", None),
            "horario_id": getattr(horario_do_vinculo or HorarioAula.objects.first(), "id", None),
            "notificacao_id": NotificacaoGestao.objects.values_list("id", flat=True).first(),
            "documento_id": DocumentoGerado.objects.values_list("id", flat=True).first(),
            "ano": 2026,
            "mes": 5,
        }
        return gestor, professor, sample

    def handle(self, *args, **options):
        gestor, professor, sample = self._pick_users_and_samples()
        resolved = []
        tested = []
        errors = []
        skipped = []

        cg, cp = Client(), Client()
        if gestor:
            cg.force_login(gestor)
        if professor:
            cp.force_login(professor)

        for pattern in self._iter_patterns(get_resolver().url_patterns):
            if not pattern.name or ":" in str(pattern.name):
                continue
            pat = str(pattern.pattern)
            kwargs = {}
            skip = False
            for match in re.finditer(r"<(?:[^:>]+:)?([^>]+)>", pat):
                key = match.group(1)
                value = sample.get(key)
                if value is None:
                    skipped.append((pattern.name, f"sem amostra válida para {key}"))
                    skip = True
                    break
                kwargs[key] = value
            if skip:
                continue
            try:
                url = reverse(pattern.name, kwargs=kwargs) if kwargs else reverse(pattern.name)
                resolved.append((pattern.name, url))
            except Exception as exc:
                skipped.append((pattern.name, f"reverse ignorado: {exc}"))
                continue

            if pattern.name not in self.CRITICAL_NAMES:
                continue
            client = cp if (pat.startswith("professor/") or str(pattern.name).startswith("professor_")) else cg
            try:
                response = client.get(url, follow=False)
                tested.append((pattern.name, url, response.status_code))
                if response.status_code >= 500 or response.status_code == 404:
                    errors.append((pattern.name, url, f"status {response.status_code}"))
            except Exception:
                errors.append((pattern.name, url, traceback.format_exc().splitlines()[-8:]))

        status = Counter(code for _, _, code in tested)
        self.stdout.write(f"ROTAS_RESOLVIDAS={len(resolved)}")
        self.stdout.write(f"ROTAS_CRITICAS_TESTADAS={len(tested)}")
        self.stdout.write(f"STATUS={dict(status)}")
        self.stdout.write(f"IGNORADAS={len(skipped)}")
        self.stdout.write(f"ERROS={len(errors)}")
        if skipped and options.get("show_skipped"):
            for name, reason in skipped[:80]:
                self.stdout.write(self.style.WARNING(f"IGNORADA {name}: {reason}"))
        for name, url, err in errors[:30]:
            self.stdout.write(self.style.ERROR(f"ERRO {name} {url}: {err}"))
        if errors and options["strict"]:
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("Mega checkup concluído."))

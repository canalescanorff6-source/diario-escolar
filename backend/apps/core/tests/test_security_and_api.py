import json
from datetime import time

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.academico.models import (
    Aluno,
    AnoLetivo,
    ConteudoAula,
    Disciplina,
    Frequencia,
    HorarioAula,
    ProfessorTurmaDisciplina,
    Turma,
)


class BaseSchoolTest(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.professor = User.objects.create_user(
            username="professor_a",
            password="SenhaForte!2026",
            tipo="PROF",
            first_name="Professor",
        )
        self.outro_professor = User.objects.create_user(
            username="professor_b",
            password="OutraSenha!2026",
            tipo="PROF",
        )
        self.gestor = User.objects.create_user(
            username="gestor_a",
            password="GestaoForte!2026",
            tipo="ADMIN",
        )
        self.ano = AnoLetivo.objects.create(ano=2026, ativo=True)
        self.disciplina = Disciplina.objects.create(nome="Matemática")
        self.turma = Turma.objects.create(nome="8º A", ano_letivo=self.ano, ativa=True)
        self.turma_alheia = Turma.objects.create(nome="9º B", ano_letivo=self.ano, ativa=True)
        self.aluno = Aluno.objects.create(nome="Ana", matricula="A001", turma=self.turma)
        self.aluno_alheio = Aluno.objects.create(nome="Bruno", matricula="B001", turma=self.turma_alheia)
        self.vinculo = ProfessorTurmaDisciplina.objects.create(
            professor=self.professor,
            turma=self.turma,
            disciplina=self.disciplina,
            ano_letivo=self.ano,
            ativo=True,
        )
        self.horario = HorarioAula.objects.create(
            professor=self.professor,
            turma=self.turma,
            disciplina=self.disciplina,
            dia_semana=1,
            ordem=1,
            horario_numero=1,
            hora_inicio=time(8, 0),
            hora_fim=time(8, 50),
            turno="MATUTINO",
            ativo=True,
        )


class ProfessorPermissionsTests(BaseSchoolTest):
    def test_professor_nao_acessa_turma_sem_vinculo(self):
        client = Client()
        client.force_login(self.professor)
        response = client.get(reverse("turma_detalhe", args=[self.turma_alheia.id]))
        self.assertTemplateUsed(response, "core/acesso_negado.html")

    def test_professor_nao_acessa_boletim_de_aluno_de_outra_turma(self):
        client = Client()
        client.force_login(self.professor)
        response = client.get(reverse("boletim_aluno", args=[self.aluno_alheio.id]))
        self.assertTemplateUsed(response, "core/acesso_negado.html")

    def test_professor_acessa_turma_vinculada(self):
        client = Client()
        client.force_login(self.professor)
        response = client.get(reverse("turma_detalhe", args=[self.turma.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/turma_detalhe.html")


class MobileApiTests(BaseSchoolTest):
    def _login_token(self):
        response = self.client.post(
            reverse("api:login"),
            data=json.dumps({"username": "professor_a", "password": "SenhaForte!2026"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["token"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_app_rejeita_conta_de_gestao(self):
        response = self.client.post(
            reverse("api:login"),
            data=json.dumps({"username": "gestor_a", "password": "GestaoForte!2026"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "professor_only")

    def test_api_bloqueia_turma_nao_vinculada(self):
        token = self._login_token()
        response = self.client.get(
            reverse("api:professor_turma_alunos", args=[self.turma_alheia.id]),
            **self._auth(token),
        )
        self.assertEqual(response.status_code, 403)

    def test_registro_de_aula_cria_frequencia_e_conteudo(self):
        token = self._login_token()
        payload = {
            "turma_id": self.turma.id,
            "disciplina_id": self.disciplina.id,
            "horario_id": self.horario.id,
            "data": "2026-08-21",
            "aula_numero": 1,
            "conteudo": "Frações e equivalência",
            "observacoes": "Atividade orientada",
            "frequencias": [{"aluno_id": self.aluno.id, "status": "P"}],
        }
        response = self.client.post(
            reverse("api:professor_registrar_aula"),
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(token),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Frequencia.objects.filter(aluno=self.aluno, aula_numero=1, status="P").exists())
        self.assertTrue(ConteudoAula.objects.filter(turma=self.turma, aula_numero=1).exists())

    def test_duas_aulas_mesma_disciplina_no_mesmo_dia_nao_colidem(self):
        token = self._login_token()
        for numero in (1, 2):
            payload = {
                "turma_id": self.turma.id,
                "disciplina_id": self.disciplina.id,
                "data": "2026-08-21",
                "aula_numero": numero,
                "conteudo": f"Conteúdo {numero}",
                "frequencias": [{"aluno_id": self.aluno.id, "status": "P"}],
            }
            response = self.client.post(
                reverse("api:professor_registrar_aula"),
                data=json.dumps(payload),
                content_type="application/json",
                **self._auth(token),
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Frequencia.objects.filter(aluno=self.aluno, data="2026-08-21").count(), 2)
        self.assertEqual(ConteudoAula.objects.filter(turma=self.turma, data="2026-08-21").count(), 2)

    def test_api_rejeita_aluno_de_outra_turma(self):
        token = self._login_token()
        payload = {
            "turma_id": self.turma.id,
            "disciplina_id": self.disciplina.id,
            "data": "2026-08-21",
            "aula_numero": 1,
            "frequencias": [{"aluno_id": self.aluno_alheio.id, "status": "P"}],
        }
        response = self.client.post(
            reverse("api:professor_registrar_aula"),
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(token),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_student")
    @override_settings(MOBILE_LOGIN_MAX_ATTEMPTS=2, MOBILE_LOGIN_WINDOW_SECONDS=300)
    def test_login_mobile_aplica_limite_de_tentativas(self):
        for _ in range(2):
            response = self.client.post(
                reverse("api:login"),
                data=json.dumps({"username": "professor_a", "password": "senha-errada"}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 401)
        response = self.client.post(
            reverse("api:login"),
            data=json.dumps({"username": "professor_a", "password": "senha-errada"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"], "rate_limited")


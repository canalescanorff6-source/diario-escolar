from django.urls import path
from . import api

app_name = "api"

urlpatterns = [
    path("auth/login/", api.api_login, name="login"),
    path("auth/logout/", api.api_logout, name="logout"),
    path("me/", api.api_me, name="me"),
    path("professor/aulas-hoje/", api.api_professor_aulas_hoje, name="professor_aulas_hoje"),
    path("professor/turmas/", api.api_professor_turmas, name="professor_turmas"),
    path("professor/turmas/<int:turma_id>/alunos/", api.api_professor_turma_alunos, name="professor_turma_alunos"),
    path("professor/aulas/registrar/", api.api_professor_registrar_aula, name="professor_registrar_aula"),
    path("professor/bootstrap/", api.api_professor_bootstrap, name="professor_bootstrap"),
]

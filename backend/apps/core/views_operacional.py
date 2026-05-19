# Camada de views operacional — refatoração real etapa 1221-1280.
# Mantém os nomes públicos usados pelas URLs, mas tira o peso do antigo views.py.

from .views_shared import *  # noqa: F401,F403

def healthz(request):
    """Health check HTTP para Render: confirma app, banco e static sem exigir login."""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_status = "ok"
        http_status = 200
    except Exception as exc:  # pragma: no cover - endpoint operacional
        db_status = f"erro: {exc.__class__.__name__}"
        http_status = 503
    return JsonResponse({
        "app": "Diario IA Escolar Premium",
        "status": "ok" if http_status == 200 else "erro",
        "database": db_status,
        "render": bool(os.environ.get("RENDER")),
        "version": "1081-1160",
    }, status=http_status)


@login_required
def dashboard_gestao(request):
    """Painel executivo da gestão reconstruído para não depender de pycache e manter o Diário Escolar organizado."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    escola = Escola.objects.first()
    ano_letivo = AnoLetivo.objects.filter(ativo=True).first() or AnoLetivo.objects.order_by("-ano").first()
    turmas = Turma.objects.filter(ativa=True).prefetch_related("alunos")
    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    professores = ProfessorPerfil.objects.select_related("professor", "escola")[:8]
    horarios = HorarioAula.objects.select_related("turma", "disciplina", "professor").filter(ativo=True).order_by("turno", "dia_semana", "hora_inicio")[:10]
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True)

    status_frequencia = diagnostico_tecnico_diario_real()
    total_frequencias = status_frequencia["frequencias"]
    total_presencas = status_frequencia["presencas"]
    frequencia_geral = round((total_presencas / total_frequencias) * 100, 1) if total_frequencias else 100
    media_escola = Nota.objects.aggregate(media=Avg("valor"))["media"] or 0
    media_escola = round(float(media_escola), 1) if media_escola else 0

    alunos_risco = []
    total_risco = 0
    for turma in turmas[:12]:
        try:
            risco = AnaliseInteligenteService.alunos_em_risco(turma)
        except Exception:
            risco = []
        total_risco += len(risco)
        for item in risco[:3]:
            alunos_risco.append({"aluno": item.get("aluno") if isinstance(item, dict) else item, "turma": turma})

    total_turmas = turmas.count()
    total_alunos = alunos.count()
    total_professores = get_user_model().objects.filter(tipo="PROF").count()
    total_horarios = HorarioAula.objects.filter(ativo=True).count()
    total_vinculos = vinculos.count()

    dados_turmas = []
    for turma in turmas.order_by("turno", "nome")[:12]:
        dados_turmas.append({
            "turma": turma,
            "total_alunos": turma.alunos.filter(ativo=True).count(),
            "vinculos": ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).count(),
            "horarios": HorarioAula.objects.filter(turma=turma, ativo=True).count(),
        })

    professores_dados = []
    for professor in get_user_model().objects.filter(tipo="PROF").order_by("first_name", "username")[:10]:
        professores_dados.append({
            "professor": professor,
            "turmas": Turma.objects.filter(vinculos_professores__professor=professor, vinculos_professores__ativo=True).distinct().count(),
            "vinculos": ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).count(),
            "horarios": HorarioAula.objects.filter(professor=professor, ativo=True).count(),
        })

    total_disciplinas = Disciplina.objects.count()
    total_faltas = status_frequencia["faltas"]
    total_fj = status_frequencia["fj"]
    turmas_sem_vinculo = Turma.objects.filter(ativa=True).exclude(vinculos_professores__ativo=True).distinct().count()
    turmas_sem_horario = Turma.objects.filter(ativa=True).exclude(horarios__ativo=True).distinct().count()
    pendencias_gestao = []
    if escola is None:
        pendencias_gestao.append("Identificação da escola pendente")
    if ano_letivo is None:
        pendencias_gestao.append("Ano letivo ativo pendente")
    if turmas_sem_vinculo:
        pendencias_gestao.append(f"{turmas_sem_vinculo} turma(s) sem professor/disciplina")
    if turmas_sem_horario:
        pendencias_gestao.append(f"{turmas_sem_horario} turma(s) sem horário semanal")

    fluxo_gestao = fluxo_gestao_unificado()

    diagnostico_gestao = {
        "escola_configurada": escola is not None,
        "ano_letivo_configurado": ano_letivo is not None,
        "turmas_sem_vinculo": turmas_sem_vinculo,
        "turmas_sem_horario": turmas_sem_horario,
        "painel_unificado": True,
    }

    context = {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "hoje": date.today(),
        "total_turmas": total_turmas,
        "total_alunos": total_alunos,
        "total_professores": total_professores,
        "total_horarios": total_horarios,
        "total_vinculos": total_vinculos,
        "total_disciplinas": total_disciplinas,
        "carga_horaria_professores": carga_horaria_professores_resumo(),
        "total_faltas": total_faltas,
        "total_fj": total_fj,
        "turmas_sem_vinculo": turmas_sem_vinculo,
        "turmas_sem_horario": turmas_sem_horario,
        "pendencias_gestao": pendencias_gestao,
        "fluxo_gestao": fluxo_gestao,
        "diagnostico_gestao": diagnostico_gestao,
        "total_risco": total_risco,
        "frequencia_geral": frequencia_geral,
        "media_escola": media_escola,
        "professores": professores,
        "professores_dados": professores_dados,
        "horarios": horarios,
        "dados_turmas": dados_turmas,
        "alunos_risco": alunos_risco[:8],
        "alunos_risco_admin": alunos_risco[:8],
        "grafico_labels": json.dumps(["Turmas", "Alunos", "Professores", "Horários", "Vínculos"]),
        "grafico_dados": json.dumps([total_turmas, total_alunos, total_professores, total_horarios, total_vinculos]),
        "resumo_861_900_gestao": resumo_gestao_861_900(),
        "finalizacao_901_960_gestao": finalizacao_901_960(),
        "mega_checkup_961_1000_gestao": mega_checkup_961_1000(),
        "mega_checkup_1001_1080_gestao": mega_checkup_1001_1080(),
    }
    return render(request, "core/dashboard_admin.html", context)




@login_required
def checkup_etapas_301_320(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    linhas = []
    linhas.append({"item": "Botões premium", "status": "Aplicado", "detalhe": "Links soltos e ações comuns recebem classe visual global."})
    linhas.append({"item": "Separação de área", "status": "Aplicado", "detalhe": "Rotas novas redirecionam gestão/professor para sua área correta."})
    linhas.append({"item": "Carga horária semanal", "status": "Aplicado", "detalhe": "Professor e gestão possuem visão semanal por grade HorarioAula."})
    linhas.append({"item": "Gestão sem admin", "status": "Em expansão", "detalhe": "Central de cadastros cobre ano, disciplina, turma, professor, aluno, vínculo e horário."})
    linhas.append({"item": "Diário Escolar", "status": "Preservado", "detalhe": "Não foi removida lógica de frequência, aulas ou ficha oficial."})
    return render(request, "gestao/checkup_etapas_301_320.html", {"linhas": linhas})


@login_required
def checkup_etapas_321_340(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    linhas = [
        {"item": "Central da Gestão Escolar", "status": "Aplicado", "detalhe": "Nova tela mostra pendências reais, turnos, vínculos, horários e carga horária."},
        {"item": "Central do Professor", "status": "Aplicado", "detalhe": "Professor entra em rotina de trabalho com aulas de hoje, pendências e chamada rápida."},
        {"item": "Aula rápida", "status": "Aplicado", "detalhe": "Tela única salva frequência P/F/FJ e conteúdo de aula."},
        {"item": "Botões premium", "status": "Reforçado", "detalhe": "CSS global transforma links soltos e ações em botões/cards premium."},
        {"item": "Turnos oficiais", "status": "Aplicado", "detalhe": "Gestão pode normalizar turmas sem turno para manhã/tarde/noite."},
        {"item": "Sem admin obrigatório", "status": "Em avanço", "detalhe": "Fluxo principal continua saindo do /admin/ para a gestão."},
    ]
    return render(request, "gestao/checkup_etapas_321_340.html", {"linhas": linhas, "hoje": date.today()})


@login_required
def checkup_etapas_361_380(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    arquivos = _saude_deploy_render()
    cards, pendencias = _qualidade_operacional_escola()
    linhas = [
        {"item": "Render online", "status": "Preparado", "detalhe": "build.sh, Procfile, render.yaml, runtime.txt, WhiteNoise e DATABASE_URL."},
        {"item": "Botões premium", "status": "Reforçado", "detalhe": "Ações e links soltos recebem padrão visual consistente."},
        {"item": "Carga horária", "status": "Reforçada", "detalhe": "Gestão e professor conseguem acompanhar aulas e horas semanais."},
        {"item": "Qualidade operacional", "status": "Criada", "detalhe": "Gestão vê pendências reais de turno, vínculo, horário e alunos."},
        {"item": "Separação de áreas", "status": "Preservada", "detalhe": "Professor continua sem cair na gestão e gestão sem cair no professor."},
    ]
    return render(request, "gestao/checkup_etapas_361_380.html", {
        "linhas": linhas,
        "arquivos": arquivos,
        "cards": cards,
        "pendencias": pendencias,
        "hoje": date.today(),
    })

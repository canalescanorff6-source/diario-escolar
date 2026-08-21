"""Views operacionais e painel da gestão."""

from .views_shared import *  # noqa: F401,F403



def media_arquivo(request, path):
    """Entrega mídia local sem expor fotos de alunos/professores anonimamente.

    Brasões/logos em ``escolas/`` podem aparecer na tela pública de login.
    Fotos pessoais exigem sessão e autorização sobre o registro correspondente.
    """
    from django.http import FileResponse, Http404

    relativo = Path(str(path or ""))
    if relativo.is_absolute() or ".." in relativo.parts:
        raise Http404

    raiz = Path(settings.MEDIA_ROOT).resolve()
    arquivo = (raiz / relativo).resolve()
    try:
        arquivo.relative_to(raiz)
    except ValueError as exc:
        raise Http404 from exc
    if not arquivo.is_file():
        raise Http404

    caminho = relativo.as_posix()
    if caminho.startswith("escolas/"):
        return FileResponse(open(arquivo, "rb"))

    if not getattr(request.user, "is_authenticated", False):
        raise Http404

    if caminho.startswith("alunos/"):
        aluno = Aluno.objects.select_related("turma").filter(foto=caminho).first()
        if not aluno or not (usuario_gestor(request.user) or _usuario_pode_ver_turma(request.user, aluno.turma)):
            raise Http404
    elif caminho.startswith("professores/"):
        Usuario = get_user_model()
        dono = Usuario.objects.filter(foto=caminho).first()
        if not dono or not (usuario_gestor(request.user) or dono.pk == request.user.pk):
            raise Http404
    elif not usuario_gestor(request.user):
        raise Http404

    response = FileResponse(open(arquivo, "rb"))
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response

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
        "app": "Diário Escolar Pro",
        "status": "ok" if http_status == 200 else "erro",
        "database": db_status,
        "render": bool(os.environ.get("RENDER")),
        "version": "2.0",
    }, status=http_status)


def service_worker(request):
    """Entrega o service worker no escopo raiz sem armazenar páginas autenticadas em cache."""
    from django.contrib.staticfiles import finders
    from django.http import FileResponse, HttpResponse

    caminho = finders.find("js/service-worker.js")
    if not caminho:
        return HttpResponse("// service worker indisponível", content_type="application/javascript", status=404)
    response = FileResponse(open(caminho, "rb"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


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

    frequencias_qs = Frequencia.objects.all()
    total_frequencias = frequencias_qs.count()
    total_presencas = frequencias_qs.filter(status="P").count()
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
    total_faltas = frequencias_qs.filter(status="F").count()
    total_fj = frequencias_qs.filter(status="FJ").count()
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

    context = {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "hoje": date.today(),
        "total_turmas": total_turmas,
        "total_alunos": total_alunos,
        "total_professores": total_professores,
        "total_horarios": total_horarios,
        "total_faltas": total_faltas,
        "total_fj": total_fj,
        "pendencias_gestao": pendencias_gestao,
        "total_risco": total_risco,
        "frequencia_geral": frequencia_geral,
        "media_escola": media_escola,
        "professores_dados": professores_dados,
        "dados_turmas": dados_turmas,
        "alunos_risco_admin": alunos_risco[:8],
    }
    return render(request, "core/dashboard_admin.html", context)



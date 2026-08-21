"""Views da área do professor."""

from .views_shared import *  # noqa: F401,F403

@login_required
def dashboard_professor(request):

    if usuario_gestor(request.user):
        return redirect("dashboard_gestao")

    if request.user.tipo != "PROF":
        return render(request, "core/acesso_negado.html")

    professor = request.user

    vinculos = ProfessorTurmaDisciplina.objects.select_related(
        "turma",
        "disciplina",
        "ano_letivo",
    ).filter(
        professor=professor,
        ativo=True,
    )

    turmas = turmas_do_professor(professor).prefetch_related("alunos")

    if not turmas.exists():
        turmas = Turma.objects.none()

    disciplinas = disciplinas_do_professor(professor)
    horarios = horarios_do_professor(professor)

    dados_turmas = []
    total_alunos = 0
    total_risco = 0
    total_faltas = 0
    soma_media = 0

    for turma in turmas:
        resumo = AnaliseInteligenteService.resumo_turma(turma)
        risco = AnaliseInteligenteService.alunos_em_risco(turma)
        total_alunos += resumo.get("total_alunos", 0)
        total_faltas += resumo.get("total_faltas", 0)
        soma_media += resumo.get("media_geral", 0)
        total_risco += len(risco)
        dados_turmas.append({
            "turma": turma,
            "resumo": resumo,
            "alunos_risco": risco,
            "disciplinas": vinculos.filter(turma=turma).count(),
            "horarios": horarios.filter(turma=turma).count(),
        })

    total_turmas = turmas.count()
    media_geral = round(soma_media / total_turmas, 1) if total_turmas else 0

    total_registros_frequencia = Frequencia.objects.filter(turma__in=turmas).count()
    total_presencas = Frequencia.objects.filter(turma__in=turmas, status="P").count()
    total_fj = Frequencia.objects.filter(turma__in=turmas, status="FJ").count()
    total_faltas_oficiais = Frequencia.objects.filter(turma__in=turmas, status="F").count() + total_fj
    frequencia_media = 100
    if total_registros_frequencia > 0:
        frequencia_media = round((total_presencas / total_registros_frequencia) * 100, 1)

    total_aulas_registradas = ConteudoAula.objects.filter(
        professor=professor,
        turma__in=turmas,
    ).count()

    pendencias_professor = []
    if not total_turmas:
        pendencias_professor.append("Nenhuma turma vinculada pela gestão")
    if not disciplinas.exists():
        pendencias_professor.append("Nenhuma disciplina vinculada")
    if not horarios.exists():
        pendencias_professor.append("Horários semanais ainda não cadastrados")
    if total_turmas and total_aulas_registradas == 0:
        pendencias_professor.append("Registro mensal de aulas ainda vazio")

    context = {
        "dados_turmas": dados_turmas,
        "total_turmas": total_turmas,
        "total_risco": total_risco,
        "frequencia_media": frequencia_media,
        "total_fj": total_fj,
        "total_aulas_registradas": total_aulas_registradas,
        "carga_horaria_semana": carga_horaria_professor_semana(professor),
        "aulas_hoje": aulas_professor_hoje(professor),
        "pendencias_professor": pendencias_professor,
        "hoje": date.today(),
    }

    return render(request, "core/dashboard_professor.html", context)


# =====================================================
# TURMAS
# =====================================================

@login_required
def turmas(request):

    if request.user.tipo != "PROF":
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.filter(
        vinculos_professores__professor=request.user,
        vinculos_professores__ativo=True,
    ).distinct().prefetch_related(
        "alunos"
    )

    context = {

        "turmas": turmas,

        "total_turmas": turmas.count(),

    }

    return render(
        request,
        "core/turmas.html",
        context
    )


# =====================================================
# DETALHE DA TURMA
# =====================================================

@login_required
def turma_detalhe(request, turma_id):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(Turma.objects.prefetch_related("alunos"), id=turma_id)
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")

    alunos = turma.alunos.filter(ativo=True).order_by("nome")
    frequencias_turma = Frequencia.objects.filter(turma=turma)
    total_frequencias = frequencias_turma.count()
    total_presencas = frequencias_turma.filter(status="P").count()
    frequencia_media = round((total_presencas / total_frequencias) * 100, 1) if total_frequencias else None

    regras = obter_regras_academicas()
    alunos_formatados = []
    medias_validas = []
    for aluno in alunos:
        indicadores = _indicadores_aluno(aluno)
        if indicadores["media"] is not None:
            medias_validas.append(indicadores["media"])
        alunos_formatados.append({
            "obj": aluno,
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula,
            "frequencia": indicadores["frequencia"],
            "media": indicadores["media"],
            "status": indicadores["situacao"],
        })

    context = {
        "turma": turma,
        "alunos": alunos_formatados,
        "frequencia_media": frequencia_media,
        "media_geral": round(sum(medias_validas) / len(medias_validas), 1) if medias_validas else None,
        "total_alunos": alunos.count(),
        "regras": regras,
    }
    return render(request, "core/turma_detalhe.html", context)


# =====================================================
# NOTAS TURMA
# =====================================================

@login_required
def notas_turma(request, turma_id):
    if not (usuario_professor(request.user) or usuario_gestor(request.user)):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(Turma.objects.prefetch_related("alunos"), id=turma_id)
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")

    if usuario_professor(request.user):
        disciplinas = Disciplina.objects.filter(
            vinculos_professores__professor=request.user,
            vinculos_professores__turma=turma,
            vinculos_professores__ativo=True,
        ).distinct().order_by("nome")
    else:
        disciplinas = Disciplina.objects.filter(
            vinculos_professores__turma=turma,
            vinculos_professores__ativo=True,
        ).distinct().order_by("nome")
        if not disciplinas.exists():
            disciplinas = Disciplina.objects.all().order_by("nome")

    disciplina_id = request.POST.get("disciplina") or request.GET.get("disciplina")
    disciplina = disciplinas.filter(id=disciplina_id).first() if disciplina_id else disciplinas.first()
    alunos = turma.alunos.filter(ativo=True).order_by("nome")
    regras = obter_regras_academicas()

    if disciplina is None:
        messages.warning(request, "Nenhuma disciplina vinculada a esta turma. A gestão deve criar o vínculo antes de lançar notas.")
        return render(request, "core/notas_turma.html", {
            "turma": turma, "alunos": [], "disciplinas": disciplinas, "disciplina": None,
            "bimestre_atual": 1, "progresso_bimestres": [], "total_alunos": alunos.count(),
            "media_geral": None, "regras": regras,
        })

    def decimal_ou_none(valor):
        if valor in (None, ""):
            return None
        try:
            numero = Decimal(str(valor).replace(",", "."))
        except (InvalidOperation, ValueError):
            return None
        return max(Decimal("0"), min(Decimal("10"), numero))

    def bimestre_completo(numero_bimestre):
        if not alunos.exists():
            return False
        completos = Nota.objects.filter(
            turma=turma, disciplina=disciplina, bimestre=numero_bimestre,
            nota1__isnull=False, nota2__isnull=False, nota3__isnull=False,
        ).count()
        return completos == alunos.count()

    if request.method == "POST":
        try:
            bimestre = int(request.POST.get("bimestre", 1))
        except (TypeError, ValueError):
            bimestre = 1
        bimestre = max(1, min(4, bimestre))

        for aluno in alunos:
            nota1 = decimal_ou_none(request.POST.get(f"nota1_{aluno.id}"))
            nota2 = decimal_ou_none(request.POST.get(f"nota2_{aluno.id}"))
            nota3 = decimal_ou_none(request.POST.get(f"nota3_{aluno.id}"))
            if nota1 is None and nota2 is None and nota3 is None:
                continue
            Nota.objects.update_or_create(
                aluno=aluno, disciplina=disciplina, bimestre=bimestre,
                defaults={"turma": turma, "nota1": nota1, "nota2": nota2, "nota3": nota3},
            )
        messages.success(request, "Notas salvas com sucesso.")
        return redirect(f"{request.path}?disciplina={disciplina.id}&bimestre={bimestre}")

    bimestre_get = request.GET.get("bimestre")
    bimestre_atual = int(bimestre_get) if bimestre_get in {"1", "2", "3", "4"} else next(
        (n for n in (1, 2, 3, 4) if not bimestre_completo(n)), 4
    )

    notas_do_bimestre = {
        nota.aluno_id: nota
        for nota in Nota.objects.filter(turma=turma, disciplina=disciplina, bimestre=bimestre_atual)
    }
    progresso_bimestres = []
    for numero in (1, 2, 3, 4):
        total_completos = Nota.objects.filter(
            turma=turma, disciplina=disciplina, bimestre=numero,
            nota1__isnull=False, nota2__isnull=False, nota3__isnull=False,
        ).count()
        progresso_bimestres.append({
            "numero": numero, "label": f"{numero}º Bimestre", "total": alunos.count(),
            "preenchidos": total_completos, "completo": alunos.exists() and total_completos == alunos.count(),
            "ativo": numero == bimestre_atual,
        })

    alunos_notas = []
    medias = []
    alunos_completos = 0
    for aluno in alunos:
        nota = notas_do_bimestre.get(aluno.id)
        media = nota.calcular_media() if nota else None
        completo = media is not None
        if completo:
            alunos_completos += 1
            medias.append(media)
            if media >= regras.media_aprovacao:
                status, status_classe = "Aprovado", "status-aprovado"
            elif media >= (regras.media_aprovacao - Decimal("1.00")):
                status, status_classe = "Atenção", "status-atencao"
            else:
                status, status_classe = "Recuperação", "status-risco"
        else:
            status, status_classe = "Pendente", "status-pendente"
        alunos_notas.append({
            "obj": aluno, "id": aluno.id, "nome": aluno.nome,
            "nota1": nota.nota1 if nota else "", "nota2": nota.nota2 if nota else "", "nota3": nota.nota3 if nota else "",
            "media": media if media is not None else "", "completo": completo, "status": status, "status_classe": status_classe,
        })

    context = {
        "turma": turma, "alunos": alunos_notas, "disciplinas": disciplinas, "disciplina": disciplina,
        "bimestre_atual": bimestre_atual, "progresso_bimestres": progresso_bimestres,
        "alunos_completos": alunos_completos, "total_alunos": alunos.count(),
        "media_geral": round(sum(medias) / len(medias), 2) if medias else None,
        "todos_bimestres_completos": all(item["completo"] for item in progresso_bimestres) if alunos.exists() else False,
        "regras": regras,
    }
    return render(request, "core/notas_turma.html", context)


@login_required
def dashboard_professor_home(request):
    """Alias oficial do painel do professor, preservando rota /professor/."""
    return dashboard_professor(request)


@login_required
def professor_plano_intervencao(request):
    """Plano de intervenção para o professor, sem misturar recursos administrativos."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina")
    turmas_ids = list(vinculos.values_list("turma_id", flat=True).distinct())
    alunos = Aluno.objects.filter(turma_id__in=turmas_ids, ativo=True).select_related("turma")
    regras = obter_regras_academicas()
    planos = []
    for aluno in alunos:
        diag = _diagnostico_recuperacao(aluno)
        if diag["media"] < float(regras.media_aprovacao) or diag["faltas"] >= 10 or diag["disciplinas"]:
            planos.append({
                "aluno": aluno,
                **diag,
                "intervencao": [
                    "retomar habilidades essenciais em pequenos blocos",
                    "registrar acompanhamento semanal no diário",
                    "usar atividades curtas de recomposição e devolutiva individual",
                ],
            })

    return render(request, "core/professor_plano_intervencao.html", {
        "hoje": date.today(),
        "vinculos": vinculos,
        "planos": planos,
        "total_planos": len(planos),
        "total_turmas": len(turmas_ids),
    })


@login_required
def professor_alunos(request):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas_qs = _turmas_do_professor(request.user)
    alunos = Aluno.objects.filter(turma__in=turmas_qs, ativo=True).select_related("turma").order_by("turma__nome", "nome")

    return render(request, "core/professor_alunos.html", {
        "hoje": date.today(),
        "turmas": turmas_qs,
        "alunos": alunos,
        "total_alunos": alunos.count(),
    })


@login_required
def professor_configuracoes(request):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    if request.method == "POST":
        if request.FILES.get("foto"):
            request.user.foto = request.FILES["foto"]
            request.user.save(update_fields=["foto"])
            messages.success(request, "Sua imagem foi atualizada com sucesso.")
        elif request.POST.get("remover_foto") == "1":
            request.user.foto.delete(save=False)
            request.user.foto = None
            request.user.save(update_fields=["foto"])
            messages.success(request, "Sua imagem foi removida.")
        else:
            messages.info(request, "Escolha uma imagem para atualizar seu perfil.")
        return redirect("professor_configuracoes")

    return render(request, "core/professor_configuracoes.html", {
        "hoje": date.today(),
    })


@login_required
def professor_meus_horarios_reais(request):
    """Grade semanal do professor vinda do cadastro da gestão/admin."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    horarios = HorarioAula.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina").order_by("dia_semana", "ordem", "hora_inicio")
    dias = []
    for valor, nome in HorarioAula.DIAS_SEMANA:
        dias.append({"nome": nome, "horarios": horarios.filter(dia_semana=valor)})
    return render(request, "core/professor_meus_horarios_reais.html", {
        "dias": dias,
        "total": horarios.count(),
        "hoje": date.today(),
    })


@login_required
def professor_consolidado_mensal(request):
    """Professor vê somente suas turmas/disciplinas no mês, com atalhos para frequência e registro de aulas."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    turmas = _turmas_visiveis_para_usuario(request.user)
    linhas = []
    for turma in turmas:
        disciplinas, vinculos = _disciplinas_vinculadas_por_turma_professor(turma, request.user)
        blocos = [_linha_consolidado_mensal(turma, disciplina, inicio, fim, request.user) for disciplina in disciplinas]
        linhas.append({"turma": turma, "vinculos": vinculos, "disciplinas": blocos, "total_alunos": turma.alunos.filter(ativo=True).count()})
    return render(request, "core/professor_consolidado_mensal.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "linhas": linhas,
        "professor": request.user,
        "hoje": date.today(),
    })



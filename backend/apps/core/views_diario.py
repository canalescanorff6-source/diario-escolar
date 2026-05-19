# Camada de views diario — refatoração real etapa 1221-1280.
# Mantém os nomes públicos usados pelas URLs, mas tira o peso do antigo views.py.

from .views_shared import *  # noqa: F401,F403

# =====================================================
# REGISTRO DE AULAS MENSAL — MODELO DIÁRIO REAL
# =====================================================

@login_required
def registro_aulas_mensal_turma(request, turma_id):

    turma = get_object_or_404(
        Turma.objects.prefetch_related("alunos"),
        id=turma_id
    )

    if not (usuario_gestor(request.user) or usuario_professor(request.user)):
        return render(request, "core/acesso_negado.html")

    if usuario_professor(request.user):
        possui_vinculo = ProfessorTurmaDisciplina.objects.filter(
            professor=request.user,
            turma=turma,
            ativo=True
        ).exists()

        if turma.professor_id != request.user.id and not possui_vinculo:
            return render(request, "core/acesso_negado.html")

    vinculos = ProfessorTurmaDisciplina.objects.filter(
        turma=turma,
        ativo=True
    ).select_related("disciplina", "professor")

    if usuario_professor(request.user):
        vinculos = vinculos.filter(professor=request.user)

    disciplinas = Disciplina.objects.filter(
        id__in=vinculos.values_list("disciplina_id", flat=True)
    ).distinct().order_by("nome")

    if not disciplinas.exists():
        disciplinas = Disciplina.objects.all().order_by("nome")

    hoje = date.today()
    mes_param = request.GET.get("mes") or hoje.strftime("%Y-%m")

    try:
        ano, mes = [int(parte) for parte in mes_param.split("-")]
        primeiro_dia = date(ano, mes, 1)
    except Exception:
        ano, mes = hoje.year, hoje.month
        primeiro_dia = date(ano, mes, 1)
        mes_param = hoje.strftime("%Y-%m")

    ultimo_dia_numero = calendar.monthrange(ano, mes)[1]
    ultimo_dia = date(ano, mes, ultimo_dia_numero)

    diarios = Diario.objects.filter(
        turma=turma,
        data__gte=primeiro_dia,
        data__lte=ultimo_dia,
    ).select_related("turma", "professor").order_by("disciplina", "data", "id")

    if usuario_professor(request.user):
        diarios = diarios.filter(professor=request.user)

    disciplina_query = request.GET.get("disciplina")

    if disciplina_query:
        disciplina_obj = disciplinas.filter(id=disciplina_query).first()
        if disciplina_obj:
            diarios = diarios.filter(disciplina=disciplina_obj.nome)
            disciplina_query = disciplina_obj.nome
        else:
            diarios = diarios.filter(disciplina=disciplina_query)

    grupos = []

    nomes_disciplinas = list(
        diarios.exclude(disciplina__isnull=True)
        .exclude(disciplina="")
        .values_list("disciplina", flat=True)
        .distinct()
    )

    if not nomes_disciplinas:
        nomes_disciplinas = [disciplina.nome for disciplina in disciplinas]

    for nome_disciplina in sorted(set(nomes_disciplinas)):
        registros = diarios.filter(disciplina=nome_disciplina)

        total_aulas = sum(registro.quantidade_aulas or 1 for registro in registros)

        grupos.append({
            "disciplina": nome_disciplina,
            "registros": registros,
            "total_registros": registros.count(),
            "total_aulas": total_aulas,
        })

    meses = []
    for numero in range(1, 13):
        meses.append({
            "valor": f"{ano}-{numero:02d}",
            "nome": calendar.month_name[numero].capitalize(),
            "ativo": numero == mes,
        })

    total_registros = diarios.count()
    total_aulas = sum(registro.quantidade_aulas or 1 for registro in diarios)

    context = {
        "turma": turma,
        "disciplinas": disciplinas,
        "disciplina_query": disciplina_query,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "meses": meses,
        "grupos": grupos,
        "total_registros": total_registros,
        "total_aulas": total_aulas,
        "hoje": hoje,
        "escola": Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first(),
        "ano_letivo": turma.ano_letivo,
        "professor_logado": request.user if usuario_professor(request.user) else None,
        "is_gestor": usuario_gestor(request.user),
    }

    return render(
        request,
        "core/registro_aulas_mensal.html",
        context
    )


@login_required
def gestao_fechamentos(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.all()
    disciplinas = Disciplina.objects.all()

    if request.method == "POST":
        turma_id = request.POST.get("turma")
        disciplina_id = request.POST.get("disciplina") or None
        bimestre = request.POST.get("bimestre")
        status = request.POST.get("status") or "FECHADO"
        observacoes = request.POST.get("observacoes")

        if turma_id and bimestre:
            obj, created = FechamentoBimestre.objects.update_or_create(
                turma_id=turma_id,
                disciplina_id=disciplina_id,
                bimestre=bimestre,
                defaults={
                    "status": status,
                    "observacoes": observacoes,
                    "fechado_por": request.user if status == "FECHADO" else None,
                    "fechado_em": timezone.now() if status == "FECHADO" else None,
                }
            )
            messages.success(request, "Fechamento bimestral atualizado com sucesso.")
            return redirect("gestao_fechamentos")

        messages.error(request, "Informe turma e bimestre para salvar o fechamento.")

    fechamentos = FechamentoBimestre.objects.select_related(
        "turma",
        "disciplina",
        "fechado_por",
    ).order_by("turma__nome", "bimestre", "disciplina__nome")

    matriz = []
    for turma in turmas:
        linha = {"turma": turma, "bimestres": []}
        for numero in [1, 2, 3, 4]:
            total = fechamentos.filter(turma=turma, bimestre=numero).count()
            fechados = fechamentos.filter(turma=turma, bimestre=numero, status="FECHADO").count()
            linha["bimestres"].append({
                "numero": numero,
                "total": total,
                "fechados": fechados,
                "status": "Fechado" if total and total == fechados else "Pendente",
            })
        matriz.append(linha)

    context = {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turmas": turmas,
        "disciplinas": disciplinas,
        "fechamentos": fechamentos[:120],
        "matriz": matriz,
        "bimestres": Nota.BIMESTRES,
        "status_choices": FechamentoBimestre.STATUS,
        "total_fechamentos": fechamentos.count(),
        "total_fechados": fechamentos.filter(status="FECHADO").count(),
        "total_pendentes": fechamentos.exclude(status="FECHADO").count(),
    }

    return render(request, "gestao/fechamentos.html", context)


@login_required
def gestao_fechamento_anual(request):
    """Mapa anual de aprovação, recuperação e pendências por turma."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turma_id = request.GET.get("turma")
    turmas = Turma.objects.all().prefetch_related("alunos")
    turma_selecionada = turmas.filter(id=turma_id).first() if turma_id else turmas.first()

    alunos_fechamento = []
    total_aprovados = total_atencao = total_risco = 0
    if turma_selecionada:
        for aluno in turma_selecionada.alunos.filter(ativo=True):
            indicadores = _indicadores_aluno(aluno)
            if indicadores["situacao"] == "Aprovado":
                total_aprovados += 1
            elif indicadores["situacao"] == "Risco alto":
                total_risco += 1
            else:
                total_atencao += 1
            alunos_fechamento.append({"aluno": aluno, **indicadores})

    if request.method == "POST" and turma_selecionada:
        DocumentoGerado.objects.create(
            tipo="RELATORIO",
            titulo=f"Fechamento anual • {turma_selecionada.nome}",
            turma=turma_selecionada,
            gerado_por=request.user,
            observacoes="Mapa anual consolidado gerado pela Etapa 14.",
        )
        registrar_auditoria(request.user, "Fechamento anual", "Mapa anual gerado", objeto=turma_selecionada.nome)
        messages.success(request, "Fechamento anual consolidado registrado nos documentos oficiais.")
        return redirect(f"{request.path}?turma={turma_selecionada.id}")

    context = {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turmas": turmas,
        "turma_selecionada": turma_selecionada,
        "alunos_fechamento": alunos_fechamento,
        "total_aprovados": total_aprovados,
        "total_atencao": total_atencao,
        "total_risco": total_risco,
        "total_alunos": len(alunos_fechamento),
    }
    return render(request, "gestao/fechamento_anual.html", context)


@login_required
def gestao_checklist_fechamento(request):
    """Checklist institucional antes do fechamento bimestral/anual."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas_status = []
    for turma in Turma.objects.all().prefetch_related("alunos"):
        alunos = turma.alunos.filter(ativo=True)
        total_alunos = alunos.count()
        notas = Nota.objects.filter(turma=turma)
        notas_incompletas = notas.filter(valor__isnull=True).count()
        conteudos = ConteudoAula.objects.filter(turma=turma).count()
        frequencias = Frequencia.objects.filter(turma=turma).count()
        documentos = DocumentoGerado.objects.filter(turma=turma).count()
        assinaturas = AssinaturaDocumento.objects.filter(turma=turma).count()
        pendencias = []
        if total_alunos == 0:
            pendencias.append("turma sem alunos ativos")
        if notas_incompletas:
            pendencias.append(f"{notas_incompletas} notas incompletas")
        if conteudos == 0:
            pendencias.append("registro de aulas vazio")
        if frequencias == 0:
            pendencias.append("frequência ainda não lançada")
        if documentos > assinaturas:
            pendencias.append("documentos oficiais pendentes de assinatura")
        status = "PRONTO" if not pendencias else "PENDENTE"
        turmas_status.append({
            "turma": turma,
            "alunos": total_alunos,
            "notas_incompletas": notas_incompletas,
            "conteudos": conteudos,
            "frequencias": frequencias,
            "documentos": documentos,
            "assinaturas": assinaturas,
            "pendencias": pendencias,
            "status": status,
        })

    registrar_auditoria(request.user, "Fechamento", "Checklist de fechamento consultado", objeto="Etapa 15")
    return render(request, "gestao/checklist_fechamento.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turmas_status": turmas_status,
        "total_turmas": len(turmas_status),
        "total_prontas": sum(1 for item in turmas_status if item["status"] == "PRONTO"),
        "total_pendentes": sum(1 for item in turmas_status if item["status"] != "PRONTO"),
    })


@login_required
def professor_registro_rapido_aula(request):
    """Atalho premium para o professor abrir rapidamente o registro mensal de aulas."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    turmas = _turmas_visiveis_para_usuario(request.user)
    cards = []
    for turma in turmas:
        cards.append({
            "turma": turma,
            "disciplinas": _disciplinas_da_turma(turma, request.user),
            "ultimos": ConteudoAula.objects.filter(turma=turma, professor=request.user).order_by("-data")[:4],
        })
    return render(request, "core/professor_registro_rapido_aula.html", {"cards": cards, "hoje": date.today()})


@login_required
def professor_aula_rapida_321(request, horario_id=None):
    """Aula operacional: chamada P/F/FJ + conteúdo em uma tela premium."""
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    professor = request.user
    horario = _resolver_horario_do_professor(professor, horario_id)
    if not horario:
        # Mantém o professor dentro da tela Aula rápida, mesmo quando a gestão
        # ainda não cadastrou horários. Antes o clique redirecionava para a
        # Central do Professor e dava a impressão de que a Aula rápida estava vazia.
        outros_horarios = HorarioAula.objects.select_related("turma", "disciplina").filter(
            professor=professor,
            ativo=True,
        ).order_by("dia_semana", "ordem", "hora_inicio")
        messages.warning(request, "A gestão precisa cadastrar seus vínculos e horários antes da Aula rápida.")
        return render(request, "core/professor_aula_rapida_321.html", {
            "aula_rapida_sem_horario": True,
            "horario": None,
            "outros_horarios": outros_horarios,
            "alunos_linhas": [],
            "conteudo": None,
            "data_aula": date.today(),
            "resumo": {"alunos": 0, "presencas": 0, "faltas": 0, "fj": 0},
            "aula_861_900": None,
            "status_choices": Frequencia.STATUS_FREQUENCIA_CHOICES,
        })

    data_aula = date.today()
    data_informada = request.POST.get("data") if request.method == "POST" else request.GET.get("data")
    if data_informada:
        try:
            data_aula = datetime.strptime(data_informada, "%Y-%m-%d").date()
        except Exception:
            data_aula = date.today()

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "salvar_chamada":
            for aluno in horario.turma.alunos.filter(ativo=True):
                status = request.POST.get(f"status_{aluno.id}") or "P"
                observacao = request.POST.get(f"obs_{aluno.id}") or ""
                Frequencia.objects.update_or_create(
                    aluno=aluno,
                    disciplina=horario.disciplina,
                    data=data_aula,
                    defaults={"turma": horario.turma, "status": status, "observacao": observacao},
                )
            messages.success(request, "Chamada oficial salva com P/F/FJ.")
        elif acao == "salvar_conteudo":
            descricao = (request.POST.get("descricao") or "").strip()
            observacoes = (request.POST.get("observacoes") or "").strip()
            if descricao:
                ConteudoAula.objects.update_or_create(
                    professor=professor,
                    turma=horario.turma,
                    disciplina=horario.disciplina,
                    data=data_aula,
                    defaults={"descricao": descricao, "observacoes": observacoes},
                )
                messages.success(request, "Conteúdo da aula salvo no Diário Escolar.")
            else:
                messages.warning(request, "Informe o conteúdo da aula para salvar o registro mensal.")
        destino = redirect("professor_aula_rapida_321_horario", horario_id=horario.id)
        destino["Location"] = f"{destino['Location']}?data={data_aula:%Y-%m-%d}"
        return destino

    alunos_linhas = []
    for aluno in horario.turma.alunos.filter(ativo=True).order_by("nome"):
        freq = Frequencia.objects.filter(aluno=aluno, turma=horario.turma, disciplina=horario.disciplina, data=data_aula).first()
        alunos_linhas.append({"aluno": aluno, "frequencia": freq, "status": freq.status_oficial if freq else "P"})
    conteudo = ConteudoAula.objects.filter(professor=professor, turma=horario.turma, disciplina=horario.disciplina, data=data_aula).first()
    outros_horarios = HorarioAula.objects.select_related("turma", "disciplina").filter(professor=professor, ativo=True).order_by("dia_semana", "ordem")
    resumo = {
        "alunos": len(alunos_linhas),
        "presencas": sum(1 for l in alunos_linhas if l["status"] == "P"),
        "faltas": sum(1 for l in alunos_linhas if l["status"] == "F"),
        "fj": sum(1 for l in alunos_linhas if l["status"] == "FJ"),
    }
    return render(request, "core/professor_aula_rapida_321.html", {
        "horario": horario,
        "outros_horarios": outros_horarios,
        "alunos_linhas": alunos_linhas,
        "conteudo": conteudo,
        "data_aula": data_aula,
        "resumo": resumo,
        "aula_861_900": resumo_aula_861_900(horario, data_aula, professor),
        "status_choices": Frequencia.STATUS_FREQUENCIA_CHOICES,
    })


@login_required
def gestao_fechamento_mensal_901(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    mes_param = request.GET.get("mes") or ""
    ano = mes = None
    if mes_param and "-" in mes_param:
        try:
            ano, mes = [int(x) for x in mes_param.split("-", 1)]
        except Exception:
            ano = mes = None
    contexto = {
        "fechamento": fechamento_mensal_901_960(ano=ano, mes=mes),
        "finalizacao": finalizacao_901_960(),
        "hoje": date.today(),
    }
    registrar_auditoria(request.user, "Fechamento mensal", "Mapa final 901-960 consultado")
    return render(request, "gestao/fechamento_mensal_901.html", contexto)


@login_required
def professor_fechamento_mensal_901(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    mes_param = request.GET.get("mes") or ""
    ano = mes = None
    if mes_param and "-" in mes_param:
        try:
            ano, mes = [int(x) for x in mes_param.split("-", 1)]
        except Exception:
            ano = mes = None
    contexto = {
        "fechamento": fechamento_mensal_901_960(professor=request.user, ano=ano, mes=mes),
        "finalizacao": finalizacao_901_960(professor=request.user),
        "hoje": date.today(),
    }
    return render(request, "core/professor_fechamento_mensal_901.html", contexto)

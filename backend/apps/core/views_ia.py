# Camada de views ia — refatoração real etapa 1221-1280.
# Mantém os nomes públicos usados pelas URLs, mas tira o peso do antigo views.py.

from .views_shared import *  # noqa: F401,F403

# =====================================================
# DIÁRIO
# =====================================================

@login_required
def diario(request):

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
        "core/diario.html",
        context
    )


# =====================================================
# FREQUÊNCIA
# =====================================================

# =====================================================
# FREQUÊNCIA
# =====================================================

@login_required
def frequencia(request):

    if request.user.tipo != "PROF":
        return render(
            request,
            "core/acesso_negado.html"
        )

    turmas = Turma.objects.prefetch_related(
        "alunos"
    ).all()

    turma = turmas.first()

    alunos = []

    total_alunos = 0

    if turma:

        alunos = turma.alunos.all()

        total_alunos = alunos.count()

    context = {

        "turmas": turmas,

        "turma": turma,

        "alunos": alunos,

        "total_turmas": turmas.count(),

        "total_alunos": total_alunos,

        "hoje": date.today(),

    }

    return render(
        request,
        "core/frequencia.html",
        context
    )


# =====================================================
# FREQUÊNCIA TURMA
# =====================================================

@login_required
def frequencia_turma(request, turma_id):

    if request.user.tipo != "PROF":
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(
        Turma,
        id=turma_id
    )

    alunos = turma.alunos.all()

    disciplina = get_disciplina_padrao()

    if request.method == "POST":

        for aluno in alunos:

            presente = request.POST.get(
                f"aluno_{aluno.id}"
            )

            Frequencia.objects.update_or_create(

                aluno=aluno,

                disciplina=disciplina,

                data=date.today(),

                defaults={
                    "turma": turma,
                    "presente": presente == "on",
                    "status": "P" if presente == "on" else "F",
                }

            )

        messages.success(request, "Chamada salva com sucesso.")

        return redirect(
            "turma_detalhe",
            turma.id
        )

    total_presentes = Frequencia.objects.filter(
        turma=turma,
        data=date.today(),
        presente=True
    ).count()

    total_faltas = Frequencia.objects.filter(
        turma=turma,
        data=date.today(),
        presente=False
    ).count()

    context = {

        "turma": turma,

        "alunos": alunos,

        "total_presentes": total_presentes,

        "total_faltas": total_faltas,

        "hoje": date.today(),

    }

    return render(
        request,
        "core/frequencia_turma.html",
        context
    )


@login_required
def frequencia_mensal_turma(request, turma_id):

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

    disciplina_id = request.GET.get("disciplina") or request.POST.get("disciplina")

    disciplina = None

    if disciplina_id:
        disciplina = disciplinas.filter(id=disciplina_id).first()

    if disciplina is None:
        disciplina = disciplinas.first() or get_disciplina_padrao()

    hoje = date.today()
    mes_param = request.GET.get("mes") or request.POST.get("mes") or hoje.strftime("%Y-%m")

    try:
        ano, mes = [int(parte) for parte in mes_param.split("-")]
        primeiro_dia = date(ano, mes, 1)
    except Exception:
        ano, mes = hoje.year, hoje.month
        primeiro_dia = date(ano, mes, 1)
        mes_param = hoje.strftime("%Y-%m")

    ultimo_dia_numero = calendar.monthrange(ano, mes)[1]
    ultimo_dia = date(ano, mes, ultimo_dia_numero)

    data_aula_param = request.GET.get("data") or request.POST.get("data") or hoje.isoformat()

    try:
        data_aula = datetime.strptime(data_aula_param, "%Y-%m-%d").date()
    except Exception:
        data_aula = hoje

    if data_aula < primeiro_dia or data_aula > ultimo_dia:
        data_aula = primeiro_dia

    alunos = turma.alunos.filter(ativo=True).order_by("nome")

    if request.method == "POST":

        for aluno in alunos:

            status = request.POST.get(f"status_{aluno.id}", "P")
            observacao = request.POST.get(f"observacao_{aluno.id}", "").strip()

            presente = status == "P"

            if status == "FJ":
                observacao = observacao or "Falta justificada"
            elif status == "F":
                observacao = observacao or "Falta"

            Frequencia.objects.update_or_create(
                aluno=aluno,
                turma=turma,
                disciplina=disciplina,
                data=data_aula,
                defaults={
                    "presente": presente,
                    "status": status,
                    "observacao": observacao or None,
                }
            )

        messages.success(request, "Frequência mensal salva com sucesso.")

        return redirect(
            f"{request.path}?disciplina={disciplina.id}&mes={mes_param}&data={data_aula.isoformat()}"
        )

    frequencias_mes = Frequencia.objects.filter(
        turma=turma,
        disciplina=disciplina,
        data__gte=primeiro_dia,
        data__lte=ultimo_dia,
    ).select_related("aluno")

    datas_registradas = list(
        frequencias_mes.order_by("data")
        .values_list("data", flat=True)
        .distinct()
    )

    if data_aula not in datas_registradas:
        datas_registradas.append(data_aula)
        datas_registradas = sorted(datas_registradas)

    frequencias_por_aluno_data = {
        (freq.aluno_id, freq.data): freq
        for freq in frequencias_mes
    }

    linhas = []
    total_faltas = 0
    total_presencas = 0

    for indice, aluno in enumerate(alunos, start=1):

        celulas = []
        faltas_aluno = 0
        presencas_aluno = 0

        for data_ref in datas_registradas:
            freq = frequencias_por_aluno_data.get((aluno.id, data_ref))

            status = _status_frequencia(freq)
            classe = _classe_status_frequencia(status)

            if status == "P":
                presencas_aluno += 1
            elif _frequencia_e_falta(status):
                faltas_aluno += 1

            celulas.append({
                "data": data_ref,
                "status": status,
                "classe": classe,
            })

        total_faltas += faltas_aluno
        total_presencas += presencas_aluno

        linhas.append({
            "numero": indice,
            "aluno": aluno,
            "celulas": celulas,
            "faltas": faltas_aluno,
            "presencas": presencas_aluno,
        })

    chamada_dia = []
    for aluno in alunos:
        freq = frequencias_por_aluno_data.get((aluno.id, data_aula))
        status = "P"
        observacao = ""

        if freq:
            status = _status_frequencia(freq) or "P"
            observacao = freq.observacao or ""

        chamada_dia.append({
            "aluno": aluno,
            "status": status,
            "observacao": observacao,
        })

    meses = []
    for numero in range(1, 13):
        meses.append({
            "valor": f"{ano}-{numero:02d}",
            "nome": calendar.month_name[numero].capitalize(),
            "ativo": numero == mes,
        })

    context = {
        "turma": turma,
        "disciplina": disciplina,
        "disciplinas": disciplinas,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "meses": meses,
        "data_aula": data_aula,
        "datas_registradas": datas_registradas,
        "linhas": linhas,
        "chamada_dia": chamada_dia,
        "total_alunos": alunos.count(),
        "total_faltas": total_faltas,
        "total_presencas": total_presencas,
        "hoje": hoje,
        "escola": Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first(),
        "ano_letivo": turma.ano_letivo,
        "professor_logado": request.user if usuario_professor(request.user) else None,
        "is_gestor": usuario_gestor(request.user),
        "total_fj": sum(1 for linha in linhas for celula in linha["celulas"] if celula["status"] == "FJ"),
    }

    return render(
        request,
        "core/frequencia_mensal.html",
        context
    )


# =====================================================
# RELATÓRIO DO DIÁRIO DE CLASSE — MODELO OFICIAL
# =====================================================

@login_required
def diario_classe_turma(request, turma_id):

    turma = get_object_or_404(
        Turma.objects.select_related("ano_letivo", "professor").prefetch_related("alunos"),
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

    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()

    professor = turma.professor

    if professor is None:
        vinculo_professor = ProfessorTurmaDisciplina.objects.filter(
            turma=turma,
            ativo=True
        ).select_related("professor").first()
        professor = vinculo_professor.professor if vinculo_professor else request.user

    perfil_professor = ProfessorPerfil.objects.filter(
        usuario=professor
    ).select_related("escola").first()

    vinculos = ProfessorTurmaDisciplina.objects.filter(
        turma=turma,
        ativo=True
    ).select_related("professor", "disciplina", "ano_letivo")

    disciplinas = Disciplina.objects.filter(
        id__in=vinculos.values_list("disciplina_id", flat=True)
    ).distinct().order_by("nome")

    if not disciplinas.exists():
        disciplinas = Disciplina.objects.filter(
            id__in=Nota.objects.filter(turma=turma).values_list("disciplina_id", flat=True)
        ).distinct().order_by("nome")

    if not disciplinas.exists():
        disciplinas = Disciplina.objects.filter(
            id__in=Frequencia.objects.filter(turma=turma).values_list("disciplina_id", flat=True)
        ).distinct().order_by("nome")

    if not disciplinas.exists():
        disciplinas = Disciplina.objects.all().order_by("nome")

    horarios = HorarioAula.objects.filter(
        turma=turma,
        ativo=True
    ).select_related("professor", "disciplina").order_by("dia_semana", "ordem", "hora_inicio")

    grade = []
    for dia_valor, dia_label in HorarioAula.DIAS_SEMANA:
        grade.append({
            "dia": dia_label,
            "horarios": horarios.filter(dia_semana=dia_valor),
        })

    alunos = turma.alunos.filter(ativo=True).order_by("nome")

    meses_nomes = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    ano_base = turma.ano_letivo.ano if turma.ano_letivo else date.today().year

    frequencia_por_mes = []

    for mes_num in range(1, 13):
        primeiro_dia = date(ano_base, mes_num, 1)
        ultimo_dia = date(ano_base, mes_num, calendar.monthrange(ano_base, mes_num)[1])

        disciplinas_mes = []

        for disciplina in disciplinas:
            registros = Frequencia.objects.filter(
                turma=turma,
                disciplina=disciplina,
                data__gte=primeiro_dia,
                data__lte=ultimo_dia,
            ).select_related("aluno").order_by("data")

            datas = list(
                registros.values_list("data", flat=True).distinct().order_by("data")
            )

            if not datas:
                continue

            linhas = []
            for aluno in alunos:
                status_por_data = []
                faltas = 0
                for data_item in datas:
                    registro = registros.filter(aluno=aluno, data=data_item).first()
                    status = "-"
                    if registro:
                        if registro.presente:
                            status = "FJ" if registro.observacao and "justificada" in registro.observacao.lower() else "P"
                        else:
                            status = "F"
                            faltas += 1
                    status_por_data.append({"data": data_item, "status": status})

                linhas.append({
                    "aluno": aluno,
                    "status_por_data": status_por_data,
                    "faltas": faltas,
                })

            disciplinas_mes.append({
                "disciplina": disciplina,
                "datas": datas,
                "linhas": linhas,
            })

        if disciplinas_mes:
            frequencia_por_mes.append({
                "numero": mes_num,
                "nome": meses_nomes[mes_num],
                "disciplinas": disciplinas_mes,
            })

    registros_aulas = []
    for disciplina in disciplinas:
        aulas = ConteudoAula.objects.filter(
            turma=turma,
            disciplina=disciplina
        ).select_related("disciplina", "professor").order_by("data")

        diarios = Diario.objects.filter(
            turma=turma,
            disciplina__iexact=disciplina.nome
        ).order_by("data")

        if aulas.exists() or diarios.exists():
            registros_aulas.append({
                "disciplina": disciplina,
                "aulas": aulas,
                "diarios": diarios,
            })

    avaliacoes = []
    for disciplina in disciplinas:
        linhas = []
        for aluno in alunos:
            notas = Nota.objects.filter(
                aluno=aluno,
                turma=turma,
                disciplina=disciplina
            )
            bimestres = []
            soma = Decimal("0")
            quantidade = 0
            for bimestre in [1, 2, 3, 4]:
                nota = notas.filter(bimestre=bimestre).first()
                media = nota.valor if nota and nota.valor is not None else None
                if media is not None:
                    soma += Decimal(str(media))
                    quantidade += 1
                bimestres.append({
                    "numero": bimestre,
                    "nota": nota,
                    "media": media,
                })
            media_anual = round(soma / quantidade, 2) if quantidade else None
            linhas.append({
                "aluno": aluno,
                "bimestres": bimestres,
                "media_anual": media_anual,
            })
        avaliacoes.append({
            "disciplina": disciplina,
            "linhas": linhas,
        })

    resumo = {
        "total_alunos": alunos.count(),
        "total_disciplinas": disciplinas.count(),
        "total_horarios": horarios.count(),
        "total_registros": sum(item["aulas"].count() + item["diarios"].count() for item in registros_aulas),
    }

    context = {
        "turma": turma,
        "escola": escola,
        "professor": professor,
        "perfil_professor": perfil_professor,
        "alunos": alunos,
        "disciplinas": disciplinas,
        "grade": grade,
        "frequencia_por_mes": frequencia_por_mes,
        "registros_aulas": registros_aulas,
        "avaliacoes": avaliacoes,
        "resumo": resumo,
        "ano_base": ano_base,
        "hoje": date.today(),
    }

    return render(request, "core/diario_classe_turma.html", context)


# =====================================================
# GESTÃO — INTELIGÊNCIA ESCOLAR E RELATÓRIOS
# Etapa 8: adiciona visão executiva sem remover telas antigas.
# =====================================================

@login_required
def gestao_inteligencia(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    Usuario = get_user_model()

    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()

    turmas = Turma.objects.all().prefetch_related("alunos")
    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    professores = Usuario.objects.filter(tipo="PROF")
    frequencias = Frequencia.objects.select_related("aluno", "turma", "disciplina")
    notas = Nota.objects.select_related("aluno", "turma", "disciplina")
    conteudos = ConteudoAula.objects.select_related("turma", "disciplina", "professor")

    total_registros = frequencias.count()
    total_presencas = frequencias.filter(presente=True).count()
    total_faltas = frequencias.filter(presente=False).count()
    frequencia_geral = round((total_presencas / total_registros) * 100, 1) if total_registros else 0

    medias_validas = [float(n.valor) for n in notas if n.valor is not None]
    media_geral = round(sum(medias_validas) / len(medias_validas), 1) if medias_validas else 0

    turmas_dados = []
    total_risco = 0

    for turma in turmas:
        alunos_turma = turma.alunos.filter(ativo=True)
        ids_alunos = alunos_turma.values_list("id", flat=True)
        freq_turma = frequencias.filter(aluno_id__in=ids_alunos)
        notas_turma = notas.filter(aluno_id__in=ids_alunos)

        qtd_freq = freq_turma.count()
        qtd_pres = freq_turma.filter(presente=True).count()
        freq_percentual = round((qtd_pres / qtd_freq) * 100, 1) if qtd_freq else 0

        medias_turma = [float(n.valor) for n in notas_turma if n.valor is not None]
        media_turma = round(sum(medias_turma) / len(medias_turma), 1) if medias_turma else 0

        alunos_risco = AnaliseInteligenteService.alunos_em_risco(turma)
        total_risco += len(alunos_risco)

        turmas_dados.append({
            "turma": turma,
            "total_alunos": alunos_turma.count(),
            "frequencia": freq_percentual,
            "media": media_turma,
            "risco": len(alunos_risco),
            "conteudos": conteudos.filter(turma=turma).count(),
        })

    turmas_criticas = sorted(
        turmas_dados,
        key=lambda item: (item["risco"], -item["frequencia"]),
        reverse=True
    )[:8]

    professores_dados = []
    for professor in professores:
        vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True)
        horarios = HorarioAula.objects.filter(professor=professor, ativo=True)
        conteudos_professor = conteudos.filter(professor=professor).count()
        professores_dados.append({
            "professor": professor,
            "nome": _nome_usuario(professor),
            "vinculos": vinculos.count(),
            "horarios": horarios.count(),
            "conteudos": conteudos_professor,
        })

    context = {
        "escola": escola,
        "hoje": date.today(),
        "total_alunos": alunos.count(),
        "total_turmas": turmas.count(),
        "total_professores": professores.count(),
        "total_risco": total_risco,
        "total_faltas": total_faltas,
        "frequencia_geral": frequencia_geral,
        "media_geral": media_geral,
        "total_conteudos": conteudos.count(),
        "turmas_dados": turmas_dados,
        "turmas_criticas": turmas_criticas,
        "professores_dados": professores_dados,
        "grafico_labels": json.dumps([item["turma"].nome for item in turmas_dados[:10]]),
        "grafico_frequencia": json.dumps([item["frequencia"] for item in turmas_dados[:10]]),
        "grafico_media": json.dumps([item["media"] for item in turmas_dados[:10]]),
    }

    return render(request, "gestao/inteligencia.html", context)


@login_required
def gestao_pareceres(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    turmas = Turma.objects.all()

    busca = request.GET.get("busca", "").strip()
    if busca:
        alunos = alunos.filter(nome__icontains=busca)

    if request.method == "POST":
        aluno_id = request.POST.get("aluno")
        bimestre = request.POST.get("bimestre") or None
        texto = request.POST.get("texto")
        encaminhamentos = request.POST.get("encaminhamentos")

        if aluno_id and texto:
            aluno = get_object_or_404(Aluno, id=aluno_id)
            ParecerAluno.objects.create(
                aluno=aluno,
                turma=aluno.turma,
                bimestre=bimestre,
                professor=request.user,
                texto=texto,
                encaminhamentos=encaminhamentos,
            )
            messages.success(request, "Parecer descritivo registrado com sucesso.")
            return redirect("gestao_pareceres")

        messages.error(request, "Informe aluno e parecer para salvar.")

    pareceres = ParecerAluno.objects.select_related(
        "aluno",
        "turma",
        "professor",
    )[:120]

    context = {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "alunos": alunos[:150],
        "turmas": turmas,
        "pareceres": pareceres,
        "busca": busca,
        "bimestres": Nota.BIMESTRES,
        "total_pareceres": ParecerAluno.objects.count(),
        "total_alunos": alunos.count(),
    }

    return render(request, "gestao/pareceres.html", context)


@login_required
def gestao_auditoria(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    modulo = request.GET.get("modulo", "")
    auditorias = AuditoriaSistema.objects.select_related("usuario").all()

    if modulo:
        auditorias = auditorias.filter(modulo__icontains=modulo)

    context = {
        "auditorias": auditorias[:160],
        "modulo": modulo,
        "total_auditorias": AuditoriaSistema.objects.count(),
        "hoje": date.today(),
    }

    return render(request, "gestao/auditoria.html", context)


@login_required
def professor_ia_pedagogica(request):
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')

    turmas = Turma.objects.filter(ativa=True, professor=request.user)
    contexto_ia = montar_analise_pedagogica_avancada(turmas)
    contexto_ia['modo'] = 'Professor'
    contexto_ia['subtitulo'] = 'IA pedagógica avançada para suas turmas, notas, frequência e recuperação.'
    return render(request, 'core/ia_pedagogica_avancada.html', contexto_ia)


@login_required
def gestao_ia_pedagogica(request):
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')

    contexto_ia = montar_analise_pedagogica_avancada()
    contexto_ia['modo'] = 'Gestão'
    contexto_ia['subtitulo'] = 'Leitura executiva de risco pedagógico, frequência, médias e intervenção escolar.'
    return render(request, 'gestao/ia_pedagogica_avancada.html', contexto_ia)


@login_required
def gestao_auditoria_exportacao(request):
    """Página imprimível para conferência/exportação da auditoria."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    auditorias = AuditoriaSistema.objects.select_related("usuario")[:300]
    registrar_auditoria(request.user, "Auditoria", "Exportação de auditoria aberta", objeto="Auditoria imprimível")
    return render(request, "gestao/auditoria_exportacao.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "auditorias": auditorias,
        "total_auditorias": AuditoriaSistema.objects.count(),
    })


@login_required
def gestao_analytics_avancado(request):
    """Analytics executivo sem alterar dashboards existentes."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.all().prefetch_related("alunos")
    linhas = []
    for turma in turmas:
        alunos = turma.alunos.filter(ativo=True)
        medias = [_media_aluno(aluno) for aluno in alunos]
        faltas = sum(_faltas_aluno(aluno) for aluno in alunos)
        linhas.append({
            "turma": turma,
            "alunos": alunos.count(),
            "media": round(sum(medias) / len(medias), 1) if medias else 0,
            "faltas": faltas,
            "risco": sum(1 for m in medias if m < 6),
        })

    registrar_auditoria(request.user, "Analytics", "Analytics executivo consultado")
    return render(request, "gestao/analytics_avancado.html", {
        "hoje": date.today(),
        "linhas": linhas,
        "total_turmas": len(linhas),
        "total_alunos": sum(item["alunos"] for item in linhas),
        "media_geral": round(sum(item["media"] for item in linhas) / len(linhas), 1) if linhas else 0,
        "total_risco": sum(item["risco"] for item in linhas),
    })


@login_required
def gestao_pendencias_professores(request):
    """Mapa de acompanhamento de pendências por professor/turma/disciplina."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    Usuario = get_user_model()
    professores = Usuario.objects.filter(tipo="PROF")
    linhas = []
    for professor in professores:
        turmas = Turma.objects.filter(professor=professor)
        vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
        total_alunos = Aluno.objects.filter(turma__in=turmas, ativo=True).count()
        notas = Nota.objects.filter(turma__in=turmas).count()
        freq = Frequencia.objects.filter(turma__in=turmas).count()
        conteudos = ConteudoAula.objects.filter(professor=professor).count()
        pendencias = []
        if turmas.exists() and notas == 0:
            pendencias.append("Notas T1/T2/T3 ainda não lançadas")
        if turmas.exists() and freq == 0:
            pendencias.append("Frequência sem registros")
        if turmas.exists() and conteudos == 0:
            pendencias.append("Registro mensal de aulas pendente")
        if not vinculos.exists():
            pendencias.append("Vínculo professor x turma x disciplina pendente")
        linhas.append({
            "professor": professor,
            "turmas": turmas.count(),
            "alunos": total_alunos,
            "notas": notas,
            "frequencias": freq,
            "conteudos": conteudos,
            "pendencias": pendencias,
            "status": "OK" if not pendencias else "Atenção",
        })

    registrar_auditoria(request.user, "Pendências", "Mapa de pendências por professor consultado")
    return render(request, "gestao/pendencias_professores.html", {
        "hoje": date.today(),
        "linhas": linhas,
        "total_pendencias": sum(len(item["pendencias"]) for item in linhas),
    })


@login_required
def professor_central_pendencias(request):
    """Central operacional do professor: o que falta preencher sem entrar na gestão."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.filter(professor=request.user, ativa=True).prefetch_related("alunos")
    linhas = []
    for turma in turmas:
        alunos = turma.alunos.filter(ativo=True)
        notas = Nota.objects.filter(turma=turma).count()
        freq = Frequencia.objects.filter(turma=turma).count()
        conteudos = ConteudoAula.objects.filter(turma=turma, professor=request.user).count()
        faltas = Frequencia.objects.filter(turma=turma, presente=False).count()
        pendencias = []
        if alunos.exists() and notas == 0:
            pendencias.append("Lançar notas T1/T2/T3")
        if alunos.exists() and freq == 0:
            pendencias.append("Registrar frequência")
        if conteudos == 0:
            pendencias.append("Registrar conteúdo/atividade mensal")
        if faltas >= 10:
            pendencias.append("Acompanhar faltas recorrentes")
        linhas.append({
            "turma": turma,
            "alunos": alunos.count(),
            "notas": notas,
            "frequencias": freq,
            "conteudos": conteudos,
            "faltas": faltas,
            "pendencias": pendencias,
            "status": "OK" if not pendencias else "Atenção",
        })

    return render(request, "core/professor_central_pendencias.html", {
        "hoje": date.today(),
        "linhas": linhas,
        "ultimos_conteudos": _ultimos_conteudos_professor(request.user),
        "total_pendencias": sum(len(item["pendencias"]) for item in linhas),
    })


@login_required
def gestao_publicacao_comercial(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    registrar_auditoria(request.user, "Comercial", "Checklist de publicação comercial consultado")
    checklist = [
        {"nome":"Domínio/SSL", "status":"Pendente externo", "detalhe":"Configurar no provedor escolhido."},
        {"nome":"Variáveis de ambiente", "status":"Pronto para configurar", "detalhe":"SECRET_KEY, DEBUG=False, ALLOWED_HOSTS e banco de produção."},
        {"nome":"Plano comercial", "status":"Estruturado", "detalhe":"Licença escola, multi-escola e suporte."},
        {"nome":"Homologação escola piloto", "status":"Recomendado", "detalhe":"Validar com dados reais antes do lançamento público."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Publicação comercial", "Checklist final para transformar o Diário IA em produto vendável e implantável.", "98", checklist=checklist,
        cards=[{"titulo":"Release", "valor":"Candidato", "texto":"Pronto para homologação comercial."}, {"titulo":"Documentação", "valor":"Incluída", "texto":"Leia README_ETAPAS97_108_FINALIZACAO_ACELERADA.md."}],
        proximos=["Definir preço/plano", "Configurar ambiente cloud", "Criar escola piloto"]
    ))


@login_required
def gestao_diario_oficial(request):
    """Central de diário oficial da gestão: escola, professor, turma, disciplinas, horários e ações."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    turmas = _turmas_visiveis_para_usuario(request.user)
    turno = request.GET.get("turno", "")
    if turno:
        turmas = turmas.filter(turno__icontains=turno)
    dados = [_resumo_diario_turma(turma) for turma in turmas]
    context = {
        "escola": escola,
        "ano_letivo": escola.ano_letivo_ativo if escola else AnoLetivo.objects.filter(ativo=True).first(),
        "dados": dados,
        "turno": turno,
        "turnos": ["MATUTINO", "VESPERTINO", "NOTURNO", "EJA", "MANHÃ", "TARDE", "NOITE"],
        "hoje": date.today(),
        "resumo_861_900_gestao": resumo_gestao_861_900(),
    }
    return render(request, "gestao/diario_oficial_central.html", context)


@login_required
def professor_diario_oficial(request):
    """Central do professor com apenas suas turmas/disciplinas para diário, frequência e aula mensal."""
    if not usuario_professor(request.user):
        if usuario_gestor(request.user):
            return redirect("gestao_diario_oficial")
        return render(request, "core/acesso_negado.html")
    turmas = _turmas_visiveis_para_usuario(request.user)
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    dados = [_resumo_diario_turma(turma, request.user) for turma in turmas]
    context = {
        "escola": escola,
        "dados": dados,
        "professor": request.user,
        "perfil_professor": ProfessorPerfil.objects.filter(usuario=request.user).select_related("escola").first(),
        "hoje": date.today(),
        "resumo_861_900_professor": resumo_professor_861_900(request.user),
    }
    return render(request, "core/professor_diario_oficial_central.html", context)


@login_required
def gestao_ficha_aluno_oficial(request, aluno_id):
    """Ficha real do aluno com boletim, frequência por disciplina, histórico, parecer e documentos."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    turma = aluno.turma
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    disciplinas = _disciplinas_da_turma(turma)
    if not disciplinas.exists():
        disciplinas = Disciplina.objects.all().order_by("nome")

    resumo_disciplinas = []
    for disciplina in disciplinas:
        frequencias = Frequencia.objects.filter(aluno=aluno, disciplina=disciplina).order_by("-data")
        total = frequencias.count()
        faltas = frequencias.filter(presente=False).count()
        presencas = total - faltas
        freq_percentual = round((presencas / total) * 100, 1) if total else 100
        notas = Nota.objects.filter(aluno=aluno, disciplina=disciplina).order_by("bimestre")
        notas_validas = [n.valor for n in notas if n.valor is not None]
        media = round(sum(notas_validas) / len(notas_validas), 2) if notas_validas else None
        resumo_disciplinas.append({
            "disciplina": disciplina,
            "frequencias": frequencias[:16],
            "faltas": faltas,
            "frequencia_percentual": freq_percentual,
            "notas": notas,
            "media": media,
            "conteudos": ConteudoAula.objects.filter(turma=turma, disciplina=disciplina).order_by("-data")[:8],
        })

    context = {
        "aluno": aluno,
        "turma": turma,
        "escola": escola,
        "ano_letivo": turma.ano_letivo if turma else None,
        "resumo_disciplinas": resumo_disciplinas,
        "historicos": HistoricoAluno.objects.filter(aluno=aluno).select_related("registrado_por", "ano_letivo")[:60],
        "pareceres": ParecerAluno.objects.filter(aluno=aluno).select_related("professor")[:40],
        "documentos": DocumentoGerado.objects.filter(aluno=aluno).select_related("gerado_por")[:40],
        "hoje": date.today(),
    }
    return render(request, "gestao/ficha_aluno_oficial.html", context)


@login_required
def diario_oficial_turma_completo(request, turma_id):
    turma = get_object_or_404(Turma.objects.select_related("ano_letivo", "professor").prefetch_related("alunos"), id=turma_id)
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")
    context = _montar_diario_oficial_turma(turma, request.user, request)
    return render(request, "gestao/diario_oficial_turma_completo.html", context)


@login_required
def frequencia_disciplina_mensal(request, turma_id, disciplina_id):
    turma = get_object_or_404(Turma, id=turma_id)
    disciplina = get_object_or_404(Disciplina, id=disciplina_id)
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")
    mes = request.GET.get("mes") or date.today().strftime("%Y-%m")
    return redirect(f"/turma/{turma.id}/frequencia-mensal/?disciplina={disciplina.id}&mes={mes}")


@login_required
def gestao_diario_matriz_turnos(request):
    """Mapa oficial dos turnos/séries para conferir se a escola está estruturada conforme pedido."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    grupos = _turmas_por_turno_contexto()
    context = {
        "escola": escola,
        "ano_letivo": escola.ano_letivo_ativo if escola else AnoLetivo.objects.filter(ativo=True).first(),
        "grupos": grupos,
        "hoje": date.today(),
    }
    return render(request, "gestao/diario_matriz_turnos.html", context)


@login_required
def gestao_diario_consolidado_anual(request):
    """Consolidado anual do diário por turma: disciplinas, aulas, frequência e pendências."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    linhas = []
    for turma in turmas:
        disciplinas = _disciplinas_da_turma(turma)
        frequencias = Frequencia.objects.filter(turma=turma)
        total_freq = frequencias.count()
        faltas = frequencias.filter(presente=False).count()
        presencas = total_freq - faltas
        freq_percentual = round((presencas / total_freq) * 100, 1) if total_freq else 100
        aulas = ConteudoAula.objects.filter(turma=turma).count() + Diario.objects.filter(turma=turma).count()
        horarios = HorarioAula.objects.filter(turma=turma, ativo=True).count()
        pendencias = []
        if not disciplinas.exists():
            pendencias.append("sem disciplinas vinculadas")
        if horarios == 0:
            pendencias.append("sem grade semanal")
        if aulas == 0:
            pendencias.append("sem registro de aulas")
        if total_freq == 0:
            pendencias.append("sem frequência lançada")
        linhas.append({
            "turma": turma,
            "disciplinas": disciplinas,
            "total_disciplinas": disciplinas.count(),
            "total_alunos": turma.alunos.filter(ativo=True).count(),
            "freq_percentual": freq_percentual,
            "faltas": faltas,
            "aulas": aulas,
            "horarios": horarios,
            "pendencias": pendencias,
        })
    return render(request, "gestao/diario_consolidado_anual.html", {
        "escola": escola,
        "ano_letivo": escola.ano_letivo_ativo if escola else AnoLetivo.objects.filter(ativo=True).first(),
        "linhas": linhas,
        "hoje": date.today(),
    })


@login_required
def gestao_conferencia_frequencia_mensal(request):
    """Conferência de frequência por mês/disciplina, focada em achar turmas sem lançamentos."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    ano, mes, mes_param, primeiro, ultimo, meses = _periodo_mes_por_parametro(request)
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo")
    linhas = []
    for turma in turmas:
        disciplinas = _disciplinas_da_turma(turma)
        if not disciplinas.exists():
            disciplinas = Disciplina.objects.none()
        itens = []
        for disciplina in disciplinas:
            qs = Frequencia.objects.filter(turma=turma, disciplina=disciplina, data__gte=primeiro, data__lte=ultimo)
            total = qs.count()
            faltas = qs.filter(presente=False).count()
            itens.append({"disciplina": disciplina, "total": total, "faltas": faltas, "status": "OK" if total else "PENDENTE"})
        linhas.append({"turma": turma, "disciplinas": itens, "total_pendentes": sum(1 for i in itens if i["status"] == "PENDENTE")})
    return render(request, "gestao/conferencia_frequencia_mensal.html", {
        "linhas": linhas,
        "meses": meses,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def professor_frequencia_rapida(request):
    """Atalho premium para abrir frequência mensal por turma/disciplina sem botão morto."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    cards = []
    for turma in _turmas_visiveis_para_usuario(request.user):
        cards.append({
            "turma": turma,
            "disciplinas": _disciplinas_da_turma(turma, request.user),
            "alunos": turma.alunos.filter(ativo=True).count(),
        })
    return render(request, "core/professor_frequencia_rapida.html", {"cards": cards, "hoje": date.today()})


@login_required
def gestao_diario_validacao_completa(request):
    """Validação oficial: confere se cada turma tem tudo que o diário físico exige."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    linhas = [_linha_validacao_diario(turma) for turma in turmas]
    context = {
        "escola": Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first(),
        "linhas": linhas,
        "total_turmas": len(linhas),
        "completas": sum(1 for item in linhas if not item["pendencias"]),
        "pendentes": sum(1 for item in linhas if item["pendencias"]),
        "hoje": date.today(),
    }
    return render(request, "gestao/diario_validacao_completa.html", context)


@login_required
def gestao_professor_diario_real(request, professor_id):
    """Página de conferência do professor vindo do admin: vínculos, horários, turmas e disciplinas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    Usuario = get_user_model()
    professor = get_object_or_404(Usuario, id=professor_id, tipo="PROF")
    perfil, _ = ProfessorPerfil.objects.get_or_create(usuario=professor, defaults={"ativo": True})
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina", "ano_letivo")
    horarios = HorarioAula.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina").order_by("dia_semana", "ordem")
    turmas = Turma.objects.filter(id__in=vinculos.values_list("turma_id", flat=True)).distinct().order_by("nome")
    dados = []
    for turma in turmas:
        dados.append(_resumo_diario_turma(turma, professor))
    return render(request, "gestao/professor_diario_real.html", {
        "professor": professor,
        "perfil": perfil,
        "vinculos": vinculos,
        "horarios": horarios,
        "dados": dados,
        "hoje": date.today(),
    })


@login_required
def gestao_aluno_diario_completo(request, aluno_id):
    """Ficha consolidada do aluno: dados, frequência por disciplina/mês, notas, pareceres e histórico."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    turma = aluno.turma
    disciplinas = _disciplinas_da_turma(turma)
    if not disciplinas.exists():
        disciplinas = Disciplina.objects.filter(
            models.Q(nota__aluno=aluno) | models.Q(frequencia__aluno=aluno)
        ).distinct().order_by("nome")
    linhas = []
    for disciplina in disciplinas:
        frequencias = Frequencia.objects.filter(aluno=aluno, disciplina=disciplina).order_by("data")
        por_mes = []
        ano_base = turma.ano_letivo.ano if turma and turma.ano_letivo else date.today().year
        for mes in range(1, 13):
            registros = frequencias.filter(data__year=ano_base, data__month=mes)
            total = registros.count()
            faltas = registros.filter(presente=False).count()
            fj = registros.filter(observacao__icontains="Falta justificada").count()
            por_mes.append({
                "mes": calendar.month_name[mes].capitalize(),
                "total": total,
                "faltas": faltas,
                "fj": fj,
                "presencas": total - faltas,
            })
        notas = Nota.objects.filter(aluno=aluno, turma=turma, disciplina=disciplina).order_by("bimestre")
        linhas.append({
            "disciplina": disciplina,
            "por_mes": por_mes,
            "notas": notas,
            "aulas": ConteudoAula.objects.filter(turma=turma, disciplina=disciplina).order_by("-data")[:12],
            "faltas_total": frequencias.filter(presente=False).count(),
            "fj_total": frequencias.filter(observacao__icontains="Falta justificada").count(),
        })
    return render(request, "gestao/aluno_diario_completo.html", {
        "aluno": aluno,
        "turma": turma,
        "escola": Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first(),
        "linhas": linhas,
        "historicos": HistoricoAluno.objects.filter(aluno=aluno).select_related("registrado_por")[:30],
        "pareceres": ParecerAluno.objects.filter(aluno=aluno).select_related("professor")[:20],
        "documentos": DocumentoGerado.objects.filter(aluno=aluno).select_related("gerado_por")[:20],
        "hoje": date.today(),
    })


@login_required
def gestao_diario_mapa_operacional(request):
    """Mapa de entrada para a gestão clicar na turma/aluno e abrir o diário escolar operacional."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola = Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first()
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    linhas = []
    for turma in turmas:
        vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related("professor", "disciplina")
        horarios = HorarioAula.objects.filter(turma=turma, ativo=True)
        alunos = turma.alunos.filter(ativo=True).order_by("nome")
        faltas = Frequencia.objects.filter(turma=turma, presente=False).exclude(observacao__icontains="justificada").count()
        fj = Frequencia.objects.filter(turma=turma, observacao__icontains="justificada").count()
        aulas = ConteudoAula.objects.filter(turma=turma).count()
        linhas.append({
            "turma": turma,
            "alunos": alunos[:8],
            "total_alunos": alunos.count(),
            "professores": get_user_model().objects.filter(id__in=vinculos.values_list("professor_id", flat=True)).distinct(),
            "disciplinas": Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct(),
            "horarios": horarios.count(),
            "faltas": faltas,
            "fj": fj,
            "aulas": aulas,
        })
    return render(request, "gestao/diario_mapa_operacional.html", {
        "escola": escola,
        "linhas": linhas,
        "hoje": date.today(),
    })


@login_required
def gestao_aluno_diario_operacional(request, aluno_id):
    """Gestão clica no aluno e abre diário completo ligado à turma, disciplinas, horários e frequência."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    contexto = _diario_aluno_contexto(aluno)
    return render(request, "gestao/aluno_diario_operacional.html", contexto)


@login_required
def professor_aluno_diario_operacional(request, turma_id, aluno_id):
    """Professor abre o diário do aluno somente dentro de suas turmas e disciplinas vinculadas."""
    if not usuario_professor(request.user):
        if usuario_gestor(request.user):
            return redirect("gestao_aluno_diario_operacional", aluno_id=aluno_id)
        return render(request, "core/acesso_negado.html")
    turma = get_object_or_404(_turmas_visiveis_para_usuario(request.user), id=turma_id)
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id, turma=turma)
    contexto = _diario_aluno_contexto(aluno, request.user, True)
    return render(request, "core/professor_aluno_diario_operacional.html", contexto)


@login_required
def professor_lancamento_frequencia_aluno(request, turma_id, aluno_id):
    """Lançamento oficial por aluno: data + disciplina + P/F/FJ, obedecendo vínculos do professor."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    turma = get_object_or_404(_turmas_visiveis_para_usuario(request.user), id=turma_id)
    aluno = get_object_or_404(Aluno.objects.select_related("turma"), id=aluno_id, turma=turma)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, turma=turma, ativo=True).select_related("disciplina")
    disciplinas = Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct().order_by("nome")
    data_str = request.POST.get("data") or request.GET.get("data") or date.today().isoformat()
    try:
        data_lancamento = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        data_lancamento = date.today()
    if request.method == "POST":
        for disciplina in disciplinas:
            status = request.POST.get(f"status_{disciplina.id}", "P")
            if status not in ["P", "F", "FJ"]:
                status = "P"
            presente = status in ["P", "FJ"]
            observacao = ""
            if status == "FJ":
                observacao = "Falta justificada"
            elif status == "F":
                observacao = "Falta"
            Frequencia.objects.update_or_create(
                aluno=aluno,
                disciplina=disciplina,
                data=data_lancamento,
                defaults={"turma": turma, "presente": presente, "status": status, "observacao": observacao},
            )
        messages.success(request, "Frequência oficial do aluno atualizada com P/F/FJ.")
        return redirect("professor_aluno_diario_operacional", turma_id=turma.id, aluno_id=aluno.id)
    linhas = []
    for disciplina in disciplinas:
        registro = Frequencia.objects.filter(aluno=aluno, turma=turma, disciplina=disciplina, data=data_lancamento).first()
        linhas.append({"disciplina": disciplina, "status": _status_frequencia_oficial(registro) or "P"})
    return render(request, "core/professor_lancamento_frequencia_aluno.html", {
        "aluno": aluno,
        "turma": turma,
        "linhas": linhas,
        "data_lancamento": data_lancamento,
        "hoje": date.today(),
    })


@login_required
def gestao_conferencia_vinculos_horarios(request):
    """Conferência de gestão: professores, vínculos e horários cadastrados para validar o diário escolar."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    Usuario = get_user_model()
    professores = Usuario.objects.filter(tipo="PROF").order_by("first_name", "username")
    linhas = []
    for professor in professores:
        vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
        horarios = HorarioAula.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
        linhas.append({
            "professor": professor,
            "vinculos": vinculos,
            "horarios": horarios,
            "turmas": Turma.objects.filter(id__in=vinculos.values_list("turma_id", flat=True)).distinct(),
            "disciplinas": Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct(),
            "pendente": not vinculos.exists() or not horarios.exists(),
        })
    return render(request, "gestao/conferencia_vinculos_horarios.html", {
        "linhas": linhas,
        "pendentes": sum(1 for item in linhas if item["pendente"]),
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_diario_real(request):
    """Checkup geral do projeto após as etapas 91–114, antes da continuação operacional."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    resumo, linhas_turmas = _checkup_diario_real()
    return render(request, "gestao/checkup_diario_real.html", {
        "resumo": resumo,
        "linhas": linhas_turmas,
        "hoje": date.today(),
    })


@login_required
def gestao_matriz_turnos_oficial(request):
    """Matriz visual por turno real solicitado: manhã, tarde e noite/EJA."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    _, linhas_turmas = _checkup_diario_real()
    grupos = {"Manhã": [], "Tarde": [], "Noite/EJA": [], "Pendente": []}
    for item in linhas_turmas:
        chave = item["turno_real"] if item["turno_real"] in grupos else "Pendente"
        grupos[chave].append(item)
    metas = {
        "Manhã": "5 turmas: 1º ao 5º ano",
        "Tarde": "8 turmas: 6º ao 9º + 1ª, 2ª e 3ª série do Ensino Médio",
        "Noite/EJA": "5 turmas EJA",
        "Pendente": "Turmas sem turno definido para ajuste da gestão",
    }
    grupos_lista = []
    for nome, itens in grupos.items():
        grupos_lista.append({"nome": nome, "meta": metas[nome], "itens": itens})
    return render(request, "gestao/matriz_turnos_oficial.html", {
        "grupos_lista": grupos_lista,
        "hoje": date.today(),
    })


@login_required
def gestao_lacunas_diario_real(request):
    """Lista objetiva de lacunas para não perder escola, ano letivo, professor, disciplina, horário e frequência."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    resumo, linhas_turmas = _checkup_diario_real()
    lacunas = []
    for item in linhas_turmas:
        problemas = []
        if item["alunos"] == 0:
            problemas.append("sem alunos ativos")
        if item["vinculos"] == 0:
            problemas.append("sem professor/disciplina vinculado")
        if item["horarios"] == 0:
            problemas.append("sem horário semanal")
        if item["frequencias"] == 0:
            problemas.append("sem frequência lançada")
        if item["aulas"] == 0:
            problemas.append("sem registro mensal de aula")
        if problemas:
            lacunas.append({"turma": item["turma"], "problemas": problemas, "item": item})
    return render(request, "gestao/lacunas_diario_real.html", {
        "resumo": resumo,
        "lacunas": lacunas,
        "hoje": date.today(),
    })


@login_required
def professor_checkup_meu_diario(request):
    """Checkup do professor: mostra o que veio automaticamente da gestão/admin."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina", "ano_letivo")
    horarios = HorarioAula.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina").order_by("dia_semana", "ordem")
    linhas = []
    for vinculo in vinculos:
        turma = vinculo.turma
        disciplina = vinculo.disciplina
        freq = Frequencia.objects.filter(turma=turma, disciplina=disciplina)
        aulas = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina)
        linhas.append({
            "vinculo": vinculo,
            "alunos": turma.alunos.filter(ativo=True).count(),
            "horarios": horarios.filter(turma=turma, disciplina=disciplina),
            "frequencias": freq.count(),
            "faltas": freq.filter(presente=False).exclude(observacao__icontains="justificada").count(),
            "fj": freq.filter(observacao__icontains="justificada").count(),
            "aulas": aulas.count(),
        })
    return render(request, "core/professor_checkup_meu_diario.html", {
        "linhas": linhas,
        "total_vinculos": vinculos.count(),
        "total_horarios": horarios.count(),
        "hoje": date.today(),
    })




@login_required
def gestao_consolidado_mensal_diario_real(request):
    """Gestão acompanha mês oficial: escola, ano letivo, turmas, professores, disciplinas, P/F/FJ e aulas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    turmas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor").prefetch_related("alunos")
    if ano_letivo:
        turmas = turmas.filter(ano_letivo=ano_letivo)
    linhas = []
    for turma in turmas.order_by("turno", "nome"):
        disciplinas, vinculos = _disciplinas_vinculadas_por_turma_professor(turma)
        blocos = [_linha_consolidado_mensal(turma, disciplina, inicio, fim) for disciplina in disciplinas]
        linhas.append({
            "turma": turma,
            "turno_oficial": _turma_turno_normalizado(turma),
            "professor_regente": turma.professor,
            "vinculos": vinculos,
            "disciplinas": blocos,
            "total_alunos": turma.alunos.filter(ativo=True).count(),
            "pendente": any(b["sem_aula"] or b["sem_frequencia"] for b in blocos) or not blocos,
        })
    return render(request, "gestao/consolidado_mensal_diario_real.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "linhas": linhas,
        "hoje": date.today(),
    })


@login_required
def gestao_aluno_linha_do_tempo_oficial(request, aluno_id):
    """Gestão clica no aluno e vê linha do tempo completa: dados, disciplinas, frequência, aulas e observações."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    contexto = _diario_aluno_contexto(aluno)
    eventos = []
    for freq in Frequencia.objects.filter(aluno=aluno).select_related("disciplina", "turma").order_by("-data")[:80]:
        eventos.append({"data": freq.data, "tipo": "Frequência", "titulo": freq.disciplina.nome, "texto": _status_frequencia_oficial(freq), "extra": freq.observacao or ""})
    for aula in ConteudoAula.objects.filter(turma=aluno.turma).select_related("disciplina", "professor").order_by("-data")[:80]:
        eventos.append({"data": aula.data, "tipo": "Aula", "titulo": aula.disciplina.nome, "texto": aula.descricao, "extra": _nome_professor(aula.professor)})
    eventos = sorted(eventos, key=lambda item: item["data"], reverse=True)[:120]
    contexto.update({"eventos": eventos})
    return render(request, "gestao/aluno_linha_do_tempo_oficial.html", contexto)


@login_required
def professor_registro_aula_mensal_oficial(request):
    """Registro mensal de aulas com turma/disciplina vindas automaticamente dos vínculos da gestão."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina")
    turma_id = request.POST.get("turma") or request.GET.get("turma")
    disciplina_id = request.POST.get("disciplina") or request.GET.get("disciplina")
    data_str = request.POST.get("data") or date.today().isoformat()
    if request.method == "POST":
        turma = get_object_or_404(_turmas_visiveis_para_usuario(request.user), id=turma_id)
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)
        if not vinculos.filter(turma=turma, disciplina=disciplina).exists():
            return render(request, "core/acesso_negado.html")
        try:
            data_aula = datetime.strptime(data_str, "%Y-%m-%d").date()
        except Exception:
            data_aula = date.today()
        descricao = (request.POST.get("descricao") or "").strip()
        observacoes = (request.POST.get("observacoes") or "").strip()
        if descricao:
            ConteudoAula.objects.create(turma=turma, disciplina=disciplina, professor=request.user, data=data_aula, descricao=descricao, observacoes=observacoes)
            messages.success(request, "Registro mensal de aula salvo no Diário Oficial.")
            return redirect("professor_consolidado_mensal")
        messages.error(request, "Informe o conteúdo/descrição da aula.")
    return render(request, "core/professor_registro_aula_mensal_oficial.html", {
        "vinculos": vinculos,
        "data_padrao": date.today(),
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_geral_diario_real_127(request):
    """Checkup geral consolidando 91–126 antes da continuidade 127–132."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    total_turmas = Turma.objects.filter(ativa=True).count()
    total_alunos = Aluno.objects.filter(ativo=True).count()
    total_professores = get_user_model().objects.filter(tipo="PROF").count()
    total_vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).count()
    total_horarios = HorarioAula.objects.filter(ativo=True).count()
    total_freq = Frequencia.objects.count()
    total_aulas = ConteudoAula.objects.count()
    cards = [
        {"titulo": "Identificação da escola", "valor": escola.nome if escola else "Pendente", "ok": escola is not None},
        {"titulo": "Ano letivo ativo", "valor": ano_letivo.ano if ano_letivo else "Pendente", "ok": ano_letivo is not None},
        {"titulo": "Turmas ativas", "valor": total_turmas, "ok": total_turmas > 0},
        {"titulo": "Alunos ativos", "valor": total_alunos, "ok": total_alunos > 0},
        {"titulo": "Professores do admin", "valor": total_professores, "ok": total_professores > 0},
        {"titulo": "Vínculos professor/disciplina", "valor": total_vinculos, "ok": total_vinculos > 0},
        {"titulo": "Horários semanais", "valor": total_horarios, "ok": total_horarios > 0},
        {"titulo": "Frequência P/F/FJ", "valor": total_freq, "ok": total_freq > 0},
        {"titulo": "Registros mensais de aula", "valor": total_aulas, "ok": total_aulas > 0},
    ]
    pendencias = _linhas_pendencias_diario()[:12]
    return render(request, "gestao/checkup_geral_diario_real_127.html", {
        "cards": cards,
        "pendencias": pendencias,
        "hoje": date.today(),
    })


@login_required
def gestao_auditoria_diario_turma(request, turma_id):
    """Auditoria oficial por turma: escola, ano, série/turma/turno, disciplinas, professores, horários, frequência e aulas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    turma = get_object_or_404(Turma.objects.select_related("ano_letivo", "professor"), id=turma_id)
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    contexto = _resumo_integridade_diario_turma(turma, inicio, fim)
    contexto.update({
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "inicio": inicio,
        "fim": fim,
    })
    return render(request, "gestao/auditoria_diario_turma.html", contexto)


@login_required
def gestao_pendencias_diario_oficial(request):
    """Mapa de pendências reais do diário por turma/disciplina para o gestor corrigir no admin/gestão."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas = _linhas_pendencias_diario(inicio, fim)
    return render(request, "gestao/pendencias_diario_oficial.html", {
        "linhas": linhas,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "total_pendencias": sum(item["total_pendencias"] for item in linhas),
        "hoje": date.today(),
    })


@login_required
def gestao_pacote_oficial_aluno_diario(request, aluno_id):
    """Pacote oficial do aluno clicável pela gestão, mantendo ficha, linha do tempo, P/F/FJ e aulas da turma."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    contexto = _diario_aluno_contexto(aluno)
    resumo_turma = _resumo_integridade_diario_turma(aluno.turma)
    contexto.update({
        "resumo_turma": resumo_turma,
        "documentos": DocumentoGerado.objects.filter(aluno=aluno).order_by("-criado_em")[:12],
        "pareceres": ParecerAluno.objects.filter(aluno=aluno).select_related("professor").order_by("-criado_em")[:12],
        "historico": HistoricoAluno.objects.filter(aluno=aluno).order_by("-data", "-criado_em")[:12],
        "hoje": date.today(),
    })
    return render(request, "gestao/pacote_oficial_aluno_diario.html", contexto)


@login_required
def professor_diario_classe_impressao_oficial(request):
    """Professor imprime/consulta o diário de classe oficial com dados vindos automaticamente dos vínculos da gestão."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    turma_id = request.GET.get("turma")
    disciplina_id = request.GET.get("disciplina")
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina", "ano_letivo").order_by("turma__nome", "disciplina__nome")
    vinculo_atual = None
    if turma_id and disciplina_id:
        vinculo_atual = vinculos.filter(turma_id=turma_id, disciplina_id=disciplina_id).first()
    if vinculo_atual is None:
        vinculo_atual = vinculos.first()
    contexto = {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "professor": request.user,
        "vinculos": vinculos,
        "vinculo_atual": vinculo_atual,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    }
    if vinculo_atual:
        turma = vinculo_atual.turma
        disciplina = vinculo_atual.disciplina
        alunos = turma.alunos.filter(ativo=True).order_by("nome")
        linhas = []
        for aluno in alunos:
            freq = Frequencia.objects.filter(aluno=aluno, turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
            linhas.append({"aluno": aluno, "frequencia": _contagens_oficiais_frequencia(freq), "registros": freq.order_by("data")})
        contexto.update({
            "turma": turma,
            "disciplina": disciplina,
            "alunos_linhas": linhas,
            "horarios": HorarioAula.objects.filter(professor=request.user, turma=turma, disciplina=disciplina, ativo=True).order_by("dia_semana", "ordem", "hora_inicio"),
            "aulas": ConteudoAula.objects.filter(professor=request.user, turma=turma, disciplina=disciplina, data__gte=inicio, data__lte=fim).order_by("data"),
        })
    return render(request, "core/professor_diario_classe_impressao_oficial.html", contexto)


@login_required
def gestao_checkup_geral_diario_real_133(request):
    """Checkup geral atual antes da continuidade: escola, ano, turmas, professores, vínculos, horários, frequência e aulas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    resumo = _resumo_checkup_diario_real_atual()
    pendencias = _linhas_pendencias_diario()[:20]
    return render(request, "gestao/checkup_geral_diario_real_133.html", {
        "resumo": resumo,
        "pendencias": pendencias,
        "hoje": date.today(),
    })


@login_required
def gestao_conferencia_anual_aluno_diario(request, aluno_id):
    """Gestor clica no aluno e vê o ano letivo completo por disciplina, P/F/FJ, aulas e últimos lançamentos."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    ano = request.GET.get("ano")
    try:
        ano_int = int(ano) if ano else (ano_letivo.ano if ano_letivo else date.today().year)
    except Exception:
        ano_int = date.today().year
    linhas = _linhas_conferencia_anual_aluno(aluno, ano_int)
    return render(request, "gestao/aluno_conferencia_anual_diario.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "ano": ano_int,
        "aluno": aluno,
        "turma": aluno.turma,
        "linhas": linhas,
        "hoje": date.today(),
    })


@login_required
def professor_mapa_frequencia_anual_disciplina(request):
    """Professor vê suas turmas/disciplinas do ano com P/F/FJ separado e sem pegar turma de outro professor."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    ano = request.GET.get("ano")
    try:
        ano_int = int(ano) if ano else date.today().year
    except Exception:
        ano_int = date.today().year
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina", "ano_letivo").order_by("turma__nome", "disciplina__nome")
    linhas = []
    for vinculo in vinculos:
        freq = Frequencia.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, data__year=ano_int)
        aulas = ConteudoAula.objects.filter(professor=request.user, turma=vinculo.turma, disciplina=vinculo.disciplina, data__year=ano_int)
        linhas.append({
            "vinculo": vinculo,
            "frequencia": _contagens_oficiais_frequencia(freq),
            "aulas": aulas.count(),
            "alunos": vinculo.turma.alunos.filter(ativo=True).count(),
            "horarios": HorarioAula.objects.filter(professor=request.user, turma=vinculo.turma, disciplina=vinculo.disciplina, ativo=True),
        })
    return render(request, "core/professor_mapa_frequencia_anual_disciplina.html", {"linhas": linhas, "ano": ano_int, "hoje": date.today()})


@login_required
def gestao_prontidao_diario_real_139(request):
    """Painel de prontidão mensal: escola, ano letivo, turma, turno, professor, disciplina, horários, frequência e aulas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas, totais = _resumo_prontidao_diario_real(ano_letivo, inicio, fim)
    return render(request, "gestao/prontidao_diario_real_139.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "linhas": linhas,
        "totais": totais,
        "hoje": date.today(),
    })


@login_required
def professor_fechamento_mensal_diario_139(request):
    """Professor confere mês antes de entregar: vínculo oficial, horário, frequência P/F/FJ e aulas."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina", "ano_letivo").order_by("turma__nome", "disciplina__nome")
    linhas = []
    totais = {"vinculos": 0, "ok": 0, "pendentes": 0, "aulas": 0, "frequencias": 0}
    for vinculo in vinculos:
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user)
        alunos = vinculo.turma.alunos.filter(ativo=True).order_by("nome")
        alunos_linhas = []
        for aluno in alunos:
            freq_aluno = Frequencia.objects.filter(aluno=aluno, turma=vinculo.turma, disciplina=vinculo.disciplina, data__gte=inicio, data__lte=fim)
            alunos_linhas.append({"aluno": aluno, "contagens": _contagens_oficiais_frequencia(freq_aluno), "datas": freq_aluno.order_by("data")})
        linhas.append({"vinculo": vinculo, "bloco": bloco, "alunos": alunos_linhas})
        totais["vinculos"] += 1
        totais["aulas"] += bloco["aulas_count"]
        totais["frequencias"] += bloco["frequencia"]["total"]
        if bloco["ok"]:
            totais["ok"] += 1
        else:
            totais["pendentes"] += 1
    return render(request, "core/professor_fechamento_mensal_diario_139.html", {
        "linhas": linhas,
        "totais": totais,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def professor_prontidao_diario_139(request):
    """Resumo rápido do professor para saber o que falta lançar por turma/disciplina."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina").order_by("turma__turno", "turma__nome", "disciplina__nome")
    cards = []
    for vinculo in vinculos:
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user)
        cards.append({"vinculo": vinculo, "bloco": bloco})
    return render(request, "core/professor_prontidao_diario_139.html", {
        "cards": cards,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def gestao_fechamento_oficial_diario_145(request):
    """Fechamento oficial mensal do diário, mantendo escola, ano letivo, turma, turno, professor e disciplina."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas, totais = _resumo_prontidao_diario_real(ano_letivo, inicio, fim)
    blocos_finais = []
    for linha in linhas:
        for bloco in linha["blocos"]:
            professores = ProfessorTurmaDisciplina.objects.filter(
                turma=linha["turma"],
                disciplina=bloco["disciplina"],
                ativo=True,
            ).select_related("professor")
            blocos_finais.append({
                "turma": linha["turma"],
                "turno": linha["turno_oficial"],
                "disciplina": bloco["disciplina"],
                "professores": professores,
                "frequencia": bloco["frequencia"],
                "aulas_count": bloco["aulas_count"],
                "horarios_count": bloco["horarios_count"],
                "pendencias": bloco["pendencias"],
                "ok": bloco["ok"],
            })
    return render(request, "gestao/fechamento_oficial_diario_145.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "linhas": linhas,
        "blocos_finais": blocos_finais,
        "totais": totais,
        "hoje": date.today(),
    })


@login_required
def professor_entrega_mensal_diario_145(request):
    """Entrega mensal do professor com vínculos automáticos da gestão e status por disciplina."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(
        professor=request.user,
        ativo=True,
    ).select_related("turma", "disciplina", "ano_letivo").order_by("turma__turno", "turma__nome", "disciplina__nome")
    linhas = []
    totais = {"vinculos": 0, "prontos": 0, "pendentes": 0, "frequencias": 0, "aulas": 0}
    for vinculo in vinculos:
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user)
        linhas.append({"vinculo": vinculo, "bloco": bloco, "turno": _turma_turno_normalizado(vinculo.turma)})
        totais["vinculos"] += 1
        totais["frequencias"] += bloco["frequencia"]["total"]
        totais["aulas"] += bloco["aulas_count"]
        if bloco["ok"]:
            totais["prontos"] += 1
        else:
            totais["pendentes"] += 1
    return render(request, "core/professor_entrega_mensal_diario_145.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "linhas": linhas,
        "totais": totais,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def gestao_aluno_prontuario_anual_diario_145(request, aluno_id):
    """Prontuário anual do aluno: gestor clica no aluno e acompanha P/F/FJ, aulas e disciplinas mês a mês."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    ano = int(request.GET.get("ano") or (ano_letivo.ano if ano_letivo else date.today().year))
    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=aluno.turma, ativo=True).select_related("professor", "disciplina")
    disciplinas = Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct().order_by("nome")
    if not disciplinas.exists():
        disciplinas = _disciplinas_da_turma(aluno.turma)
    meses = []
    totais_anuais = {"presencas": 0, "faltas": 0, "fj": 0, "total": 0, "aulas": 0}
    for periodo in _periodos_mensais_ano(ano):
        linhas_disciplina = []
        for disciplina in disciplinas:
            freq = Frequencia.objects.filter(
                aluno=aluno,
                turma=aluno.turma,
                disciplina=disciplina,
                data__gte=periodo["inicio"],
                data__lte=periodo["fim"],
            )
            aulas = ConteudoAula.objects.filter(
                turma=aluno.turma,
                disciplina=disciplina,
                data__gte=periodo["inicio"],
                data__lte=periodo["fim"],
            )
            contagens = _contagens_oficiais_frequencia(freq)
            totais_anuais["presencas"] += contagens["presencas"]
            totais_anuais["faltas"] += contagens["faltas"]
            totais_anuais["fj"] += contagens["fj"]
            totais_anuais["total"] += contagens["total"]
            totais_anuais["aulas"] += aulas.count()
            linhas_disciplina.append({
                "disciplina": disciplina,
                "professores": vinculos.filter(disciplina=disciplina),
                "frequencia": contagens,
                "aulas_count": aulas.count(),
                "pendente": contagens["total"] == 0 and aulas.count() == 0,
            })
        meses.append({"periodo": periodo, "disciplinas": linhas_disciplina})
    return render(request, "gestao/aluno_prontuario_anual_diario_145.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "aluno": aluno,
        "turma": aluno.turma,
        "ano": ano,
        "meses": meses,
        "totais_anuais": totais_anuais,
        "hoje": date.today(),
    })


@login_required
def gestao_matriz_turnos_conferencia_145(request):
    """Conferência oficial dos turnos esperados: manhã 5, tarde 8 e noite/EJA 5."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    linhas = []
    total_turmas = 0
    total_horarios = 0
    for regra in _turnos_esperados_diario_real():
        turmas = Turma.objects.filter(ativa=True)
        if ano_letivo:
            turmas = turmas.filter(ano_letivo=ano_letivo)
        turmas = [t for t in turmas.select_related("professor") if _turma_turno_normalizado(t) == regra["turno"]]
        horarios = HorarioAula.objects.filter(turma__in=turmas, ativo=True).select_related("professor", "turma", "disciplina")
        linhas.append({
            "regra": regra,
            "turmas": turmas,
            "total_turmas": len(turmas),
            "horarios": horarios.order_by("turma__nome", "dia_semana", "ordem"),
            "total_horarios": horarios.count(),
            "ok": len(turmas) == regra["esperado"],
        })
        total_turmas += len(turmas)
        total_horarios += horarios.count()
    return render(request, "gestao/matriz_turnos_conferencia_145.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "linhas": linhas,
        "total_turmas": total_turmas,
        "total_horarios": total_horarios,
        "hoje": date.today(),
    })


@login_required
def gestao_rotas_diario_real_145(request):
    """Mapa dos botões e rotas oficiais do Diário Escolar para evitar caminhos quebrados."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    return render(request, "gestao/rotas_diario_real_145.html", {
        "rotas": _rotas_diario_real_status(),
        "hoje": date.today(),
    })


@login_required
def gestao_homologacao_diario_real_151(request):
    """Homologação geral do Diário Escolar antes de novas entregas: escola, ano, turmas, vínculos, horários, frequência e aulas."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    linhas, totais = _resumo_prontidao_diario_real(saude['ano_letivo'], inicio, fim)
    cards = [
        {'titulo': 'Escola oficial', 'valor': saude['escola'].nome if saude['escola'] else 'Pendente', 'ok': bool(saude['escola'])},
        {'titulo': 'Ano letivo', 'valor': saude['ano_letivo'].ano if saude['ano_letivo'] else 'Pendente', 'ok': bool(saude['ano_letivo'])},
        {'titulo': 'Turmas ativas', 'valor': saude['turmas'].count(), 'ok': saude['turmas'].count() > 0},
        {'titulo': 'Professores', 'valor': saude['professores'].count(), 'ok': saude['professores'].count() > 0},
        {'titulo': 'Vínculos', 'valor': saude['vinculos'].count(), 'ok': saude['vinculos'].count() > 0},
        {'titulo': 'Horários', 'valor': saude['horarios'].count(), 'ok': saude['horarios'].count() > 0},
        {'titulo': 'Frequências do mês', 'valor': saude['frequencias'].count(), 'ok': saude['frequencias'].count() > 0},
        {'titulo': 'Aulas do mês', 'valor': saude['aulas'].count(), 'ok': saude['aulas'].count() > 0},
    ]
    return render(request, 'gestao/homologacao_diario_real_151.html', {
        'cards': cards, 'saude': saude, 'linhas': linhas, 'totais': totais,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_trilha_lancamentos_diario_151(request):
    """Trilha por vínculo: professor automático da gestão, turma, disciplina, turno, dias com frequência e dias com aula."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).select_related('professor', 'turma', 'disciplina', 'ano_letivo').order_by('turma__turno', 'turma__nome', 'disciplina__nome')
    linhas = []
    for vinculo in vinculos:
        dias = _dias_com_lancamento_por_vinculo(vinculo, inicio, fim, professor=vinculo.professor)
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=vinculo.professor)
        linhas.append({'vinculo': vinculo, 'turno': _turma_turno_normalizado(vinculo.turma), 'dias': dias, 'bloco': bloco})
    return render(request, 'gestao/trilha_lancamentos_diario_151.html', {
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_painel_aluno_diario_real_151(request, aluno_id):
    """Painel do aluno clicável para a gestão, juntando ficha, extrato mensal, prontuário anual e rotas oficiais."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    aluno = get_object_or_404(Aluno.objects.select_related('turma', 'turma__ano_letivo'), id=aluno_id)
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    contexto = _diario_aluno_contexto(aluno)
    linhas_mes = []
    for linha in contexto['linhas']:
        disciplina = linha['disciplina']
        freq = Frequencia.objects.filter(aluno=aluno, turma=aluno.turma, disciplina=disciplina, data__gte=inicio, data__lte=fim).order_by('data')
        aulas = ConteudoAula.objects.filter(turma=aluno.turma, disciplina=disciplina, data__gte=inicio, data__lte=fim).order_by('data')
        linhas_mes.append({'disciplina': disciplina, 'professores': linha.get('professores'), 'frequencias': freq, 'contagens': _contagens_oficiais_frequencia(freq), 'aulas': aulas})
    return render(request, 'gestao/painel_aluno_diario_real_151.html', {
        'aluno': aluno, 'turma': aluno.turma, 'contexto': contexto, 'linhas_mes': linhas_mes,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_trilha_mensal_diario_151(request):
    """Professor vê, por vínculo oficial da gestão, as datas em que lançou frequência e aula no mês."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related('turma', 'disciplina', 'ano_letivo').order_by('turma__turno', 'turma__nome', 'disciplina__nome')
    linhas = []
    for vinculo in vinculos:
        linhas.append({
            'vinculo': vinculo,
            'turno': _turma_turno_normalizado(vinculo.turma),
            'dias': _dias_com_lancamento_por_vinculo(vinculo, inicio, fim, professor=request.user),
            'bloco': _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user),
        })
    return render(request, 'core/professor_trilha_mensal_diario_151.html', {
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_resumo_anual_diario_151(request):
    """Resumo anual do professor por turma e disciplina, mantendo P/F/FJ separados e aulas por mês."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    try:
        ano = int(request.GET.get('ano') or date.today().year)
    except Exception:
        ano = date.today().year
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related('turma', 'disciplina', 'ano_letivo').order_by('turma__nome', 'disciplina__nome')
    linhas = []
    for vinculo in vinculos:
        meses = []
        for periodo in _periodos_mensais_ano(ano):
            bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, periodo['inicio'], periodo['fim'], professor=request.user)
            meses.append({'periodo': periodo, 'bloco': bloco})
        linhas.append({'vinculo': vinculo, 'turno': _turma_turno_normalizado(vinculo.turma), 'meses': meses})
    return render(request, 'core/professor_resumo_anual_diario_151.html', {'linhas': linhas, 'ano': ano, 'hoje': date.today()})


@login_required
def gestao_integridade_diario_real_157(request):
    """Painel de integridade: escola, ano letivo, vínculos, horários, frequência e aula mensal."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    turnos = _resumo_turnos_diario_real(inicio, fim)
    cards = [
        {"titulo": "Escola identificada", "valor": saude['escola'].nome if saude['escola'] else "Pendente", "ok": bool(saude['escola'])},
        {"titulo": "Ano letivo ativo", "valor": saude['ano_letivo'].ano if saude['ano_letivo'] else "Pendente", "ok": bool(saude['ano_letivo'])},
        {"titulo": "Professor automático", "valor": saude['vinculos'].count(), "ok": saude['vinculos'].count() > 0},
        {"titulo": "Horários semanais", "valor": saude['horarios'].count(), "ok": saude['horarios'].count() > 0},
        {"titulo": "Frequência do mês", "valor": saude['frequencias'].count(), "ok": True},
        {"titulo": "Aulas registradas", "valor": saude['aulas'].count(), "ok": saude['aulas'].count() > 0},
    ]
    return render(request, 'gestao/integridade_diario_real_157.html', {
        'cards': cards, 'saude': saude, 'turnos': turnos,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_matriz_turnos_diario_real_157(request):
    """Matriz por turno: manhã, tarde e noite com turmas, vínculos, horários e lançamentos."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas = _resumo_turnos_diario_real(inicio, fim)
    return render(request, 'gestao/matriz_turnos_diario_real_157.html', {
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_auditoria_fj_diario_real_157(request):
    """Auditoria de faltas justificadas separadas de presença e falta comum."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    criterio_fj = models.Q(observacao__icontains='justificada') | models.Q(observacao__icontains='fj')
    registros = Frequencia.objects.filter(criterio_fj, data__gte=inicio, data__lte=fim).select_related('aluno', 'turma', 'disciplina').order_by('-data', 'aluno__nome')
    return render(request, 'gestao/auditoria_fj_diario_real_157.html', {
        'registros': registros, 'total': registros.count(), 'mes_param': mes_param,
        'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_agenda_semanal_diario_real_157(request):
    """Agenda semanal oficial do professor, derivada dos horários cadastrados pela gestão."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    horarios = HorarioAula.objects.filter(professor=request.user, ativo=True).select_related('turma', 'disciplina').order_by('dia_semana', 'ordem', 'hora_inicio')
    dias = []
    for codigo, nome in HorarioAula.DIAS_SEMANA:
        dias.append({'codigo': codigo, 'nome': nome, 'horarios': horarios.filter(dia_semana=codigo)})
    return render(request, 'core/professor_agenda_semanal_diario_real_157.html', {
        'dias': dias, 'hoje': date.today(), 'professor_nome': _nome_professor_oficial(request.user),
    })


@login_required
def gestao_conferencia_final_diario_real_163(request):
    """Conferência final mensal: identifica escola, ano letivo, turnos, vínculos, horários, frequência e aulas."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    turnos = _resumo_turnos_diario_real(inicio, fim)
    turmas = Turma.objects.filter(ativa=True).prefetch_related('alunos').order_by('turno', 'nome')
    linhas = []
    for turma in turmas:
        vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True)
        horarios = HorarioAula.objects.filter(turma=turma, ativo=True)
        frequencias = Frequencia.objects.filter(turma=turma, data__gte=inicio, data__lte=fim)
        aulas = ConteudoAula.objects.filter(turma=turma, data__gte=inicio, data__lte=fim)
        pendencias = []
        if not vinculos.exists():
            pendencias.append('Sem professor/disciplina vinculado')
        if not horarios.exists():
            pendencias.append('Sem horários semanais')
        if not frequencias.exists():
            pendencias.append('Sem frequência mensal')
        if not aulas.exists():
            pendencias.append('Sem registro mensal de aulas')
        linhas.append({
            'turma': turma,
            'turno': _turma_turno_normalizado(turma),
            'alunos_count': turma.alunos.filter(ativo=True).count(),
            'vinculos_count': vinculos.count(),
            'horarios_count': horarios.count(),
            'frequencia': _contagens_oficiais_frequencia(frequencias),
            'aulas_count': aulas.count(),
            'pendencias': pendencias,
            'ok': not pendencias,
        })
    return render(request, 'gestao/conferencia_final_diario_real_163.html', {
        'saude': saude, 'turnos': turnos, 'linhas': linhas,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_livro_diario_turma_163(request, turma_id):
    """Livro oficial mensal da turma: professor automático, disciplinas, frequência P/F/FJ e aulas do mês."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    turma = get_object_or_404(Turma, id=turma_id)
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()
    ano_letivo = AnoLetivo.objects.filter(ativo=True).first()
    linhas = _linhas_livro_diario_turma(turma, inicio, fim)
    alunos = turma.alunos.filter(ativo=True).order_by('nome')
    return render(request, 'gestao/livro_diario_turma_163.html', {
        'escola': escola, 'ano_letivo': ano_letivo, 'turma': turma, 'alunos': alunos,
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_aluno_frequencia_anual_disciplina_163(request, aluno_id):
    """Mapa anual clicável do aluno por disciplina, separando P, F e FJ para a gestão."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    aluno = get_object_or_404(Aluno.objects.select_related('turma'), id=aluno_id)
    try:
        ano = int(request.GET.get('ano') or date.today().year)
    except Exception:
        ano = date.today().year
    disciplinas = Disciplina.objects.filter(frequencia__aluno=aluno, frequencia__data__year=ano).distinct().order_by('nome')
    linhas = []
    for disciplina in disciplinas:
        meses = []
        for periodo in _periodos_mensais_ano(ano):
            qs = Frequencia.objects.filter(aluno=aluno, disciplina=disciplina, data__gte=periodo['inicio'], data__lte=periodo['fim'])
            meses.append({'periodo': periodo, 'freq': _contagens_oficiais_frequencia(qs), 'total': qs.count()})
        linhas.append({'disciplina': disciplina, 'meses': meses})
    return render(request, 'gestao/aluno_frequencia_anual_disciplina_163.html', {
        'aluno': aluno, 'linhas': linhas, 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_livro_diario_mensal_163(request):
    """Livro mensal do professor com escola, ano letivo, turma, turno, disciplina, P/F/FJ e aulas."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()
    ano_letivo = AnoLetivo.objects.filter(ativo=True).first()
    linhas = _painel_prontidao_lancamento_professor(request.user, inicio, fim)
    return render(request, 'core/professor_livro_diario_mensal_163.html', {
        'escola': escola, 'ano_letivo': ano_letivo, 'professor_nome': _nome_professor_oficial(request.user),
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_revisao_oficial_diario_real_169(request):
    """Revisão oficial do mês: escola, ano letivo, turmas, turnos, professores, horários, frequência e aulas."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    turmas = Turma.objects.filter(ativa=True).prefetch_related('alunos').order_by('turno', 'nome')
    linhas = []
    for turma in turmas:
        vinculos = ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).select_related('professor', 'disciplina', 'ano_letivo')
        blocos = []
        for vinculo in vinculos:
            espelho = _espelho_mensal_turma_disciplina(turma, vinculo.disciplina, inicio, fim, professor=vinculo.professor)
            blocos.append({'vinculo': vinculo, 'professor_nome': _nome_professor_oficial(vinculo.professor), 'espelho': espelho})
        pendencias = []
        if not escola:
            pendencias.append('Escola não identificada')
        if not ano_letivo:
            pendencias.append('Ano letivo não identificado')
        if not turma.turno:
            pendencias.append('Turno não informado')
        if not vinculos.exists():
            pendencias.append('Sem professor/disciplina vinculado')
        if not HorarioAula.objects.filter(turma=turma, ativo=True).exists():
            pendencias.append('Sem horários cadastrados')
        linhas.append({
            'turma': turma,
            'turno': _turma_turno_normalizado(turma),
            'alunos_count': turma.alunos.filter(ativo=True).count(),
            'blocos': blocos,
            'pendencias': pendencias,
            'ok': not pendencias and bool(blocos),
        })
    return render(request, 'gestao/revisao_oficial_diario_real_169.html', {
        'escola': escola, 'ano_letivo': ano_letivo, 'linhas': linhas,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_aluno_dossie_diario_real_169(request, aluno_id):
    """Dossiê clicável do aluno: identificação, turma, frequência por disciplina e registros de aula relacionados."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    aluno = get_object_or_404(Aluno.objects.select_related('turma', 'turma__ano_letivo'), id=aluno_id)
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    disciplinas, _ = _disciplinas_vinculadas_por_turma_professor(aluno.turma)
    linhas = []
    for disciplina in disciplinas:
        freq = Frequencia.objects.filter(aluno=aluno, turma=aluno.turma, disciplina=disciplina, data__gte=inicio, data__lte=fim)
        aulas = ConteudoAula.objects.filter(turma=aluno.turma, disciplina=disciplina, data__gte=inicio, data__lte=fim).select_related('professor')
        linhas.append({
            'disciplina': disciplina,
            'frequencia': _contagens_oficiais_frequencia(freq),
            'registros': freq.order_by('data'),
            'aulas': aulas.order_by('data'),
            'ok': freq.exists() or aulas.exists(),
        })
    return render(request, 'gestao/aluno_dossie_diario_real_169.html', {
        'escola': escola, 'ano_letivo': ano_letivo, 'aluno': aluno, 'turma': aluno.turma, 'linhas': linhas,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_mapa_lancamento_diario_169(request):
    """Mapa do professor para lançar e conferir frequência/aula por turma, disciplina e data."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related('turma', 'disciplina', 'ano_letivo').order_by('turma__turno', 'turma__nome', 'disciplina__nome')
    linhas = []
    for vinculo in vinculos:
        espelho = _espelho_mensal_turma_disciplina(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user)
        linhas.append({'vinculo': vinculo, 'turno': _turma_turno_normalizado(vinculo.turma), 'espelho': espelho})
    return render(request, 'core/professor_mapa_lancamento_diario_169.html', {
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_carga_horaria_301(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    carga = carga_horaria_professor_semana(request.user)
    return render(request, "core/professor_carga_horaria_301.html", {"carga": carga, "hoje": date.today()})


@login_required
def gestao_carga_horaria_professores_301(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    linhas = carga_horaria_professores_resumo()
    total_horas = round(sum(l["horas"] for l in linhas), 2)
    total_aulas = sum(l["aulas"] for l in linhas)
    return render(request, "gestao/carga_horaria_professores_301.html", {
        "linhas": linhas,
        "total_horas": total_horas,
        "total_aulas": total_aulas,
        "hoje": date.today(),
    })


@login_required
def gestao_ia_pedagogica_901(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = {
        "modo": "Gestão",
        "subtitulo": "IA pedagógica operacional com risco escolar, faltas, FJ, turmas críticas e professores pendentes.",
        "ia_901_960": inteligencia_pedagogica_901_960(),
        "finalizacao": finalizacao_901_960(),
        "hoje": date.today(),
    }
    registrar_auditoria(request.user, "IA Pedagógica", "IA operacional 901-960 consultada")
    return render(request, "gestao/ia_pedagogica_901.html", contexto)


@login_required
def professor_ia_pedagogica_901(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = {
        "modo": "Professor",
        "subtitulo": "IA pedagógica das suas turmas com foco em frequência, conteúdo e fechamento.",
        "ia_901_960": inteligencia_pedagogica_901_960(professor=request.user),
        "finalizacao": finalizacao_901_960(professor=request.user),
        "hoje": date.today(),
    }
    return render(request, "core/professor_ia_pedagogica_901.html", contexto)

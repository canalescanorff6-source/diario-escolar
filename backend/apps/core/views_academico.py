"""Views de indicadores e acompanhamento pedagógico."""

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
    """Chamada por turma com disciplina, data e horário explícitos."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(Turma.objects.prefetch_related("alunos"), id=turma_id, ativa=True)
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")

    disciplinas = _disciplinas_da_turma(turma, request.user)
    disciplina_id = request.POST.get("disciplina") or request.GET.get("disciplina")
    disciplina = disciplinas.filter(id=disciplina_id).first() if disciplina_id else disciplinas.first()

    data_texto = request.POST.get("data") or request.GET.get("data") or date.today().isoformat()
    try:
        data_aula = datetime.strptime(data_texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        data_aula = date.today()

    try:
        aula_numero = int(request.POST.get("aula_numero") or request.GET.get("aula_numero") or 1)
    except (TypeError, ValueError):
        aula_numero = 1
    aula_numero = max(1, min(20, aula_numero))

    alunos = turma.alunos.filter(ativo=True).order_by("nome")
    if request.method == "POST":
        if disciplina is None:
            messages.warning(request, "Nenhuma disciplina vinculada a esta turma para o seu usuário.")
        else:
            for aluno in alunos:
                status = (request.POST.get(f"status_{aluno.id}") or "P").upper()
                if status not in {"P", "F", "FJ"}:
                    status = "P"
                observacao = (request.POST.get(f"obs_{aluno.id}") or "").strip()
                Frequencia.objects.update_or_create(
                    aluno=aluno,
                    disciplina=disciplina,
                    data=data_aula,
                    aula_numero=aula_numero,
                    defaults={"turma": turma, "status": status, "observacao": observacao},
                )
            registrar_auditoria(
                request.user, "Frequência", "Chamada registrada",
                objeto=f"{turma.nome} • {disciplina.nome}",
                descricao=f"{data_aula:%d/%m/%Y} • aula {aula_numero}",
            )
            messages.success(request, "Chamada salva com sucesso.")
            return redirect(
                f"{request.path}?disciplina={disciplina.id}&data={data_aula:%Y-%m-%d}&aula_numero={aula_numero}"
            )

    registros = {}
    if disciplina is not None:
        registros = {
            item.aluno_id: item
            for item in Frequencia.objects.filter(
                turma=turma, disciplina=disciplina, data=data_aula, aula_numero=aula_numero
            )
        }

    alunos_linhas = []
    for aluno in alunos:
        registro = registros.get(aluno.id)
        alunos_linhas.append({
            "aluno": aluno,
            "status": _status_frequencia(registro) or "P",
            "observacao": registro.observacao if registro else "",
        })

    total_presentes = sum(1 for item in alunos_linhas if item["status"] == "P") if registros else 0
    total_faltas = sum(1 for item in alunos_linhas if item["status"] in {"F", "FJ"}) if registros else 0
    return render(request, "core/frequencia_turma.html", {
        "turma": turma,
        "disciplinas": disciplinas,
        "disciplina": disciplina,
        "data_aula": data_aula,
        "aula_numero": aula_numero,
        "alunos_linhas": alunos_linhas,
        "total_alunos": alunos.count(),
        "total_presentes": total_presentes,
        "total_faltas": total_faltas,
    })


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

    try:
        aula_numero = int(request.POST.get("aula_numero") or request.GET.get("aula_numero") or 1)
    except (TypeError, ValueError):
        aula_numero = 1
    aula_numero = max(1, min(20, aula_numero))

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
        if disciplina is None:
            messages.warning(request, "Nenhuma disciplina cadastrada/vinculada para registrar frequência.")
            return redirect(f"{request.path}?mes={mes_param}&data={data_aula.isoformat()}&aula_numero={aula_numero}")

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
                aula_numero=aula_numero,
                defaults={
                    "presente": presente,
                    "status": status,
                    "observacao": observacao or None,
                }
            )

        messages.success(request, "Frequência mensal salva com sucesso.")

        return redirect(
            f"{request.path}?disciplina={disciplina.id}&mes={mes_param}&data={data_aula.isoformat()}&aula_numero={aula_numero}"
        )

    frequencias_mes = Frequencia.objects.filter(
        turma=turma,
        disciplina=disciplina,
        aula_numero=aula_numero,
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
        "aula_numero": aula_numero,
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
# =====================================================


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
    contexto_ia['subtitulo'] = 'Indicadores pedagógicos para turmas, notas, frequência e recuperação.'
    return render(request, 'core/assistente_pedagogico.html', contexto_ia)


@login_required
def gestao_ia_pedagogica(request):
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')

    contexto_ia = montar_analise_pedagogica_avancada()
    contexto_ia['modo'] = 'Gestão'
    contexto_ia['subtitulo'] = 'Leitura executiva de risco pedagógico, frequência, médias e intervenção escolar.'
    return render(request, 'gestao/assistente_pedagogico.html', contexto_ia)


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
        "total_aulas_registradas": sum(item.get("registros_aulas", 0) for item in dados),
        "conteudos_hoje": ConteudoAula.objects.filter(professor=request.user, data=date.today()).count(),
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
def gestao_carga_horaria_professores(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    User = get_user_model()

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "vinculo":
            professor_id = request.POST.get("professor")
            turma_id = request.POST.get("turma")
            disciplina_id = request.POST.get("disciplina")
            ano_id = request.POST.get("ano_letivo") or None

            if professor_id and turma_id and disciplina_id:
                ProfessorTurmaDisciplina.objects.get_or_create(
                    professor_id=professor_id,
                    turma_id=turma_id,
                    disciplina_id=disciplina_id,
                    ano_letivo_id=ano_id,
                    defaults={"ativo": True},
                )
                messages.success(request, "Vínculo professor/turma/disciplina salvo com sucesso.")
            else:
                messages.error(request, "Selecione professor, turma e disciplina para criar o vínculo.")

        elif acao == "horario":
            professor_id = request.POST.get("professor")
            turma_id = request.POST.get("turma")
            disciplina_id = request.POST.get("disciplina")
            dia_semana = int(request.POST.get("dia_semana") or 1)
            ordem = int(request.POST.get("ordem") or request.POST.get("horario_numero") or 1)

            if professor_id and turma_id and disciplina_id:
                horario, criado = HorarioAula.objects.get_or_create(
                    professor_id=professor_id,
                    turma_id=turma_id,
                    disciplina_id=disciplina_id,
                    dia_semana=dia_semana,
                    ordem=ordem,
                    defaults={
                        "horario_numero": ordem,
                        "hora_inicio": _parse_hora(request.POST.get("hora_inicio"), "07:00"),
                        "hora_fim": _parse_hora(request.POST.get("hora_fim"), "07:45"),
                        "turno": request.POST.get("turno") or None,
                        "ativo": True,
                    },
                )

                if not criado:
                    horario.horario_numero = ordem
                    horario.hora_inicio = _parse_hora(request.POST.get("hora_inicio"), "07:00")
                    horario.hora_fim = _parse_hora(request.POST.get("hora_fim"), "07:45")
                    horario.turno = request.POST.get("turno") or None
                    horario.ativo = True
                    horario.save()

                ProfessorTurmaDisciplina.objects.get_or_create(
                    professor_id=professor_id,
                    turma_id=turma_id,
                    disciplina_id=disciplina_id,
                    ano_letivo_id=request.POST.get("ano_letivo") or None,
                    defaults={"ativo": True},
                )

                messages.success(request, "Horário semanal salvo e vinculado ao professor.")
            else:
                messages.error(request, "Selecione professor, turma e disciplina para cadastrar o horário.")

        return redirect("gestao_carga_horaria")

    linhas = carga_horaria_professores_resumo()
    total_horas = round(sum(l["horas"] for l in linhas), 2)
    total_aulas = sum(l["aulas"] for l in linhas)
    return render(request, "gestao/carga_horaria_professores.html", {
        "linhas": linhas,
        "total_horas": total_horas,
        "total_aulas": total_aulas,
        "professores": User.objects.filter(tipo="PROF").order_by("first_name", "username"),
        "turmas": Turma.objects.filter(ativa=True).select_related("ano_letivo").order_by("nome"),
        "disciplinas": Disciplina.objects.all().order_by("nome"),
        "anos": AnoLetivo.objects.all().order_by("-ano"),
        "dias_semana": HorarioAula.DIAS_SEMANA,
        "turnos": HorarioAula.TURNO_CHOICES,
        "horarios": HorarioAula.objects.select_related("professor", "turma", "disciplina").filter(ativo=True).order_by("dia_semana", "ordem", "hora_inicio")[:80],
        "hoje": date.today(),
    })



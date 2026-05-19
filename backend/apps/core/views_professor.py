# Camada de views professor — refatoração real etapa 1221-1280.
# Mantém os nomes públicos usados pelas URLs, mas tira o peso do antigo views.py.

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

    # Etapas 229–234: seletores oficiais centralizados para evitar repetir
    # as mesmas queries em cada tela do professor.
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

    # Etapas 241–246: fluxo único centralizado em utilitário para evitar
    # recriar cards repetidos de Diário/Frequência/Aulas no painel.
    fluxo_operacional = fluxo_professor_unificado(
        total_turmas=total_turmas,
        total_disciplinas=disciplinas.count(),
        total_horarios=horarios.count(),
        total_pendencias=len(pendencias_professor),
    )

    agenda = []
    for horario in horarios[:8]:
        agenda.append({
            "horario": f"{horario.hora_inicio.strftime('%H:%M')} - {horario.hora_fim.strftime('%H:%M')}",
            "titulo": f"{horario.turma.nome} • {horario.disciplina.nome}",
            "turno": horario.get_turno_display() if horario.turno else "Turno não informado",
        })

    atalhos_diario = [
        {"titulo": "Lançamentos oficiais", "descricao": "Diário, frequência P/F/FJ e registro de aulas reunidos em uma única entrada.", "url": "professor_diario_oficial", "icone": "📘"},
        {"titulo": "Fechamento", "descricao": "Prontidão, livro mensal e entrega oficial do professor sem novo lançamento duplicado.", "url": "professor_prontidao_lancamentos_163", "icone": "📕"},
    ]

    diagnostico_painel = {
        "fluxo_unico": True,
        "diario_frequencia_agrupados": True,
        "turmas_por_vinculo": total_turmas,
        "disciplinas_por_vinculo": disciplinas.count(),
        "horarios_por_gestao": horarios.count(),
    }

    context = {
        "dados_turmas": dados_turmas,
        "total_turmas": total_turmas,
        "total_alunos": total_alunos,
        "total_risco": total_risco,
        "media_geral": media_geral,
        "frequencia_media": frequencia_media,
        "total_faltas": total_faltas,
        "total_fj": total_fj,
        "total_faltas_oficiais": total_faltas_oficiais,
        "total_disciplinas": disciplinas.count(),
        "total_horarios": horarios.count(),
        "total_aulas_registradas": total_aulas_registradas,
        "total_vinculos": vinculos.count(),
        "carga_horaria_semana": carga_horaria_professor_semana(professor),
        "aulas_hoje": aulas_professor_hoje(professor),
        "agenda": agenda,
        "atalhos_diario": atalhos_diario,
        "diagnostico_painel": diagnostico_painel,
        "fluxo_operacional": fluxo_operacional,
        "pendencias_professor": pendencias_professor,
        "resumo_861_900_professor": resumo_professor_861_900(professor),
        "finalizacao_901_960_professor": finalizacao_901_960(professor=professor),
        "mega_checkup_961_1000_professor": mega_checkup_961_1000(professor=professor),
        "mega_checkup_1001_1080_professor": mega_checkup_1001_1080(professor=professor),
        "hoje": date.today(),
        "grafico_labels": json.dumps(["Turmas", "Disciplinas", "Horários", "Aulas", "Risco"]),
        "grafico_dados": json.dumps([total_turmas, disciplinas.count(), horarios.count(), total_aulas_registradas, total_risco]),
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

    if request.user.tipo != "PROF":
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(
        Turma.objects.prefetch_related("alunos"),
        id=turma_id
    )

    alunos = turma.alunos.all()

    total_alunos = alunos.count()

    total_presencas = Frequencia.objects.filter(
        turma=turma,
        presente=True
    ).count()

    total_frequencias = Frequencia.objects.filter(
        turma=turma
    ).count()

    frequencia_media = 0

    if total_frequencias > 0:
        frequencia_media = round(
            (total_presencas / total_frequencias) * 100,
            1
        )

    alunos_formatados = []

    for aluno in alunos:

        frequencias_aluno = Frequencia.objects.filter(
            turma=turma,
            aluno=aluno
        )

        total_aulas = frequencias_aluno.count()

        presencas = frequencias_aluno.filter(
            presente=True
        ).count()

        frequencia = 0

        if total_aulas > 0:
            frequencia = round(
                (presencas / total_aulas) * 100,
                1
            )

        media = getattr(aluno, "media", 8.5)

        status = "✅ Estável"

        if frequencia < 75:
            status = "🚨 Crítico"

        elif frequencia < 85:
            status = "⚠ Atenção"

        alunos_formatados.append({

            "obj": aluno,

            "id": aluno.id,

            "nome": aluno.nome,

            "matricula": aluno.matricula,

            "frequencia": frequencia,

            "media": media,

            "status": status,

        })

    context = {

        "turma": turma,

        "alunos": alunos_formatados,

        "frequencia_media": frequencia_media,

        "media_geral": 8.5,

        "total_alunos": total_alunos,

    }

    return render(
        request,
        "core/turma_detalhe.html",
        context
    )


# =====================================================
# NOTAS TURMA
# =====================================================

@login_required
def notas_turma(request, turma_id):

    if not (usuario_professor(request.user) or usuario_gestor(request.user)):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(
        Turma.objects.prefetch_related("alunos"),
        id=turma_id
    )

    disciplina = get_disciplina_padrao()
    alunos = turma.alunos.all()

    def decimal_ou_none(valor):
        if valor in (None, ""):
            return None

        try:
            numero = Decimal(str(valor).replace(",", "."))
        except (InvalidOperation, ValueError):
            return None

        if numero < 0:
            numero = Decimal("0")

        if numero > 10:
            numero = Decimal("10")

        return numero

    def bimestre_completo(numero_bimestre):
        if not alunos.exists():
            return False

        notas = Nota.objects.filter(
            turma=turma,
            disciplina=disciplina,
            bimestre=numero_bimestre,
            nota1__isnull=False,
            nota2__isnull=False,
            nota3__isnull=False,
        ).count()

        return notas == alunos.count()

    def proximo_bimestre_pendente():
        for numero in [1, 2, 3, 4]:
            if not bimestre_completo(numero):
                return numero

        return 4

    if request.method == "POST":

        bimestre = int(request.POST.get("bimestre", 1))

        for aluno in alunos:

            nota1 = decimal_ou_none(request.POST.get(f"nota1_{aluno.id}"))
            nota2 = decimal_ou_none(request.POST.get(f"nota2_{aluno.id}"))
            nota3 = decimal_ou_none(request.POST.get(f"nota3_{aluno.id}"))

            if nota1 is None and nota2 is None and nota3 is None:
                continue

            Nota.objects.update_or_create(
                aluno=aluno,
                turma=turma,
                disciplina=disciplina,
                bimestre=bimestre,
                defaults={
                    "nota1": nota1,
                    "nota2": nota2,
                    "nota3": nota3,
                }
            )

        messages.success(request, "Notas salvas com sucesso.")
        return redirect(f"{request.path}?bimestre={bimestre}")

    bimestre_get = request.GET.get("bimestre")

    if bimestre_get in ["1", "2", "3", "4"]:
        bimestre_atual = int(bimestre_get)
    else:
        bimestre_atual = proximo_bimestre_pendente()

    notas_do_bimestre = {
        nota.aluno_id: nota
        for nota in Nota.objects.filter(
            turma=turma,
            disciplina=disciplina,
            bimestre=bimestre_atual
        )
    }

    progresso_bimestres = []

    for numero in [1, 2, 3, 4]:
        total_completos = Nota.objects.filter(
            turma=turma,
            disciplina=disciplina,
            bimestre=numero,
            nota1__isnull=False,
            nota2__isnull=False,
            nota3__isnull=False,
        ).count()

        completo = alunos.exists() and total_completos == alunos.count()

        progresso_bimestres.append({
            "numero": numero,
            "label": f"{numero}º Bimestre",
            "total": alunos.count(),
            "preenchidos": total_completos,
            "completo": completo,
            "ativo": numero == bimestre_atual,
        })

    alunos_notas = []
    soma_medias = Decimal("0")
    alunos_com_media = 0
    alunos_completos = 0

    for aluno in alunos:
        nota = notas_do_bimestre.get(aluno.id)

        media = ""
        completo = False
        status = "Pendente"
        status_classe = "status-pendente"

        if nota:
            media_calculada = nota.calcular_media()

            if media_calculada is not None:
                media = media_calculada
                completo = True
                alunos_completos += 1
                soma_medias += media_calculada
                alunos_com_media += 1

                if media_calculada >= 7:
                    status = "Aprovado"
                    status_classe = "status-aprovado"
                elif media_calculada >= 5:
                    status = "Atenção"
                    status_classe = "status-atencao"
                else:
                    status = "Risco"
                    status_classe = "status-risco"

        alunos_notas.append({
            "obj": aluno,
            "id": aluno.id,
            "nome": aluno.nome,
            "nota1": nota.nota1 if nota else "",
            "nota2": nota.nota2 if nota else "",
            "nota3": nota.nota3 if nota else "",
            "media": media,
            "completo": completo,
            "status": status,
            "status_classe": status_classe,
        })

    media_geral = 0

    if alunos_com_media > 0:
        media_geral = round(soma_medias / alunos_com_media, 2)

    context = {
        "turma": turma,
        "alunos": alunos_notas,
        "disciplina": disciplina,
        "bimestre_atual": bimestre_atual,
        "progresso_bimestres": progresso_bimestres,
        "alunos_completos": alunos_completos,
        "total_alunos": alunos.count(),
        "media_geral": media_geral,
        "todos_bimestres_completos": all(
            item["completo"] for item in progresso_bimestres
        ) if alunos.exists() else False,
    }

    return render(
        request,
        "core/notas_turma.html",
        context
    )


@login_required
def dashboard_professor_home(request):
    """Alias oficial do painel do professor, preservando rota /professor/."""
    return dashboard_professor(request)


@login_required
def professor_alertas_inteligentes(request):
    """Painel do professor com alertas pedagógicos, sem misturar gestão."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina")
    turmas_ids = list(vinculos.values_list("turma_id", flat=True).distinct())
    alunos = Aluno.objects.filter(turma_id__in=turmas_ids, ativo=True).select_related("turma")

    alertas = []
    for aluno in alunos[:120]:
        indicadores = _indicadores_aluno(aluno)
        if indicadores["situacao"] != "Aprovado":
            alertas.append({"aluno": aluno, **indicadores})

    return render(request, "core/professor_alertas_inteligentes.html", {
        "hoje": date.today(),
        "vinculos": vinculos,
        "alertas": alertas,
        "total_alertas": len(alertas),
        "total_turmas": len(turmas_ids),
    })


@login_required
def professor_plano_intervencao(request):
    """Plano de intervenção para o professor, sem misturar recursos administrativos."""
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina")
    turmas_ids = list(vinculos.values_list("turma_id", flat=True).distinct())
    alunos = Aluno.objects.filter(turma_id__in=turmas_ids, ativo=True).select_related("turma")
    planos = []
    for aluno in alunos:
        diag = _diagnostico_recuperacao(aluno)
        if diag["media"] < 6 or diag["faltas"] >= 10 or diag["disciplinas"]:
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
def professor_modo_release_final(request):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    turmas = Turma.objects.filter(professor=request.user, ativa=True).prefetch_related("alunos")
    cards = []
    for turma in turmas:
        cards.append({
            "turma": turma,
            "alunos": turma.alunos.filter(ativo=True).count(),
            "frequencias": Frequencia.objects.filter(turma=turma).count(),
            "notas": Nota.objects.filter(turma=turma).count(),
            "conteudos": ConteudoAula.objects.filter(turma=turma, professor=request.user).count(),
            "acao": "Conferir frequência, notas T1/T2/T3 e registro de aula antes do fechamento.",
        })
    return render(request, "core/professor_release_final.html", {
        "titulo":"Modo release final do professor", "subtitulo":"Painel compacto para validar tudo que o professor precisa antes da escola entrar em uso real.", "etapa":"103", "hoje":date.today(), "cards":cards,
        "tarefas":["Conferir turmas", "Lançar frequência", "Registrar conteúdos", "Validar notas", "Gerar boletins"],
    })


@login_required
def professor_checklist_lancamento(request):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    return render(request, "core/professor_release_final.html", {
        "titulo":"Checklist de lançamento do professor", "subtitulo":"Roteiro simples para validar o uso real do diário em sala.", "etapa":"104", "hoje":date.today(),
        "cards":[],
        "tarefas":["Entrar no painel professor", "Abrir turmas", "Testar frequência mensal", "Testar notas", "Testar registro de aulas", "Gerar boletim/diário"],
    })


@login_required
def professor_assistente_producao(request):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")
    sugestoes = [
        "Comece pela frequência do mês atual.",
        "Registre conteúdos por disciplina com carga horária.",
        "Complete T1/T2/T3 antes do fechamento.",
        "Use pareceres para alunos em atenção.",
        "Revise boletim antes de imprimir ou enviar.",
    ]
    return render(request, "core/professor_release_final.html", {
        "titulo":"Assistente de produção do professor", "subtitulo":"Orientações rápidas para usar o Diário IA em operação real sem travar o fluxo da aula.", "etapa":"105", "hoje":date.today(),
        "cards":[], "tarefas":sugestoes,
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
def professor_minha_matriz_mensal(request):
    """Resumo do professor: cada turma, cada disciplina, frequência e aula do mês selecionado."""
    if not usuario_professor(request.user):
        if usuario_gestor(request.user):
            return redirect("gestao_diario_oficial")
        return render(request, "core/acesso_negado.html")
    turma_id = request.GET.get("turma")
    turmas = _turmas_visiveis_para_usuario(request.user)
    turma_base = turmas.filter(id=turma_id).first() if turma_id else turmas.first()
    ano, mes, mes_param, primeiro, ultimo, meses = _periodo_mes_por_parametro(request, turma_base)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related("turma", "disciplina")
    if turma_id:
        vinculos = vinculos.filter(turma_id=turma_id)
    linhas = []
    for vinculo in vinculos:
        freq = Frequencia.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, data__gte=primeiro, data__lte=ultimo)
        aulas = ConteudoAula.objects.filter(turma=vinculo.turma, disciplina=vinculo.disciplina, professor=request.user, data__gte=primeiro, data__lte=ultimo)
        linhas.append({
            "vinculo": vinculo,
            "frequencias": freq.count(),
            "faltas": freq.filter(presente=False).count(),
            "fj": freq.filter(observacao__icontains="Falta justificada").count(),
            "aulas": aulas.count(),
            "alunos": vinculo.turma.alunos.filter(ativo=True).count(),
        })
    return render(request, "core/professor_matriz_mensal.html", {
        "turmas": turmas,
        "linhas": linhas,
        "mes_param": mes_param,
        "meses": meses,
        "professor": request.user,
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


@login_required
def professor_checklist_turma_disciplina_157(request):
    """Checklist mensal por vínculo oficial do professor: alunos, horários, frequência e aulas."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=request.user, ativo=True).select_related('turma', 'disciplina', 'ano_letivo').order_by('turma__turno', 'turma__nome', 'disciplina__nome')
    linhas = []
    for vinculo in vinculos:
        bloco = _resumo_turma_disciplina_mes(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user)
        linhas.append({'vinculo': vinculo, 'turno': _turma_turno_normalizado(vinculo.turma), 'bloco': bloco})
    return render(request, 'core/professor_checklist_turma_disciplina_157.html', {
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_prontidao_lancamentos_163(request):
    """Prontidão mensal do professor: mostra onde lançar frequência e registro de aulas por vínculo."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas = _painel_prontidao_lancamento_professor(request.user, inicio, fim)
    return render(request, 'core/professor_prontidao_lancamentos_163.html', {
        'linhas': linhas, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_espelho_mensal_disciplina_169(request, turma_id, disciplina_id):
    """Espelho mensal do professor para uma turma/disciplina vinculada pela gestão."""
    if not usuario_professor(request.user):
        return render(request, 'core/acesso_negado.html')
    vinculo = get_object_or_404(ProfessorTurmaDisciplina.objects.select_related('turma', 'disciplina', 'ano_letivo'), professor=request.user, turma_id=turma_id, disciplina_id=disciplina_id, ativo=True)
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    espelho = _espelho_mensal_turma_disciplina(vinculo.turma, vinculo.disciplina, inicio, fim, professor=request.user)
    return render(request, 'core/professor_espelho_mensal_disciplina_169.html', {
        'escola': escola, 'ano_letivo': ano_letivo, 'vinculo': vinculo, 'espelho': espelho,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def professor_operacao_real_301(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    professor = request.user
    carga = carga_horaria_professor_semana(professor)
    aulas_hoje = aulas_professor_hoje(professor)
    turmas = turmas_do_professor(professor).prefetch_related("alunos")
    vinculos = ProfessorTurmaDisciplina.objects.select_related("turma", "disciplina").filter(professor=professor, ativo=True)
    pendencias = []
    if not turmas.exists():
        pendencias.append("A gestão ainda não vinculou turmas para este professor.")
    if not vinculos.exists():
        pendencias.append("A gestão ainda não vinculou disciplinas oficiais.")
    if carga["aulas"] == 0:
        pendencias.append("A grade semanal/carga horária ainda não foi cadastrada pela gestão.")
    return render(request, "core/professor_operacao_real_301.html", {
        "carga": carga,
        "aulas_hoje": aulas_hoje,
        "turmas": turmas,
        "vinculos": vinculos,
        "pendencias": pendencias,
        "hoje": date.today(),
    })


@login_required
def professor_centro_operacional_321(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    professor = request.user
    carga = carga_horaria_professor_semana(professor)
    aulas_hoje_qs = aulas_professor_hoje(professor)
    pendencias = _professor_pendencias_operacionais(professor)
    turmas = turmas_do_professor(professor).prefetch_related("alunos")
    vinculos = ProfessorTurmaDisciplina.objects.select_related("turma", "disciplina").filter(professor=professor, ativo=True)
    return render(request, "core/professor_centro_operacional_321.html", {
        "carga": carga,
        "aulas_hoje": aulas_hoje_qs,
        "pendencias": pendencias,
        "turmas": turmas,
        "vinculos": vinculos,
        "hoje": date.today(),
        "resumo_861_900_professor": resumo_professor_861_900(professor),
    })


@login_required
def professor_rotina_semanal_361(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    professor = request.user
    carga = carga_horaria_professor_semana(professor)
    aulas_hoje = aulas_professor_hoje(professor)
    pendencias = _professor_pendencias_operacionais(professor)
    return render(request, "core/professor_rotina_semanal_361.html", {
        "carga": carga,
        "aulas_hoje": aulas_hoje,
        "pendencias": pendencias,
        "hoje": date.today(),
    })


@login_required
def professor_checkup_funcional_381(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    professor = request.user
    carga = carga_horaria_professor_semana(professor)
    turmas = turmas_do_professor(professor)
    vinculos = ProfessorTurmaDisciplina.objects.select_related("turma", "disciplina").filter(professor=professor, ativo=True)
    alunos = Aluno.objects.filter(turma__in=turmas, ativo=True).distinct()
    aulas = ConteudoAula.objects.filter(professor=professor)
    pendencias = _professor_pendencias_operacionais(professor)
    cards = [
        {"label": "Turmas", "valor": turmas.count(), "detalhe": "vinculadas pela gestão"},
        {"label": "Disciplinas", "valor": vinculos.values("disciplina").distinct().count(), "detalhe": "ativas"},
        {"label": "Carga semanal", "valor": f"{carga['horas']}h", "detalhe": f"{carga['aulas']} aula(s)"},
        {"label": "Alunos", "valor": alunos.count(), "detalhe": "das suas turmas"},
        {"label": "Aulas registradas", "valor": aulas.count(), "detalhe": "conteúdos oficiais"},
        {"label": "Pendências", "valor": len(pendencias), "detalhe": "operacionais"},
    ]
    return render(request, "core/professor_checkup_funcional_381.html", {
        "cards": cards,
        "carga": carga,
        "vinculos": vinculos,
        "pendencias": pendencias,
        "hoje": date.today(),
    })


@login_required
def professor_checkup_etapas_861_900(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    return render(request, "core/professor_checkup_etapas_861_900.html", {
        "resumo": resumo_professor_861_900(request.user),
        "hoje": date.today(),
    })


@login_required
def professor_checkup_etapas_901_960(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = finalizacao_901_960(professor=request.user)
    return render(request, "core/professor_checkup_etapas_901_960.html", contexto)


@login_required
def professor_checkup_etapas_961_1000(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = mega_checkup_961_1000(professor=request.user)
    contexto["hoje"] = date.today()
    return render(request, "core/professor_checkup_etapas_961_1000.html", contexto)


@login_required
def professor_qualidade_final_961(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = roteiro_final_961_1000(professor=request.user)
    contexto["hoje"] = date.today()
    return render(request, "core/professor_qualidade_final_961.html", contexto)


@login_required
def professor_checkup_etapas_1001_1080(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = mega_checkup_1001_1080(professor=request.user)
    contexto["hoje"] = date.today()
    return render(request, "core/professor_checkup_etapas_1001_1080.html", contexto)


@login_required
def professor_finalizacao_total_1001(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = plano_conclusao_1001_1080(professor=request.user)
    contexto["hoje"] = date.today()
    return render(request, "core/professor_finalizacao_total_1001.html", contexto)


@login_required
def professor_checkup_etapas_1081_1160(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = mega_checkup_1081_1160(professor=request.user)
    contexto["hoje"] = date.today()
    return render(request, "core/professor_checkup_etapas_1081_1160.html", contexto)


@login_required
def professor_render_ready_1081(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    contexto = plano_render_1081_1160(professor=request.user)
    contexto["hoje"] = date.today()
    return render(request, "core/professor_render_ready_1081.html", contexto)

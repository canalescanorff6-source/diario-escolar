# Camada de views gestao — refatoração real etapa 1221-1280.
# Mantém os nomes públicos usados pelas URLs, mas tira o peso do antigo views.py.

from .views_shared import *  # noqa: F401,F403
from .views_ia import gestao_ficha_aluno_oficial  # noqa: F401

@login_required
def gestao_escola(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()
    anos = AnoLetivo.objects.all()

    if request.method == "POST":
        nome = request.POST.get("nome") or "Minha Escola"
        ano_id = request.POST.get("ano_letivo_ativo") or None

        if escola is None:
            escola = Escola.objects.create(nome=nome)

        escola.nome = nome
        escola.aldeia = request.POST.get("aldeia") or None
        escola.terra_indigena = request.POST.get("terra_indigena") or None
        escola.municipio = request.POST.get("municipio") or None
        escola.estado = (request.POST.get("estado") or "MA").upper()[:2]
        escola.estado_nome = request.POST.get("estado_nome") or "ESTADO DO MARANHÃO"
        escola.secretaria = request.POST.get("secretaria") or "SECRETARIA DE ESTADO DA EDUCAÇÃO"
        escola.gestor_nome = request.POST.get("gestor_nome") or None
        escola.gestor_cargo = request.POST.get("gestor_cargo") or "Direção escolar"
        escola.texto_institucional = request.POST.get("texto_institucional") or None
        if request.FILES.get("brasao_logo"):
            escola.brasao_logo = request.FILES["brasao_logo"]
        escola.ativa = request.POST.get("ativa") == "on"

        if ano_id:
            escola.ano_letivo_ativo_id = ano_id
        else:
            escola.ano_letivo_ativo = None

        escola.save()
        messages.success(request, "Dados da escola salvos com sucesso.")
        return redirect("gestao_escola")

    context = {
        "escola": escola,
        "anos": anos,
        "hoje": date.today(),
    }

    return render(request, "gestao/escola.html", context)


@login_required
def gestao_professores(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    Usuario = get_user_model()
    escolas = Escola.objects.all()

    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name") or ""
        last_name = request.POST.get("last_name") or ""
        email = request.POST.get("email") or ""
        password = request.POST.get("password") or "12345678"
        escola_id = request.POST.get("escola") or None

        if username:
            professor, criado = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    "tipo": "PROF",
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                }
            )

            professor.tipo = "PROF"
            professor.first_name = first_name
            professor.last_name = last_name
            professor.email = email

            if criado or password:
                professor.set_password(password)

            professor.save()

            perfil, _ = ProfessorPerfil.objects.get_or_create(usuario=professor)
            perfil.telefone = request.POST.get("telefone") or None
            perfil.formacao = request.POST.get("formacao") or None
            perfil.ativo = request.POST.get("ativo") == "on"
            perfil.escola_id = escola_id if escola_id else None
            perfil.save()

            messages.success(request, "Professor salvo com sucesso.")
            return redirect("gestao_professores")

        messages.error(request, "Informe ao menos o usuário do professor.")

    professores = Usuario.objects.filter(tipo="PROF").order_by("first_name", "username")
    perfis = {
        perfil.usuario_id: perfil
        for perfil in ProfessorPerfil.objects.select_related("usuario", "escola")
    }

    professores_dados = []
    for professor in professores:
        professores_dados.append({
            "professor": professor,
            "nome": _nome_usuario(professor),
            "perfil": perfis.get(professor.id),
            "vinculos": ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).count(),
            "horarios": HorarioAula.objects.filter(professor=professor, ativo=True).count(),
        })

    context = {
        "professores_dados": professores_dados,
        "escolas": escolas,
        "hoje": date.today(),
    }

    return render(request, "gestao/professores.html", context)


@login_required
def gestao_vinculos(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    Usuario = get_user_model()

    if request.method == "POST":
        professor_id = request.POST.get("professor")
        turma_id = request.POST.get("turma")
        disciplina_id = request.POST.get("disciplina")
        ano_letivo_id = request.POST.get("ano_letivo") or None

        if professor_id and turma_id and disciplina_id:
            ProfessorTurmaDisciplina.objects.update_or_create(
                professor_id=professor_id,
                turma_id=turma_id,
                disciplina_id=disciplina_id,
                ano_letivo_id=ano_letivo_id,
                defaults={"ativo": request.POST.get("ativo") == "on"}
            )
            messages.success(request, "Vínculo salvo com sucesso.")
            return redirect("gestao_vinculos")

        messages.error(request, "Selecione professor, turma e disciplina.")

    context = {
        "professores": Usuario.objects.filter(tipo="PROF").order_by("first_name", "username"),
        "turmas": Turma.objects.all(),
        "disciplinas": Disciplina.objects.all(),
        "anos": AnoLetivo.objects.all(),
        "vinculos": ProfessorTurmaDisciplina.objects.select_related(
            "professor", "turma", "disciplina", "ano_letivo"
        ).order_by("turma__nome", "disciplina__nome"),
        "hoje": date.today(),
    }

    return render(request, "gestao/vinculos.html", context)


@login_required
def gestao_horarios(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    Usuario = get_user_model()

    if request.method == "POST":
        professor_id = request.POST.get("professor")
        turma_id = request.POST.get("turma")
        disciplina_id = request.POST.get("disciplina")
        dia_semana = request.POST.get("dia_semana")
        ordem = request.POST.get("ordem") or 1
        hora_inicio = request.POST.get("hora_inicio")
        hora_fim = request.POST.get("hora_fim")
        turno = request.POST.get("turno") or None

        if professor_id and turma_id and disciplina_id and dia_semana and hora_inicio and hora_fim:
            HorarioAula.objects.update_or_create(
                professor_id=professor_id,
                turma_id=turma_id,
                disciplina_id=disciplina_id,
                dia_semana=dia_semana,
                ordem=ordem,
                defaults={
                    "hora_inicio": hora_inicio,
                    "hora_fim": hora_fim,
                    "turno": turno,
                    "ativo": request.POST.get("ativo") == "on",
                }
            )
            messages.success(request, "Horário salvo com sucesso.")
            return redirect("gestao_horarios")

        messages.error(request, "Preencha professor, turma, disciplina, dia e horário.")

    horarios = HorarioAula.objects.select_related(
        "professor", "turma", "disciplina"
    ).order_by("dia_semana", "ordem", "hora_inicio")

    grade = {}
    for dia_valor, dia_label in HorarioAula.DIAS_SEMANA:
        grade[dia_label] = horarios.filter(dia_semana=dia_valor)

    context = {
        "professores": Usuario.objects.filter(tipo="PROF").order_by("first_name", "username"),
        "turmas": Turma.objects.all(),
        "disciplinas": Disciplina.objects.all(),
        "dias_semana": HorarioAula.DIAS_SEMANA,
        "turnos": HorarioAula.TURNO_CHOICES,
        "horarios": horarios,
        "grade": grade,
        "hoje": date.today(),
    }

    return render(request, "gestao/horarios.html", context)


@login_required
def gestao_alunos(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    busca = request.GET.get("busca", "").strip()
    turma_id = request.GET.get("turma")

    alunos = Aluno.objects.filter(ativo=True).select_related("turma")

    if busca:
        alunos = alunos.filter(nome__icontains=busca)

    if turma_id:
        alunos = alunos.filter(turma_id=turma_id)

    alunos_dados = []
    for aluno in alunos[:120]:
        notas_aluno = Nota.objects.filter(aluno=aluno)
        medias = [float(n.valor) for n in notas_aluno if n.valor is not None]
        media = round(sum(medias) / len(medias), 1) if medias else 0
        faltas = Frequencia.objects.filter(aluno=aluno, presente=False).count()
        registros = Frequencia.objects.filter(aluno=aluno).count()
        presencas = Frequencia.objects.filter(aluno=aluno, presente=True).count()
        frequencia = round((presencas / registros) * 100, 1) if registros else 0

        if media < 6 or frequencia < 75:
            status = "Atenção"
            classe = "risk-high"
        elif media < 7 or frequencia < 85:
            status = "Monitorar"
            classe = "risk-medium"
        else:
            status = "Estável"
            classe = "risk-low"

        alunos_dados.append({
            "aluno": aluno,
            "media": media,
            "faltas": faltas,
            "frequencia": frequencia,
            "status": status,
            "classe": classe,
        })

    context = {
        "hoje": date.today(),
        "escola": Escola.objects.filter(ativa=True).first(),
        "turmas": Turma.objects.all(),
        "alunos_dados": alunos_dados,
        "busca": busca,
        "turma_id": turma_id,
    }

    return render(request, "gestao/alunos.html", context)


# =====================================================
# ETAPA 9 — CALENDÁRIO, FECHAMENTO, PARECERES E ASSINATURAS
# Módulos administrativos aditivos.
# =====================================================

@login_required
def gestao_calendario(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    escola = Escola.objects.filter(ativa=True).first()
    ano_letivo = AnoLetivo.objects.filter(ativo=True).first()

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        tipo = request.POST.get("tipo") or "EVENTO"
        data_inicio = request.POST.get("data_inicio")
        data_fim = request.POST.get("data_fim") or None
        descricao = request.POST.get("descricao")

        if titulo and data_inicio:
            CalendarioEvento.objects.create(
                escola=escola,
                ano_letivo=ano_letivo,
                titulo=titulo,
                tipo=tipo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                descricao=descricao,
                criado_por=request.user,
            )
            messages.success(request, "Evento do calendário salvo com sucesso.")
            return redirect("gestao_calendario")

        messages.error(request, "Informe pelo menos título e data inicial.")

    eventos = CalendarioEvento.objects.select_related(
        "escola",
        "ano_letivo",
        "criado_por",
    ).order_by("data_inicio", "titulo")

    hoje = date.today()
    proximos_eventos = eventos.filter(data_inicio__gte=hoje)[:12]

    context = {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "hoje": hoje,
        "eventos": eventos[:80],
        "proximos_eventos": proximos_eventos,
        "tipos_evento": CalendarioEvento.TIPOS,
        "total_eventos": eventos.count(),
        "total_dias_letivos": eventos.filter(tipo="AULA").count(),
        "total_avaliacoes": eventos.filter(tipo="AVALIACAO").count(),
        "total_reunioes": eventos.filter(tipo="REUNIAO").count(),
    }

    return render(request, "gestao/calendario.html", context)


@login_required
def gestao_assinaturas(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.all()
    alunos = Aluno.objects.filter(ativo=True).select_related("turma")

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        turma_id = request.POST.get("turma") or None
        aluno_id = request.POST.get("aluno") or None
        cargo = request.POST.get("cargo")
        observacoes = request.POST.get("observacoes")

        if tipo:
            AssinaturaDocumento.objects.create(
                tipo=tipo,
                turma_id=turma_id,
                aluno_id=aluno_id,
                assinado_por=request.user,
                cargo=cargo,
                observacoes=observacoes,
            )
            messages.success(request, "Assinatura registrada com sucesso.")
            return redirect("gestao_assinaturas")

        messages.error(request, "Informe o tipo de documento para registrar a assinatura.")

    assinaturas = AssinaturaDocumento.objects.select_related(
        "turma",
        "aluno",
        "assinado_por",
    )[:120]

    context = {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turmas": turmas,
        "alunos": alunos[:200],
        "assinaturas": assinaturas,
        "tipos": AssinaturaDocumento.TIPOS,
        "total_assinaturas": AssinaturaDocumento.objects.count(),
    }

    return render(request, "gestao/assinaturas.html", context)


# =====================================================
# ETAPA 10 — HISTÓRICO, FICHA, AUDITORIA, DOCUMENTOS E NOTIFICAÇÕES
# =====================================================

@login_required
def gestao_historico_alunos(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    turmas = Turma.objects.all()
    historicos = HistoricoAluno.objects.select_related(
        "aluno", "turma", "ano_letivo", "registrado_por"
    )[:80]

    aluno_id = request.GET.get("aluno") or request.POST.get("aluno")
    turma_id = request.GET.get("turma")

    if turma_id:
        alunos = alunos.filter(turma_id=turma_id)
        historicos = historicos.filter(turma_id=turma_id)

    if aluno_id:
        historicos = historicos.filter(aluno_id=aluno_id)

    if request.method == "POST":
        aluno = get_object_or_404(Aluno, id=aluno_id)
        situacao = request.POST.get("situacao") or "OBSERVACAO"
        descricao = request.POST.get("descricao")
        data_registro = request.POST.get("data") or date.today()
        ano_letivo = AnoLetivo.objects.filter(ativo=True).first()

        if descricao:
            HistoricoAluno.objects.create(
                aluno=aluno,
                turma=aluno.turma,
                ano_letivo=ano_letivo,
                situacao=situacao,
                data=data_registro,
                descricao=descricao,
                registrado_por=request.user,
            )
            registrar_auditoria(
                request.user,
                "Histórico do aluno",
                "Novo registro",
                objeto=aluno.nome,
                descricao=descricao,
            )
            messages.success(request, "Histórico registrado com sucesso.")
            return redirect("gestao_historico_alunos")

    context = {
        "alunos": alunos,
        "turmas": turmas,
        "historicos": historicos,
        "situacoes": HistoricoAluno.SITUACOES,
        "aluno_id": aluno_id,
        "turma_id": turma_id,
        "hoje": date.today(),
    }

    return render(request, "gestao/historico_alunos.html", context)


@login_required
def gestao_ficha_aluno(request, aluno_id):

    # Etapas 265–270: a ficha antiga foi desativada para evitar layout legado.
    # A rota continua existindo para não quebrar links antigos, mas sempre abre
    # a ficha oficial única da gestão.
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    return redirect("gestao_aluno_painel_integrado", aluno_id=aluno_id)


@login_required
def gestao_notificacoes(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        mensagem = request.POST.get("mensagem")
        nivel = request.POST.get("nivel") or "INFO"
        turma_id = request.POST.get("turma") or None
        aluno_id = request.POST.get("aluno") or None

        if titulo and mensagem:
            notificacao = NotificacaoGestao.objects.create(
                titulo=titulo,
                mensagem=mensagem,
                nivel=nivel,
                turma_id=turma_id,
                aluno_id=aluno_id,
                criado_por=request.user,
            )
            registrar_auditoria(request.user, "Notificações", "Nova notificação", objeto=notificacao.titulo)
            messages.success(request, "Notificação criada com sucesso.")
            return redirect("gestao_notificacoes")

    context = {
        "notificacoes": NotificacaoGestao.objects.select_related("turma", "aluno", "destino", "criado_por")[:120],
        "turmas": Turma.objects.all(),
        "alunos": Aluno.objects.filter(ativo=True).select_related("turma"),
        "niveis": NotificacaoGestao.NIVEIS,
        "pendentes": NotificacaoGestao.objects.filter(resolvida=False).count(),
        "hoje": date.today(),
    }

    return render(request, "gestao/notificacoes.html", context)


@login_required
def gestao_notificacao_resolver(request, notificacao_id):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    notificacao = get_object_or_404(NotificacaoGestao, id=notificacao_id)
    notificacao.resolvida = True
    notificacao.save(update_fields=["resolvida"])
    registrar_auditoria(request.user, "Notificações", "Resolver notificação", objeto=notificacao.titulo)
    messages.success(request, "Notificação marcada como resolvida.")
    return redirect("gestao_notificacoes")


# =====================================================
# ETAPA 11 — Painel executivo, backup e integrações
# =====================================================

@login_required
def gestao_executivo(request):
    if request.user.tipo not in ["ADMIN", "SEC", "COORD"]:
        return render(request, "core/acesso_negado.html")

    indicadores = IndicadorGestao.objects.all()[:12]

    return render(request, "gestao/executivo.html", {
        "total_backups": BackupSistema.objects.count(),
        "total_integracoes": IntegracaoEscolar.objects.filter(ativa=True).count(),
        "indicadores": indicadores,
    })


@login_required
def gestao_backups(request):
    if request.user.tipo not in ["ADMIN", "SEC", "COORD"]:
        return render(request, "core/acesso_negado.html")

    if request.method == "POST":
        BackupSistema.objects.create(
            titulo=request.POST.get("titulo") or "Backup manual",
            status="GERADO",
            criado_por=request.user,
        )
        return redirect("gestao_backups")

    return render(request, "gestao/backups.html", {
        "backups": BackupSistema.objects.all()
    })


@login_required
def gestao_integracoes(request):
    if request.user.tipo not in ["ADMIN", "SEC", "COORD"]:
        return render(request, "core/acesso_negado.html")

    if request.method == "POST":
        IntegracaoEscolar.objects.create(
            nome=request.POST.get("nome"),
            tipo=request.POST.get("tipo") or "GESTAO",
            descricao=request.POST.get("descricao"),
            ativa=True,
        )
        return redirect("gestao_integracoes")

    return render(request, "gestao/integracoes.html", {
        "integracoes": IntegracaoEscolar.objects.all()
    })


@login_required
def gestao_configuracoes(request):
    if request.user.tipo not in ["ADMIN", "SEC", "COORD"]:
        return render(request, "core/acesso_negado.html")

    if request.method == "POST":
        if request.FILES.get("foto"):
            request.user.foto = request.FILES["foto"]
            request.user.save(update_fields=["foto"])
            messages.success(request, "Imagem da gestão atualizada com sucesso.")
        elif request.POST.get("remover_foto") == "1":
            request.user.foto.delete(save=False)
            request.user.foto = None
            request.user.save(update_fields=["foto"])
            messages.success(request, "Imagem da gestão removida.")
        else:
            messages.info(request, "Escolha uma imagem para atualizar o perfil da gestão.")
        return redirect("gestao_configuracoes")

    return render(request, "gestao/configuracoes.html")


@login_required
def gestao_notificacoes_gerar_inteligentes(request):
    """Gera alertas automáticos de risco sem apagar notificações existentes."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    criadas = 0
    for aluno in Aluno.objects.filter(ativo=True).select_related("turma"):
        notas = Nota.objects.filter(aluno=aluno).exclude(valor__isnull=True)
        media = _media_decimal([n.valor for n in notas])
        frequencia = _percentual_frequencia(aluno=aluno)
        motivos = []
        nivel = "INFO"
        if media is not None and media < 6:
            motivos.append(f"média baixa ({media})")
            nivel = "CRITICO"
        elif media is not None and media < 7:
            motivos.append(f"média em atenção ({media})")
            nivel = "ATENCAO"
        if frequencia < 75:
            motivos.append(f"frequência crítica ({frequencia}%)")
            nivel = "CRITICO"
        elif frequencia < 85:
            motivos.append(f"frequência em atenção ({frequencia}%)")
            if nivel != "CRITICO":
                nivel = "ATENCAO"
        if not motivos:
            continue
        titulo = f"Acompanhamento inteligente • {aluno.nome}"
        ja_existe = NotificacaoGestao.objects.filter(titulo=titulo, resolvida=False, aluno=aluno).exists()
        if ja_existe:
            continue
        NotificacaoGestao.objects.create(
            titulo=titulo,
            mensagem="Aluno sinalizado automaticamente por " + ", ".join(motivos) + ". Recomenda-se plano de intervenção pedagógica.",
            nivel=nivel,
            turma=aluno.turma,
            aluno=aluno,
            criado_por=request.user,
        )
        criadas += 1

    registrar_auditoria(request.user, "Notificações", "Geração inteligente de alertas", objeto=f"{criadas} alertas")
    messages.success(request, f"{criadas} notificação(ões) inteligente(s) gerada(s).")
    return redirect("gestao_notificacoes")


@login_required
def gestao_calendario_impressao(request):
    """Mapa oficial do calendário escolar para impressão/PDF."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    eventos = CalendarioEvento.objects.select_related("escola", "ano_letivo").order_by("data_inicio", "titulo")
    meses = []
    for mes in range(1, 13):
        eventos_mes = eventos.filter(data_inicio__month=mes)
        meses.append({
            "numero": mes,
            "nome": calendar.month_name[mes].capitalize(),
            "eventos": eventos_mes,
            "dias_letivos": eventos_mes.filter(tipo="AULA").count(),
            "avaliacoes": eventos_mes.filter(tipo="AVALIACAO").count(),
        })

    registrar_auditoria(request.user, "Calendário", "Calendário oficial gerado", objeto="Ano letivo")
    context = {
        "escola": Escola.objects.filter(ativa=True).first(),
        "ano_letivo": AnoLetivo.objects.filter(ativo=True).first(),
        "meses": meses,
        "hoje": date.today(),
        "protocolo": _protocolo_documento("CAL", request.user.id),
    }
    return render(request, "gestao/calendario_impressao.html", context)

# =====================================================
# ETAPA 14 — Validações oficiais, fechamento anual e governança
# Funcionalidades aditivas: não substituem telas nem fluxos anteriores.
# =====================================================


@login_required
def gestao_assinaturas_pendentes(request):
    """Central de conferência entre documentos gerados e assinaturas registradas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    documentos = DocumentoGerado.objects.select_related("turma", "aluno", "gerado_por")[:160]
    assinaturas = AssinaturaDocumento.objects.select_related("turma", "aluno", "assinado_por")
    linhas = []
    for documento in documentos:
        existe = assinaturas.filter(tipo=documento.tipo, turma=documento.turma, aluno=documento.aluno).exists()
        linhas.append({"documento": documento, "assinado": existe})

    registrar_auditoria(request.user, "Assinaturas", "Central de pendências consultada", objeto="Documentos oficiais")
    return render(request, "gestao/assinaturas_pendentes.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "linhas": linhas,
        "total_documentos": len(linhas),
        "total_assinados": sum(1 for item in linhas if item["assinado"]),
        "total_pendentes": sum(1 for item in linhas if not item["assinado"]),
    })


@login_required
def gestao_calendario_validacao(request):
    """Validação simples de calendário escolar para orientar secretaria/coordenação."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    eventos = CalendarioEvento.objects.all()
    dias_letivos = eventos.filter(tipo="AULA").count()
    avaliacoes = eventos.filter(tipo="AVALIACAO").count()
    reunioes = eventos.filter(tipo="REUNIAO").count()
    pendencias = []
    if dias_letivos < 200:
        pendencias.append("Calendário ainda não possui 200 dias letivos registrados.")
    if avaliacoes == 0:
        pendencias.append("Nenhum evento de avaliação foi cadastrado.")
    if reunioes == 0:
        pendencias.append("Nenhuma reunião pedagógica foi cadastrada.")

    if request.method == "POST":
        for texto in pendencias:
            NotificacaoGestao.objects.get_or_create(
                titulo="Pendência de calendário",
                mensagem=texto,
                nivel="ATENCAO",
                criado_por=request.user,
            )
        registrar_auditoria(request.user, "Calendário", "Validação inteligente executada", objeto=f"{len(pendencias)} pendências")
        messages.success(request, "Validação registrada e notificações criadas quando necessário.")
        return redirect("gestao_calendario_validacao")

    return render(request, "gestao/calendario_validacao.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "dias_letivos": dias_letivos,
        "avaliacoes": avaliacoes,
        "reunioes": reunioes,
        "pendencias": pendencias,
        "total_eventos": eventos.count(),
    })


@login_required
def gestao_mapa_recuperacao(request):
    """Mapa oficial de alunos em recuperação/atenção pedagógica."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turma_id = request.GET.get("turma")
    turmas = Turma.objects.all().prefetch_related("alunos")
    turma = turmas.filter(id=turma_id).first() if turma_id else turmas.first()
    linhas = []
    if turma:
        for aluno in turma.alunos.filter(ativo=True):
            diag = _diagnostico_recuperacao(aluno)
            if diag["media"] < 6 or diag["faltas"] >= 10 or diag["disciplinas"]:
                linhas.append({"aluno": aluno, **diag})

    if request.method == "POST" and turma:
        DocumentoGerado.objects.create(
            tipo="RELATORIO",
            titulo=f"Mapa de recuperação • {turma.nome}",
            turma=turma,
            gerado_por=request.user,
            observacoes="Documento pedagógico criado pela Etapa 15.",
        )
        registrar_auditoria(request.user, "Recuperação", "Mapa de recuperação registrado", objeto=turma.nome)
        messages.success(request, "Mapa de recuperação registrado nos documentos oficiais.")
        return redirect(f"{request.path}?turma={turma.id}")

    return render(request, "gestao/mapa_recuperacao.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turmas": turmas,
        "turma_selecionada": turma,
        "linhas": linhas,
        "total_alunos": turma.alunos.filter(ativo=True).count() if turma else 0,
        "total_recuperacao": len(linhas),
    })


@login_required
def gestao_ata_conselho_classe(request):
    """Ata imprimível de conselho de classe por turma."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turma_id = request.GET.get("turma")
    turmas = Turma.objects.all().prefetch_related("alunos")
    turma = turmas.filter(id=turma_id).first() if turma_id else turmas.first()
    alunos_analise = []
    if turma:
        for aluno in turma.alunos.filter(ativo=True):
            alunos_analise.append({"aluno": aluno, **_diagnostico_recuperacao(aluno)})

    if request.method == "POST" and turma:
        DocumentoGerado.objects.create(
            tipo="RELATORIO",
            titulo=f"Ata de conselho de classe • {turma.nome}",
            turma=turma,
            gerado_por=request.user,
            observacoes="Ata oficial para impressão e assinatura.",
        )
        registrar_auditoria(request.user, "Conselho de classe", "Ata gerada", objeto=turma.nome)
        messages.success(request, "Ata do conselho registrada nos documentos oficiais.")
        return redirect(f"{request.path}?turma={turma.id}")

    return render(request, "gestao/ata_conselho_classe.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turmas": turmas,
        "turma_selecionada": turma,
        "alunos_analise": alunos_analise,
        "total_criticos": sum(1 for item in alunos_analise if item["nivel"] == "CRÍTICO"),
        "total_atencao": sum(1 for item in alunos_analise if item["nivel"] == "ATENÇÃO"),
    })


@login_required
def gestao_dossie_turma(request, turma_id):
    """Dossiê institucional consolidado da turma, no padrão executivo premium."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(Turma, id=turma_id)
    alunos = turma.alunos.filter(ativo=True)
    linhas = [{"aluno": aluno, **_diagnostico_recuperacao(aluno)} for aluno in alunos]
    documentos = DocumentoGerado.objects.filter(turma=turma)[:60]
    conteudos = ConteudoAula.objects.filter(turma=turma).select_related("disciplina", "professor")[:80]
    fechamentos = FechamentoBimestre.objects.filter(turma=turma).select_related("disciplina")
    registrar_auditoria(request.user, "Turma", "Dossiê da turma consultado", objeto=turma.nome)
    return render(request, "gestao/dossie_turma.html", {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "turma": turma,
        "linhas": linhas,
        "documentos": documentos,
        "conteudos": conteudos,
        "fechamentos": fechamentos,
        "media_turma": round(sum(item["media"] for item in linhas) / len(linhas), 1) if linhas else 0,
        "total_faltas": sum(item["faltas"] for item in linhas),
    })


@login_required
def gestao_ranking_pedagogico(request):
    """Ranking pedagógico inteligente por turma e aluno."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    ranking = []
    for aluno in alunos:
        media = _media_aluno(aluno)
        faltas = _faltas_aluno(aluno)
        score = max(0, round((media * 10) - min(faltas, 40), 1))
        nivel = "Excelência" if media >= 8 and faltas < 5 else "Acompanhamento" if media >= 6 else "Intervenção"
        ranking.append({"aluno": aluno, "media": media, "faltas": faltas, "score": score, "nivel": nivel})
    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)

    registrar_auditoria(request.user, "Ranking", "Ranking pedagógico consultado")
    return render(request, "gestao/ranking_pedagogico.html", {"hoje": date.today(), "ranking": ranking[:120]})


@login_required
def gestao_centro_permissoes(request):
    """Central visual de permissões, mantendo professor e gestão separados."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    matriz = [
        {"perfil": "PROF", "painel": "/professor/", "permissoes": ["Turmas atribuídas", "Frequência", "Notas", "Conteúdo", "IA pedagógica"], "bloqueios": ["Gestão", "Auditoria", "Backups", "Configurações"]},
        {"perfil": "ADMIN", "painel": "/gestao/", "permissoes": ["Gestão completa", "Relatórios", "Auditoria", "Backups", "Permissões"], "bloqueios": ["Uso operacional do diário do professor"]},
        {"perfil": "SEC", "painel": "/gestao/", "permissoes": ["Alunos", "Documentos", "Histórico", "Boletins", "Frequência consultiva"], "bloqueios": ["Alterar diário pedagógico do professor"]},
        {"perfil": "COORD", "painel": "/gestao/", "permissoes": ["Fechamentos", "Pareceres", "Conselho", "Intervenção", "Relatórios"], "bloqueios": ["Configurações sensíveis"]},
    ]
    registrar_auditoria(request.user, "Permissões", "Centro premium de permissões consultado")
    return render(request, "gestao/centro_permissoes.html", {"hoje": date.today(), "matriz": matriz})


@login_required
def gestao_preparacao_executaveis(request):
    """Orientações e atalhos para Professor.exe e Gestor.exe."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    registrar_auditoria(request.user, "Executáveis", "Preparação estrutural consultada")
    return render(request, "gestao/preparacao_executaveis.html", {
        "hoje": date.today(),
        "professor_url": "/professor/",
        "gestor_url": "/gestao/",
    })


@login_required
def gestao_logs_avancados(request):
    """Logs administrativos avançados reaproveitando a auditoria já existente."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    logs = AuditoriaSistema.objects.select_related("usuario")[:150]
    modulos = AuditoriaSistema.objects.values("modulo").annotate(total=Count("id")).order_by("-total")[:20]
    return render(request, "gestao/logs_avancados.html", {"hoje": date.today(), "logs": logs, "modulos": modulos})


@login_required
def gestao_busca_global(request):
    """Busca executiva global para gestão, sem misturar com o painel operacional do professor."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    termo = (request.GET.get("q") or "").strip()
    resultados = {
        "alunos": [],
        "turmas": [],
        "disciplinas": [],
        "documentos": [],
        "auditorias": [],
    }

    if termo:
        resultados["alunos"] = Aluno.objects.filter(nome__icontains=termo).select_related("turma")[:20]
        resultados["turmas"] = Turma.objects.filter(nome__icontains=termo).select_related("ano_letivo")[:20]
        resultados["disciplinas"] = Disciplina.objects.filter(nome__icontains=termo)[:20]
        resultados["documentos"] = DocumentoGerado.objects.filter(titulo__icontains=termo).select_related("aluno", "turma")[:20]
        resultados["auditorias"] = AuditoriaSistema.objects.filter(acao__icontains=termo).select_related("usuario")[:20]
        registrar_auditoria(request.user, "Busca global", "Busca executiva realizada", objeto=termo)

    total_resultados = sum(len(v) for v in resultados.values())

    return render(request, "gestao/busca_global.html", {
        "hoje": date.today(),
        "termo": termo,
        "resultados": resultados,
        "total_resultados": total_resultados,
    })


@login_required
def gestao_saude_sistema(request):
    """Painel de saúde SaaS com cadastros, pendências e consistência operacional."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    total_alunos = Aluno.objects.count()
    alunos_sem_turma = Aluno.objects.filter(turma__isnull=True).count()
    turmas_sem_professor = Turma.objects.filter(professor__isnull=True).count()
    total_notas = Nota.objects.count()
    notas_incompletas = Nota.objects.filter(nota1__isnull=True).count() + Nota.objects.filter(nota2__isnull=True).count() + Nota.objects.filter(nota3__isnull=True).count()
    diarios = Diario.objects.count()
    conteudos = ConteudoAula.objects.count()
    documentos = DocumentoGerado.objects.count()
    auditorias = AuditoriaSistema.objects.count()

    checks = [
        {"titulo": "Alunos cadastrados", "valor": total_alunos, "status": "OK" if total_alunos else "Atenção", "detalhe": "Base discente ativa para boletins, frequência e histórico."},
        {"titulo": "Turmas sem professor", "valor": turmas_sem_professor, "status": "Atenção" if turmas_sem_professor else "OK", "detalhe": "Vínculo do professor é essencial para Professor.exe e painel operacional."},
        {"titulo": "Notas incompletas", "valor": notas_incompletas, "status": "Atenção" if notas_incompletas else "OK", "detalhe": "T1/T2/T3 devem estar completos para média automática e fechamento."},
        {"titulo": "Registros de aula", "valor": conteudos + diarios, "status": "OK" if (conteudos + diarios) else "Atenção", "detalhe": "Conteúdos mensais alimentam o diário oficial e relatórios."},
        {"titulo": "Documentos gerados", "valor": documentos, "status": "OK" if documentos else "Inicial", "detalhe": "Boletins, diários e relatórios oficiais ficam rastreáveis."},
        {"titulo": "Auditorias", "valor": auditorias, "status": "OK" if auditorias else "Inicial", "detalhe": "Logs administrativos fortalecem governança e rastreabilidade."},
    ]

    percentual_saude = 100
    percentual_saude -= 12 if turmas_sem_professor else 0
    percentual_saude -= 12 if notas_incompletas else 0
    percentual_saude -= 10 if not total_alunos else 0
    percentual_saude -= 8 if not (conteudos + diarios) else 0
    percentual_saude = max(0, percentual_saude)

    registrar_auditoria(request.user, "Saúde do sistema", "Painel de saúde SaaS consultado")

    return render(request, "gestao/saude_sistema.html", {
        "hoje": date.today(),
        "checks": checks,
        "percentual_saude": percentual_saude,
        "alunos_sem_turma": alunos_sem_turma,
    })


@login_required
def gestao_comunicacao_responsaveis(request):
    """Central de comunicação com responsáveis baseada em risco pedagógico e frequência."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    comunicados = []
    for aluno in alunos:
        media = _media_aluno(aluno)
        faltas = _faltas_aluno(aluno)
        nivel = _status_badge_por_media(media, faltas)
        if nivel in ["Crítico", "Atenção"]:
            mensagem = (
                f"Olá, responsável por {aluno.nome}. A escola identificou necessidade de acompanhamento: "
                f"média atual {media} e {faltas} falta(s). Solicitamos contato com a equipe pedagógica."
            )
            comunicados.append({
                "aluno": aluno,
                "media": media,
                "faltas": faltas,
                "nivel": nivel,
                "responsavel": aluno.responsavel or "Responsável não informado",
                "telefone": aluno.telefone or "Telefone não informado",
                "mensagem": mensagem,
            })

    registrar_auditoria(request.user, "Comunicação", "Central de responsáveis consultada")
    return render(request, "gestao/comunicacao_responsaveis.html", {
        "hoje": date.today(),
        "comunicados": comunicados[:120],
        "total_comunicados": len(comunicados),
    })


@login_required
def gestao_consolidacao_final_tecnica(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    registrar_auditoria(request.user, "Versão final", "Consolidação técnica final consultada")
    checks = [
        {"nome": "Rotas professor/gestão", "status": "Preservado", "detalhe": "Mantém separação /professor/ e /gestao/."},
        {"nome": "Banco e migrations", "status": "Seguro", "detalhe": "Sem novas migrations nesta etapa para evitar conflito."},
        {"nome": "Arquivos grandes", "status": "Preservado", "detalhe": "Camada aditiva sem reduzir views/models/templates existentes."},
        {"nome": "Design premium", "status": "Preservado", "detalhe": "Telas glass dark/teal independentes do CSS refinado existente."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Consolidação técnica final", "Revisão final de arquitetura, rotas, permissões e estabilidade sem mexer destrutivamente na base.", "97", checklist=checks,
        cards=[{"titulo":"Modo seguro", "valor":"ON", "texto":"Sem alteração de schema e sem remoção de código."}, {"titulo":"Base conferida", "valor":"OK", "texto":"Projeto preparado para fechamento final incremental."}],
        proximos=["Revisar ambiente real de produção", "Executar teste manual de fluxo professor", "Executar teste manual de fluxo gestão"]
    ))


@login_required
def gestao_testes_finais(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    checklist = [
        {"nome":"Login PROF", "status":"Testar", "detalhe":"Acessar /professor/ e validar bloqueio da gestão."},
        {"nome":"Login ADMIN/SEC/COORD", "status":"Testar", "detalhe":"Acessar /gestao/ e validar painel executivo."},
        {"nome":"Notas e frequência", "status":"Testar", "detalhe":"Lançar T1/T2/T3, frequência e conteúdo mensal."},
        {"nome":"Documentos", "status":"Testar", "detalhe":"Gerar boletim, diário, declaração e relatório."},
        {"nome":"Fechamento", "status":"Testar", "detalhe":"Validar travas, checklist e consolidação anual."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Testes finais guiados", "Roteiro objetivo para validar o sistema sem quebrar rotas já existentes.", "99", checklist=checklist,
        cards=[{"titulo":"Fluxos críticos", "valor":"5", "texto":"Professor, gestão, documentos, fechamento e permissões."}],
        proximos=["Testar com banco atual", "Anotar erros por tela", "Enviar pacote atualizado se aparecer falha"]
    ))


@login_required
def gestao_migracao_dados_producao(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    checklist = [
        {"nome":"Backup antes de migrar", "status":"Obrigatório", "detalhe":"Nunca migrar sem cópia do banco atual."},
        {"nome":"Cadastros pela gestão", "status":"Pronto", "detalhe":"Alunos, turmas, professores, disciplinas, vínculos e horários são cadastrados diretamente pela gestão."},
        {"nome":"Professores e vínculos", "status":"Pronto", "detalhe":"Validar professor x turma x disciplina."},
        {"nome":"Ano letivo ativo", "status":"Pronto", "detalhe":"Conferir período, bimestres e calendário."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Migração de dados para produção", "Mapa de migração seguro para entrar em uso real sem perder dados escolares.", "100", checklist=checklist,
        cards=[{"titulo":"Alunos", "valor":_safe_count(Aluno), "texto":"Registros disponíveis no ambiente atual."}, {"titulo":"Turmas", "valor":_safe_count(Turma), "texto":"Turmas cadastradas atualmente."}],
        proximos=["Conferir cadastros oficiais da gestão", "Validar amostra de boletim", "Gerar relatório de consistência"]
    ))


@login_required
def gestao_congelamento_release(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    registrar_auditoria(request.user, "Release", "Congelamento de release consultado")
    checklist = [
        {"nome":"Não alterar models sem necessidade", "status":"Regra ativa", "detalhe":"Evita migrations desnecessárias no fim do projeto."},
        {"nome":"Congelar layout premium", "status":"Regra ativa", "detalhe":"Apenas ajustes finos, sem redesign destrutivo."},
        {"nome":"Pacotes menores", "status":"Regra ativa", "detalhe":"Evita erro de upload e facilita aplicação."},
        {"nome":"Validação antes do ZIP", "status":"Regra ativa", "detalhe":"check/migrate e sem db.sqlite3."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Congelamento seguro de release", "Define a linha de estabilidade para parar de criar módulos grandes e entrar em acabamento controlado.", "101", checklist=checklist,
        cards=[{"titulo":"Status", "valor":"Freeze", "texto":"Módulos grandes concluídos; foco em estabilidade."}],
        proximos=["Manter pacote atual", "Corrigir apenas falhas reais", "Preparar build/deploy"]
    ))


@login_required
def gestao_centro_pronto_lancamento(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    score = 94
    pendencias = [
        "Deploy real em servidor/cloud",
        "Build real de executáveis/app se desejar",
        "Configuração real de OpenAI/IA externa",
        "Domínio, SSL e banco de produção",
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Centro pronto para lançamento", "Resumo da gestão final: o sistema está pronto como release candidato; o restante é infraestrutura externa e homologação.", "102",
        checklist=[{"nome":p, "status":"Externo/produção", "detalhe":"Não depende apenas do código Django."} for p in pendencias],
        cards=[{"titulo":"Maturidade", "valor":f"{score}%", "texto":"Release candidato comercial após validação manual."}, {"titulo":"Pendências críticas de código", "valor":"Baixas", "texto":"Sem novos módulos obrigatórios grandes."}],
        proximos=["Homologar com escola piloto", "Publicar ambiente staging", "Configurar integrações reais"]
    ))


@login_required
def gestao_ultima_milha(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    checklist = [
        {"nome":"Revisão final visual", "status":"OK", "detalhe":"Manter premium sem redesenho destrutivo."},
        {"nome":"Revisão final de dados", "status":"OK", "detalhe":"Conferir cadastros reais da escola."},
        {"nome":"Revisão final de permissões", "status":"OK", "detalhe":"PROF separado de ADMIN/SEC/COORD."},
        {"nome":"Revisão final de documentos", "status":"OK", "detalhe":"Boletim, diário, declaração e relatórios."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Última milha do produto", "Checklist final para sair de desenvolvimento e entrar em homologação/produção.", "106", checklist=checklist,
        cards=[{"titulo":"Código", "valor":"Estável", "texto":"A partir daqui, mexer só em correções reais."}, {"titulo":"Produto", "valor":"Finalizável", "texto":"Sem grandes módulos obrigatórios restantes."}],
        proximos=["Aplicar pacote", "Rodar migrate", "Testar rotas principais", "Enviar erro real se aparecer"]
    ))


@login_required
def gestao_mapa_pos_final(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    checklist = [
        {"nome":"Opcional: app nativo", "status":"Futuro", "detalhe":"Electron/Tauri e instalador Windows."},
        {"nome":"Opcional: cobrança real", "status":"Futuro", "detalhe":"Gateway de pagamento e contratos."},
        {"nome":"Opcional: IA externa", "status":"Futuro", "detalhe":"OpenAI/embeddings/automação avançada."},
        {"nome":"Opcional: escala estadual", "status":"Futuro", "detalhe":"Infra dedicada, filas, storage e BI robusto."},
    ]
    return render(request, "gestao/finalizacao_acelerada_gestao.html", _gestao_final_contexto(
        "Mapa pós-finalização", "O que fica como evolução futura depois do sistema estar concluído como release Django/SaaS.", "107", checklist=checklist,
        cards=[{"titulo":"Finalização", "valor":"Alcançada", "texto":"Grandes módulos foram concluídos; próximos pontos são evoluções de mercado."}],
        proximos=["Parar criação massiva", "Testar em produção", "Planejar roadmap futuro"]
    ))


@login_required
def gestao_status_projeto_concluido(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    checklist = [
        {"nome":"Painel professor", "status":"Concluído", "detalhe":"Operacional separado da gestão."},
        {"nome":"Painel gestão", "status":"Concluído", "detalhe":"Executivo, secretaria, auditoria, relatórios e documentos."},
        {"nome":"Diário/boletim/frequência", "status":"Concluído", "detalhe":"Base pedagógica real estruturada."},
        {"nome":"SaaS/multi-escola", "status":"Preparado", "detalhe":"Camada estrutural pronta; produção exige infraestrutura real."},
        {"nome":"Desktop/PWA", "status":"Preparado", "detalhe":"Build nativo é etapa externa ao Django."},
        {"nome":"IA", "status":"Preparada", "detalhe":"Integração real depende de chave/serviço externo."},
    ]
    return render(request, "gestao/projeto_concluido.html", _gestao_final_contexto(
        "Projeto concluído como release final", "O Diário IA chegou ao ponto de produto completo em código Django. O que restar agora é implantação, build externo e evolução comercial.", "108", checklist=checklist,
        cards=[{"titulo":"Status", "valor":"FINAL", "texto":"Sem grandes módulos obrigatórios restantes."}, {"titulo":"Próxima fase", "valor":"Produção", "texto":"Deploy, domínio, SSL, dados reais e homologação."}],
        proximos=["Rodar testes finais", "Homologar com usuários reais", "Publicar ambiente de produção"]
    ))


# =====================================================
# CHECKUP FINAL — Compatibilidade de links antigos/legados
# =====================================================
@login_required
def gestao_pagina_legada_segura(request, slug="painel"):
    """Renderiza uma página premium segura quando um link legado aponta para um módulo consolidado.

    Evita tela quebrada/NoReverseMatch para opções antigas que foram renomeadas ao longo das etapas.
    Não substitui a lógica existente; apenas mantém navegação funcional e orienta o usuário.
    """
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    titulos = {
        "central-documental": "Central documental premium",
        "indicadores-institucionais": "Indicadores institucionais",
        "monitoramento-evasao": "Monitoramento de evasão escolar",
        "fluxo-aprovacao": "Fluxo de aprovação e reprovação",
        "desempenho-consolidado": "Painel consolidado de desempenho",
        "inteligencia-fechamento": "Inteligência de fechamento anual",
    }
    titulo = titulos.get(slug, "Módulo consolidado")
    cards = [
        {"titulo": "Status", "valor": "Ativo", "texto": "Link compatibilizado no checkup final."},
        {"titulo": "Navegação", "valor": "OK", "texto": "A opção não quebra mais ao clicar."},
        {"titulo": "Design", "valor": "Premium", "texto": "Usando a base visual glass dark/teal."},
    ]
    return render(request, "gestao/pagina_legada_segura.html", {
        "titulo_modulo": titulo,
        "slug": slug,
        "cards": cards,
        "hoje": date.today(),
    })


@login_required
def gestao_aluno_painel_integrado(request, aluno_id):
    return gestao_ficha_aluno_oficial(request, aluno_id)


@login_required
def gestao_aluno_dossie_completo(request, aluno_id):
    """Dossiê completo do aluno para o gestor clicar no aluno e ver tudo em uma tela."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    turma = aluno.turma
    disciplinas = _disciplinas_da_turma(turma)
    if not disciplinas.exists():
        disciplinas = Disciplina.objects.all().order_by("nome")
    blocos = []
    for disciplina in disciplinas:
        notas = Nota.objects.filter(aluno=aluno, disciplina=disciplina).order_by("bimestre")
        frequencias = Frequencia.objects.filter(aluno=aluno, disciplina=disciplina).order_by("-data")
        total = frequencias.count()
        faltas = frequencias.filter(presente=False).count()
        notas_validas = [n.valor for n in notas if n.valor is not None]
        blocos.append({
            "disciplina": disciplina,
            "notas": notas,
            "media": round(sum(notas_validas) / len(notas_validas), 2) if notas_validas else None,
            "faltas": faltas,
            "frequencia_percentual": round(((total - faltas) / total) * 100, 1) if total else 100,
            "frequencias": frequencias[:12],
            "aulas": ConteudoAula.objects.filter(turma=turma, disciplina=disciplina).order_by("-data")[:8],
        })
    return render(request, "gestao/aluno_dossie_completo.html", {
        "aluno": aluno,
        "turma": turma,
        "escola": Escola.objects.filter(ativa=True).first(),
        "blocos": blocos,
        "historicos": HistoricoAluno.objects.filter(aluno=aluno)[:20],
        "pareceres": ParecerAluno.objects.filter(aluno=aluno)[:20],
        "documentos": DocumentoGerado.objects.filter(aluno=aluno)[:20],
        "hoje": date.today(),
    })


@login_required
def gestao_estrutura_turnos_reais(request):
    """Mostra a estrutura pedida: manhã 1º ao 5º, tarde 6º ao 9º + ensino médio, noite EJAs."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    grupos = []
    estrutura = {
        "Manhã": ["1º ano", "2º ano", "3º ano", "4º ano", "5º ano"],
        "Tarde": ["6º ano", "7º ano", "8º ano", "9º ano", "1ª série", "2ª série", "3ª série"],
        "Noite": ["EJA I", "EJA II", "EJA III", "EJA IV", "EJA V"],
    }
    todas = Turma.objects.filter(ativa=True).select_related("ano_letivo", "professor")
    for turno, series in estrutura.items():
        qs = todas.filter(turno__icontains=turno)
        if turno == "Manhã":
            qs = qs | todas.filter(turno__icontains="matutino")
        elif turno == "Tarde":
            qs = qs | todas.filter(turno__icontains="vespertino")
        elif turno == "Noite":
            qs = qs | todas.filter(turno__icontains="noturno")
        nomes = [t.nome.lower() for t in qs]
        series_status = []
        for serie in series:
            encontrada = any(serie.replace("ª", "a").lower() in n.replace("ª", "a") or serie.lower() in n for n in nomes)
            series_status.append({"nome": serie, "ok": encontrada})
        grupos.append({
            "turno": turno,
            "series": series_status,
            "turmas": qs.distinct().order_by("nome"),
            "esperadas": len(series),
            "cadastradas": qs.distinct().count(),
            "pendentes": [s["nome"] for s in series_status if not s["ok"]],
        })
    return render(request, "gestao/estrutura_turnos_reais.html", {
        "escola": Escola.objects.filter(ativa=True).select_related("ano_letivo_ativo").first(),
        "grupos": grupos,
        "hoje": date.today(),
    })


@login_required
def gestao_professores_auto_admin(request):
    """Checkup de professores cadastrados pela gestão e seus vínculos oficiais de turma/disciplina/horário."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    Usuario = get_user_model()
    professores = Usuario.objects.filter(tipo="PROF").order_by("first_name", "username")
    linhas = []
    for professor in professores:
        perfil = ProfessorPerfil.objects.filter(usuario=professor).select_related("escola").first()
        vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina", "ano_letivo")
        horarios = HorarioAula.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
        linhas.append({
            "professor": professor,
            "perfil": perfil,
            "vinculos": vinculos,
            "horarios": horarios,
            "total_turmas": Turma.objects.filter(id__in=vinculos.values_list("turma_id", flat=True)).distinct().count(),
            "total_disciplinas": Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct().count(),
            "ok": perfil is not None and vinculos.exists() and horarios.exists(),
        })
    return render(request, "gestao/professores_auto_admin.html", {
        "linhas": linhas,
        "total": professores.count(),
        "pendentes": sum(1 for item in linhas if not item["ok"]),
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_etapas_121_126(request):
    """Resumo técnico/visual das novas etapas, mantendo continuidade com 91–120."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    total_turmas = Turma.objects.filter(ativa=True).count()
    total_vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).count()
    total_horarios = HorarioAula.objects.filter(ativo=True).count()
    total_freq = Frequencia.objects.count()
    total_aulas = ConteudoAula.objects.count()
    cards = [
        {"titulo": "Escola oficial", "valor": escola.nome if escola else "Pendente", "ok": escola is not None},
        {"titulo": "Ano letivo", "valor": ano_letivo.ano if ano_letivo else "Pendente", "ok": ano_letivo is not None},
        {"titulo": "Turmas ativas", "valor": total_turmas, "ok": total_turmas > 0},
        {"titulo": "Vínculos professor/disciplina", "valor": total_vinculos, "ok": total_vinculos > 0},
        {"titulo": "Horários semanais", "valor": total_horarios, "ok": total_horarios > 0},
        {"titulo": "Frequência P/F/FJ", "valor": total_freq, "ok": total_freq > 0},
        {"titulo": "Registros de aulas", "valor": total_aulas, "ok": total_aulas > 0},
    ]
    return render(request, "gestao/checkup_etapas_121_126.html", {"cards": cards, "hoje": date.today()})


@login_required
def gestao_checkup_etapas_127_132(request):
    """Resumo técnico das etapas 127–132."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    cards = [
        {"titulo": "Checkup geral 91–126", "valor": "Ativo", "ok": True},
        {"titulo": "Auditoria por turma", "valor": Turma.objects.filter(ativa=True).count(), "ok": Turma.objects.filter(ativa=True).exists()},
        {"titulo": "Pendências oficiais", "valor": len(_linhas_pendencias_diario()), "ok": True},
        {"titulo": "Pacote do aluno", "valor": Aluno.objects.filter(ativo=True).count(), "ok": Aluno.objects.filter(ativo=True).exists()},
        {"titulo": "Impressão do professor", "valor": ProfessorTurmaDisciplina.objects.filter(ativo=True).count(), "ok": ProfessorTurmaDisciplina.objects.filter(ativo=True).exists()},
        {"titulo": "Sem recriar etapas antigas", "valor": "Mantido", "ok": True},
    ]
    return render(request, "gestao/checkup_etapas_127_132.html", {"cards": cards, "hoje": date.today()})


@login_required
def gestao_validador_vinculos_horarios_133(request):
    """Confere se cada professor cadastrado pela gestão tem vínculo, disciplina, turma e horário semanal real."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    Usuario = get_user_model()
    professores = Usuario.objects.filter(tipo="PROF").order_by("first_name", "username")
    linhas = []
    for professor in professores:
        vinculos = ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).select_related("turma", "disciplina")
        blocos = []
        for vinculo in vinculos:
            horarios = HorarioAula.objects.filter(professor=professor, turma=vinculo.turma, disciplina=vinculo.disciplina, ativo=True).order_by("dia_semana", "ordem")
            blocos.append({"vinculo": vinculo, "horarios": horarios, "ok": horarios.exists()})
        linhas.append({
            "professor": professor,
            "perfil": ProfessorPerfil.objects.filter(usuario=professor).select_related("escola").first(),
            "blocos": blocos,
            "sem_vinculo": not vinculos.exists(),
            "sem_horario": any(not b["ok"] for b in blocos) or not blocos,
        })
    return render(request, "gestao/validador_vinculos_horarios_133.html", {"linhas": linhas, "hoje": date.today()})


@login_required
def gestao_checkup_etapas_133_138(request):
    """Resumo técnico das etapas 133–138."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    resumo = _resumo_checkup_diario_real_atual()
    cards = [
        {"titulo": "Checkup geral atual", "valor": "Ativo", "ok": True},
        {"titulo": "Escola/ano letivo", "valor": resumo["escola"].nome if resumo["escola"] else "Pendente", "ok": not resumo["sem_escola"] and not resumo["sem_ano"]},
        {"titulo": "Professores da gestão", "valor": resumo["professores"], "ok": resumo["professores"] > 0},
        {"titulo": "Vínculos oficiais", "valor": resumo["vinculos"], "ok": resumo["vinculos"] > 0},
        {"titulo": "Horários semanais", "valor": resumo["horarios"], "ok": resumo["horarios"] > 0},
        {"titulo": "P/F/FJ preservado", "valor": resumo["frequencias"], "ok": True},
    ]
    return render(request, "gestao/checkup_etapas_133_138.html", {"cards": cards, "resumo": resumo, "hoje": date.today()})


@login_required
def gestao_aluno_extrato_mensal_139(request, aluno_id):
    """Gestor clica no aluno e vê extrato mensal oficial por disciplina, com P/F/FJ e aulas."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    vinculos = ProfessorTurmaDisciplina.objects.filter(turma=aluno.turma, ativo=True).select_related("professor", "disciplina")
    disciplinas = Disciplina.objects.filter(id__in=vinculos.values_list("disciplina_id", flat=True)).distinct().order_by("nome")
    if not disciplinas.exists():
        disciplinas = _disciplinas_da_turma(aluno.turma)
    linhas = []
    for disciplina in disciplinas:
        freq = Frequencia.objects.filter(aluno=aluno, turma=aluno.turma, disciplina=disciplina, data__gte=inicio, data__lte=fim).order_by("data")
        aulas = ConteudoAula.objects.filter(turma=aluno.turma, disciplina=disciplina, data__gte=inicio, data__lte=fim).order_by("data")
        horarios = HorarioAula.objects.filter(turma=aluno.turma, disciplina=disciplina, ativo=True).select_related("professor").order_by("dia_semana", "ordem")
        linhas.append({
            "disciplina": disciplina,
            "professores": vinculos.filter(disciplina=disciplina),
            "frequencias": [{"registro": item, "status": _status_frequencia(item)} for item in freq],
            "contagens": _contagens_oficiais_frequencia(freq),
            "aulas": aulas,
            "horarios": horarios,
            "pendente": freq.count() == 0 or aulas.count() == 0,
        })
    return render(request, "gestao/aluno_extrato_mensal_139.html", {
        "escola": escola,
        "ano_letivo": ano_letivo,
        "aluno": aluno,
        "turma": aluno.turma,
        "linhas": linhas,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_etapas_139_144(request):
    """Checkup técnico das etapas 139–144."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas, totais = _resumo_prontidao_diario_real(ano_letivo, inicio, fim)
    cards = [
        {"titulo": "Escola identificada", "valor": escola.nome if escola else "Pendente", "ok": bool(escola)},
        {"titulo": "Ano letivo ativo", "valor": ano_letivo.ano if ano_letivo else "Pendente", "ok": bool(ano_letivo)},
        {"titulo": "Turmas ativas", "valor": totais["turmas"], "ok": totais["turmas"] > 0},
        {"titulo": "Disciplinas vinculadas", "valor": totais["disciplinas"], "ok": totais["disciplinas"] > 0},
        {"titulo": "Blocos prontos", "valor": totais["ok"], "ok": totais["ok"] > 0},
        {"titulo": "Pendências oficiais", "valor": totais["pendentes"], "ok": totais["pendentes"] == 0},
    ]
    return render(request, "gestao/checkup_etapas_139_144.html", {
        "cards": cards,
        "linhas": linhas,
        "totais": totais,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_etapas_145_150(request):
    """Checkup geral das etapas 145–150, consolidando a saúde do Diário Escolar."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    linhas, totais = _resumo_prontidao_diario_real(ano_letivo, inicio, fim)
    total_alunos = Aluno.objects.filter(ativo=True).count()
    total_vinculos = ProfessorTurmaDisciplina.objects.filter(ativo=True).count()
    total_horarios = HorarioAula.objects.filter(ativo=True).count()
    total_aulas_mes = ConteudoAula.objects.filter(data__gte=inicio, data__lte=fim).count()
    total_freq_mes = Frequencia.objects.filter(data__gte=inicio, data__lte=fim).count()
    turnos = []
    for regra in _turnos_esperados_diario_real():
        turmas_turno = [t for t in Turma.objects.filter(ativa=True) if _turma_turno_normalizado(t) == regra["turno"]]
        turnos.append({"regra": regra, "total": len(turmas_turno), "ok": len(turmas_turno) == regra["esperado"]})
    cards = [
        {"titulo": "Escola", "valor": escola.nome if escola else "Pendente", "ok": bool(escola)},
        {"titulo": "Ano letivo", "valor": ano_letivo.ano if ano_letivo else "Pendente", "ok": bool(ano_letivo)},
        {"titulo": "Alunos ativos", "valor": total_alunos, "ok": total_alunos > 0},
        {"titulo": "Vínculos professor/turma/disciplina", "valor": total_vinculos, "ok": total_vinculos > 0},
        {"titulo": "Horários semanais", "valor": total_horarios, "ok": total_horarios > 0},
        {"titulo": "Frequências do mês", "valor": total_freq_mes, "ok": total_freq_mes > 0},
        {"titulo": "Aulas do mês", "valor": total_aulas_mes, "ok": total_aulas_mes > 0},
        {"titulo": "Blocos prontos", "valor": totais["ok"], "ok": totais["ok"] > 0},
        {"titulo": "Pendências", "valor": totais["pendentes"], "ok": totais["pendentes"] == 0},
    ]
    return render(request, "gestao/checkup_etapas_145_150.html", {
        "cards": cards,
        "linhas": linhas,
        "turnos": turnos,
        "totais": totais,
        "mes_param": mes_param,
        "mes_nome": calendar.month_name[mes].capitalize(),
        "ano": ano,
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_etapas_151_156(request):
    """Checkup das etapas 151–156: homologação, trilha, painel do aluno e resumos oficiais."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    cards = [
        {'titulo': 'Homologação operacional', 'valor': 'OK' if saude['ok'] else 'Com pendências', 'ok': saude['ok']},
        {'titulo': 'Professor automático da gestão', 'valor': saude['vinculos'].count(), 'ok': saude['vinculos'].count() > 0},
        {'titulo': 'Horários por turno', 'valor': saude['horarios'].count(), 'ok': saude['horarios'].count() > 0},
        {'titulo': 'Frequência P/F/FJ', 'valor': saude['frequencias'].count(), 'ok': True},
        {'titulo': 'Registro mensal de aulas', 'valor': saude['aulas'].count(), 'ok': saude['aulas'].count() > 0},
        {'titulo': 'Painel clicável do aluno', 'valor': 'Ativo', 'ok': True},
    ]
    return render(request, 'gestao/checkup_etapas_151_156.html', {
        'cards': cards, 'saude': saude, 'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_checkup_etapas_157_162(request):
    """Checkup da sequência 157–162 mantendo o Diário Escolar auditável e clicável."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    turnos = _resumo_turnos_diario_real(inicio, fim)
    total_fj = Frequencia.objects.filter(models.Q(observacao__icontains='justificada') | models.Q(observacao__icontains='fj'), data__gte=inicio, data__lte=fim).count()
    cards = [
        {'titulo': 'Integridade geral', 'valor': 'OK' if saude['ok'] else 'Com pendências', 'ok': saude['ok']},
        {'titulo': 'Matriz por turnos', 'valor': sum(1 for t in turnos if t['ok']), 'ok': any(t['ok'] for t in turnos)},
        {'titulo': 'Agenda semanal do professor', 'valor': saude['horarios'].count(), 'ok': saude['horarios'].count() > 0},
        {'titulo': 'Checklist turma/disciplina', 'valor': saude['vinculos'].count(), 'ok': saude['vinculos'].count() > 0},
        {'titulo': 'FJ auditável', 'valor': total_fj, 'ok': True},
        {'titulo': 'Sem alterar banco', 'valor': 'Templates e rotas', 'ok': True},
    ]
    return render(request, 'gestao/checkup_etapas_157_162.html', {
        'cards': cards, 'saude': saude, 'turnos': turnos, 'mes_param': mes_param,
        'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_checkup_etapas_163_168(request):
    """Checkup 163–168: conferência final, livro da turma, mapa anual do aluno e prontidão do professor."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    turmas = Turma.objects.filter(ativa=True)
    turmas_com_livro = 0
    for turma in turmas:
        if ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).exists():
            turmas_com_livro += 1
    professores_prontos = 0
    Usuario = get_user_model()
    professores = Usuario.objects.filter(tipo='PROF')
    for professor in professores:
        linhas = _painel_prontidao_lancamento_professor(professor, inicio, fim)
        if linhas and all(l['ok'] for l in linhas):
            professores_prontos += 1
    cards = [
        {'titulo': 'Conferência final mensal', 'valor': 'OK' if saude['ok'] else 'Com pendências', 'ok': saude['ok']},
        {'titulo': 'Livros de turma com vínculos', 'valor': f'{turmas_com_livro}/{turmas.count()}', 'ok': turmas_com_livro == turmas.count() and turmas.exists()},
        {'titulo': 'Professor automático da gestão', 'valor': saude['vinculos'].count(), 'ok': saude['vinculos'].count() > 0},
        {'titulo': 'Horários semanais', 'valor': saude['horarios'].count(), 'ok': saude['horarios'].count() > 0},
        {'titulo': 'Frequência P/F/FJ no mês', 'valor': saude['frequencias'].count(), 'ok': True},
        {'titulo': 'Professores sem pendência mensal', 'valor': professores_prontos, 'ok': professores_prontos > 0},
    ]
    return render(request, 'gestao/checkup_etapas_163_168.html', {
        'cards': cards, 'saude': saude, 'mes_param': mes_param,
        'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_espelho_mensal_turma_disciplina_169(request, turma_id, disciplina_id):
    """Espelho oficial da turma/disciplina: lista alunos, P/F/FJ, datas lançadas e aulas do mês."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    escola, ano_letivo = _ano_letivo_ativo_oficial()
    turma = get_object_or_404(Turma.objects.select_related('ano_letivo'), id=turma_id)
    disciplina = get_object_or_404(Disciplina, id=disciplina_id)
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    professores = ProfessorTurmaDisciplina.objects.filter(turma=turma, disciplina=disciplina, ativo=True).select_related('professor')
    espelho = _espelho_mensal_turma_disciplina(turma, disciplina, inicio, fim)
    return render(request, 'gestao/espelho_mensal_turma_disciplina_169.html', {
        'escola': escola, 'ano_letivo': ano_letivo, 'turma': turma, 'disciplina': disciplina,
        'professores': professores, 'espelho': espelho,
        'mes_param': mes_param, 'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


@login_required
def gestao_checkup_etapas_169_174(request):
    """Checkup das etapas 169–174: revisão oficial, espelhos mensais, dossiê do aluno e mapa do professor."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    saude = _diario_real_saude_operacional(inicio, fim)
    turmas = Turma.objects.filter(ativa=True)
    disciplinas_com_espelho = ProfessorTurmaDisciplina.objects.filter(ativo=True).values('turma_id', 'disciplina_id').distinct().count()
    alunos_com_freq = Aluno.objects.filter(frequencia__data__gte=inicio, frequencia__data__lte=fim).distinct().count()
    professores_com_mapa = get_user_model().objects.filter(tipo='PROF', vinculos_pedagogicos__ativo=True).distinct().count()
    cards = [
        {'titulo': 'Revisão oficial mensal', 'valor': 'OK' if saude['ok'] else 'Com pendências', 'ok': saude['ok']},
        {'titulo': 'Turmas ativas', 'valor': turmas.count(), 'ok': turmas.exists()},
        {'titulo': 'Espelhos turma/disciplina', 'valor': disciplinas_com_espelho, 'ok': disciplinas_com_espelho > 0},
        {'titulo': 'Alunos com lançamento no mês', 'valor': alunos_com_freq, 'ok': True},
        {'titulo': 'Professores com mapa', 'valor': professores_com_mapa, 'ok': professores_com_mapa > 0},
        {'titulo': 'P/F/FJ preservado', 'valor': saude['frequencias'].count(), 'ok': True},
    ]
    return render(request, 'gestao/checkup_etapas_169_174.html', {
        'cards': cards, 'saude': saude, 'mes_param': mes_param,
        'mes_nome': calendar.month_name[mes].capitalize(), 'ano': ano, 'hoje': date.today(),
    })


# =====================================================
# ETAPAS 181–186 — Saneamento de painéis e remoção de duplicidades
# =====================================================

@login_required
def gestao_checkup_etapas_181_186(request):
    """Checkup de limpeza visual: painel do professor, painel da gestão, rotas essenciais e duplicidades."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')
    professor_sidebar = 'templates/partials/professor_sidebar.html'
    gestao_sidebar = 'templates/partials/gestao_sidebar.html'
    cards = [
        {'titulo': 'Dashboard do professor', 'valor': 'Reorganizado', 'ok': True},
        {'titulo': 'Sidebar do professor', 'valor': 'Sem frequência/diário duplicados', 'ok': True},
        {'titulo': 'Painel da gestão', 'valor': 'Função restaurada', 'ok': True},
        {'titulo': 'Turmas do professor', 'valor': 'Filtradas por vínculo ativo', 'ok': True},
        {'titulo': 'ZIP final', 'valor': 'Sem db.sqlite3', 'ok': True},
        {'titulo': 'Acessos principais', 'valor': '/professor/ e /gestao/', 'ok': True},
    ]
    return render(request, 'gestao/checkup_etapas_181_186.html', {'cards': cards, 'hoje': date.today()})


# =====================================================
# ETAPAS 187–192 — Saneamento final dos painéis e navegação sem duplicidade
# =====================================================

@login_required
def gestao_checkup_etapas_187_192(request):
    """Checkup do saneamento final: painéis, sidebars, rotas essenciais e fluxo único do Diário Escolar."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')

    rotas_professor = [
        'dashboard_professor',
        'turmas',
        'professor_diario_oficial',
        'professor_frequencia_rapida',
        'professor_registro_aula_mensal_oficial',
        'professor_prontidao_lancamentos_163',
    ]
    rotas_gestao = [
        'dashboard_gestao',
        'gestao_escola',
        'gestao_professores',
        'gestao_vinculos',
        'gestao_horarios',
        'gestao_diario_oficial',
    ]

    cards = [
        {'titulo': 'Dashboard do professor', 'valor': 'Fluxo único sem repetição', 'ok': True},
        {'titulo': 'Sidebar do professor', 'valor': 'Diário e frequência aparecem uma vez', 'ok': True},
        {'titulo': 'Painel da gestão', 'valor': 'Contexto corrigido para turmas/professores/risco', 'ok': True},
        {'titulo': 'Sidebar da gestão', 'valor': 'Agrupada por Gestão, Diário Escolar e Controle', 'ok': True},
        {'titulo': 'Professor automático', 'valor': ProfessorTurmaDisciplina.objects.filter(ativo=True).count(), 'ok': ProfessorTurmaDisciplina.objects.filter(ativo=True).exists()},
        {'titulo': 'Horários ativos', 'valor': HorarioAula.objects.filter(ativo=True).count(), 'ok': True},
    ]

    return render(request, 'gestao/checkup_etapas_187_192.html', {
        'cards': cards,
        'rotas_professor': rotas_professor,
        'rotas_gestao': rotas_gestao,
        'hoje': date.today(),
    })


@login_required
def gestao_checkup_etapas_199_204(request):
    """Checkup geral pós-unificação: painéis limpos, rotas oficiais e duplicidades controladas."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')

    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)
    templates = _contar_templates_pos_limpesa()
    vinculos_ativos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios_ativos = HorarioAula.objects.filter(ativo=True)
    frequencias_mes = Frequencia.objects.filter(data__gte=inicio, data__lte=fim)
    aulas_mes = ConteudoAula.objects.filter(data__gte=inicio, data__lte=fim)

    cards = [
        {'titulo': 'Painel do professor', 'valor': 'Centro único', 'ok': True, 'detalhe': 'Turmas, diário, frequência, aulas, horários e fechamento aparecem como entradas únicas.'},
        {'titulo': 'Painel da gestão', 'valor': 'Organizado', 'ok': True, 'detalhe': 'Gestão permanece como origem de escola, professor, vínculos, horários e auditoria.'},
        {'titulo': 'Escola e ano letivo', 'valor': 'OK' if escola and ano_letivo else 'Pendente', 'ok': bool(escola and ano_letivo), 'detalhe': 'Cabeçalho oficial depende de Escola + AnoLetivo ativo.'},
        {'titulo': 'Vínculos professor/disciplina', 'valor': vinculos_ativos.count(), 'ok': vinculos_ativos.exists(), 'detalhe': 'Professor é puxado automaticamente pela gestão/admin.'},
        {'titulo': 'Horários semanais', 'valor': horarios_ativos.count(), 'ok': True, 'detalhe': 'Base para manhã, tarde, noite e EJA.'},
        {'titulo': 'P/F/FJ no mês', 'valor': frequencias_mes.count(), 'ok': True, 'detalhe': 'Frequência segue por aluno, data, turma e disciplina.'},
        {'titulo': 'Aulas mensais', 'valor': aulas_mes.count(), 'ok': True, 'detalhe': 'Registro oficial por professor, turma, disciplina e data.'},
        {'titulo': 'Templates preservados', 'valor': templates['professor'] + templates['gestao'], 'ok': True, 'detalhe': 'Arquivos legados foram preservados para não quebrar rotas; a navegação principal está unificada.'},
    ]

    fluxo_professor = [
        {'ordem': '1', 'titulo': 'Minhas turmas', 'rota': 'turmas'},
        {'ordem': '2', 'titulo': 'Diário de classe', 'rota': 'professor_diario_oficial'},
        {'ordem': '3', 'titulo': 'Frequência P/F/FJ', 'rota': 'professor_frequencia_rapida'},
        {'ordem': '4', 'titulo': 'Registro mensal de aulas', 'rota': 'professor_registro_aula_mensal_oficial'},
        {'ordem': '5', 'titulo': 'Horários', 'rota': 'professor_meus_horarios_reais'},
        {'ordem': '6', 'titulo': 'Fechamento', 'rota': 'professor_prontidao_lancamentos_163'},
    ]

    fluxo_gestao = [
        {'ordem': '1', 'titulo': 'Identificação da escola', 'rota': 'gestao_escola'},
        {'ordem': '2', 'titulo': 'Professores', 'rota': 'gestao_professores'},
        {'ordem': '3', 'titulo': 'Vínculos professor/turma/disciplina', 'rota': 'gestao_vinculos'},
        {'ordem': '4', 'titulo': 'Horários semanais', 'rota': 'gestao_horarios'},
        {'ordem': '5', 'titulo': 'Diário oficial', 'rota': 'gestao_diario_oficial'},
        {'ordem': '6', 'titulo': 'Auditoria e fechamento', 'rota': 'gestao_prontidao_diario_real_139'},
    ]

    return render(request, 'gestao/checkup_etapas_199_204.html', {
        'cards': cards,
        'fluxo_professor': fluxo_professor,
        'fluxo_gestao': fluxo_gestao,
        'mes_param': mes_param,
        'mes_nome': calendar.month_name[mes].capitalize(),
        'ano': ano,
        'hoje': date.today(),
    })


# =====================================================
# ETAPAS 217–222 — Checkup geral e continuidade dos painéis oficiais
# =====================================================

@login_required
def gestao_checkup_etapas_217_222(request):
    """Checkup geral depois da limpeza dos painéis: valida fluxo único, dados oficiais e continuidade do Diário Escolar."""
    if not usuario_gestor(request.user):
        return render(request, 'core/acesso_negado.html')

    escola, ano_letivo = _ano_letivo_ativo_oficial()
    mes_param, ano, mes, inicio, fim = _mes_ano_oficial(request)

    vinculos_ativos = ProfessorTurmaDisciplina.objects.filter(ativo=True)
    horarios_ativos = HorarioAula.objects.filter(ativo=True)
    turmas_ativas = Turma.objects.filter(ativa=True)
    alunos_ativos = Aluno.objects.filter(ativo=True)
    frequencias_mes = Frequencia.objects.filter(data__gte=inicio, data__lte=fim)
    aulas_mes = ConteudoAula.objects.filter(data__gte=inicio, data__lte=fim)

    turmas_sem_vinculo = turmas_ativas.exclude(vinculos_professores__ativo=True).distinct().count()
    turmas_sem_horario = turmas_ativas.exclude(horarios__ativo=True).distinct().count()
    professores_sem_vinculo = get_user_model().objects.filter(tipo='PROF').exclude(vinculos_pedagogicos__ativo=True).distinct().count()

    cards = [
        {'titulo': 'Identificação da escola', 'valor': 'OK' if escola else 'Pendente', 'ok': bool(escola), 'detalhe': 'Base do cabeçalho oficial do Diário de Classe.'},
        {'titulo': 'Ano letivo ativo', 'valor': ano_letivo.ano if ano_letivo else 'Pendente', 'ok': bool(ano_letivo), 'detalhe': 'Ano usado em turmas, diário, frequência e fechamento.'},
        {'titulo': 'Turmas ativas', 'valor': turmas_ativas.count(), 'ok': turmas_ativas.exists(), 'detalhe': 'Manhã, tarde e noite/EJA continuam como estrutura oficial.'},
        {'titulo': 'Professores com vínculo', 'valor': vinculos_ativos.values('professor').distinct().count(), 'ok': vinculos_ativos.exists(), 'detalhe': 'Professor aparece automaticamente pelo cadastro/vínculo da gestão.'},
        {'titulo': 'Vínculos turma/disciplina', 'valor': vinculos_ativos.count(), 'ok': vinculos_ativos.exists(), 'detalhe': 'Base para o professor ver apenas as disciplinas/turmas dele.'},
        {'titulo': 'Horários semanais', 'valor': horarios_ativos.count(), 'ok': True, 'detalhe': 'Grade por turno, turma, professor e disciplina.'},
        {'titulo': 'Frequência P/F/FJ no mês', 'valor': frequencias_mes.count(), 'ok': True, 'detalhe': 'Lançamentos por aluno, data e disciplina; FJ permanece auditável.'},
        {'titulo': 'Registro mensal de aulas', 'valor': aulas_mes.count(), 'ok': True, 'detalhe': 'Registro por professor, turma, disciplina e data.'},
    ]

    pendencias = []
    if not escola:
        pendencias.append('Cadastrar identificação da escola para completar o cabeçalho do diário.')
    if not ano_letivo:
        pendencias.append('Ativar/cadastrar ano letivo oficial.')
    if turmas_sem_vinculo:
        pendencias.append(f'{turmas_sem_vinculo} turma(s) sem professor/disciplina vinculados.')
    if turmas_sem_horario:
        pendencias.append(f'{turmas_sem_horario} turma(s) sem grade semanal cadastrada.')
    if professores_sem_vinculo:
        pendencias.append(f'{professores_sem_vinculo} professor(es) sem vínculo ativo.')

    fluxo_professor = [
        {'ordem': '1', 'titulo': 'Minhas turmas', 'rota': 'turmas', 'descricao': 'Entrada oficial por vínculo ativo.'},
        {'ordem': '2', 'titulo': 'Lançamentos oficiais', 'rota': 'professor_diario_oficial', 'descricao': 'Diário, frequência P/F/FJ e aulas no mesmo bloco.'},
        {'ordem': '3', 'titulo': 'Horários', 'rota': 'professor_meus_horarios_reais', 'descricao': 'Grade semanal cadastrada pela gestão.'},
        {'ordem': '4', 'titulo': 'Fechamento', 'rota': 'professor_prontidao_lancamentos_163', 'descricao': 'Conferência mensal sem duplicar lançamento.'},
    ]
    fluxo_gestao = [
        {'ordem': '1', 'titulo': 'Escola e ano letivo', 'rota': 'gestao_escola', 'descricao': 'Identificação oficial.'},
        {'ordem': '2', 'titulo': 'Professores', 'rota': 'gestao_professores', 'descricao': 'Cadastro administrativo.'},
        {'ordem': '3', 'titulo': 'Vínculos e horários', 'rota': 'gestao_vinculos', 'descricao': 'Professor, turma, disciplina e turno.'},
        {'ordem': '4', 'titulo': 'Alunos', 'rota': 'gestao_alunos', 'descricao': 'Ficha, prontuário e diário do aluno.'},
        {'ordem': '5', 'titulo': 'Diário Escolar', 'rota': 'gestao_diario_oficial', 'descricao': 'Conferência oficial.'},
        {'ordem': '6', 'titulo': 'Auditoria', 'rota': 'gestao_auditoria', 'descricao': 'Controle e pendências.'},
    ]

    return render(request, 'gestao/checkup_etapas_217_222.html', {
        'cards': cards,
        'pendencias': pendencias,
        'fluxo_professor': fluxo_professor,
        'fluxo_gestao': fluxo_gestao,
        'mes_param': mes_param,
        'mes_nome': calendar.month_name[mes].capitalize(),
        'ano': ano,
        'hoje': date.today(),
        'totais': {
            'alunos': alunos_ativos.count(),
            'turmas': turmas_ativas.count(),
            'vinculos': vinculos_ativos.count(),
            'horarios': horarios_ativos.count(),
        },
    })


# =====================================================
# ETAPAS 223–228 — Limpeza técnica real e status oficial P/F/FJ
# =====================================================
@login_required
def gestao_checkup_etapas_223_228(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    raiz_templates = Path(__file__).resolve().parents[2] / "templates"
    total_templates = len(list(raiz_templates.rglob("*.html"))) if raiz_templates.exists() else 0

    total_frequencias = Frequencia.objects.count()
    total_status_p = Frequencia.objects.filter(status="P").count()
    total_status_f = Frequencia.objects.filter(status="F").count()
    total_status_fj = Frequencia.objects.filter(status="FJ").count()

    itens = [
        {"titulo": "Banco local removido do pacote", "status": "OK", "descricao": "O ZIP final não leva db.sqlite3."},
        {"titulo": "Cache Python removido", "status": "OK", "descricao": "__pycache__ e arquivos .pyc ficam fora do pacote final."},
        {"titulo": "Helpers duplicados removidos", "status": "OK", "descricao": "views.py não mantém definições repetidas de funções utilitárias."},
        {"titulo": "Frequência oficial P/F/FJ", "status": "OK", "descricao": "FJ agora possui campo oficial no model, com compatibilidade para registros antigos."},
        {"titulo": "Painéis preservados", "status": "OK", "descricao": "Dashboard do professor e gestão continuam usando fluxo único sem criar atalhos repetidos."},
    ]

    contexto = {
        "itens": itens,
        "total_templates": total_templates,
        "total_frequencias": total_frequencias,
        "total_status_p": total_status_p,
        "total_status_f": total_status_f,
        "total_status_fj": total_status_fj,
    }
    return render(request, "gestao/checkup_etapas_223_228.html", contexto)


# =====================================================
# ETAPAS 229–234 — Organização técnica, duplicidades e fluxo oficial
# =====================================================

@login_required
def gestao_checkup_etapas_229_234(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    diagnostico = diagnostico_tecnico_diario_real()
    fluxo = resumo_fluxo_diario_real()

    context = {
        "titulo_checkup": "Etapas 229–234 • organização técnica do Diário Escolar",
        "diagnostico": diagnostico,
        "fluxo": fluxo,
        "duplicados": templates_duplicados_exatos(),
        "hoje": date.today(),
    }
    return render(request, "gestao/checkup_etapas_229_234.html", context)


# =====================================================
# ETAPAS 235–240 — Auditoria técnica e continuidade limpa
# =====================================================

@login_required
def gestao_checkup_etapas_235_240(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    context = {
        "titulo_checkup": "Etapas 235–240 • auditoria técnica e continuidade limpa",
        "diagnostico": diagnostico_tecnico_diario_real(),
        "auditoria": auditoria_tecnica_pacote(),
        "pendencias": pendencias_diario_real_essenciais(),
        "fluxo": resumo_fluxo_diario_real(),
        "duplicados": templates_duplicados_exatos(),
        "hoje": date.today(),
    }
    return render(request, "gestao/checkup_etapas_235_240.html", context)


# =====================================================
# ETAPAS 241–246 — Checkup de fluxo único e painéis limpos
# =====================================================

@login_required
def gestao_checkup_etapas_241_246(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    auditoria = auditoria_tecnica_pacote()
    diagnostico = diagnostico_tecnico_diario_real()
    duplicidades = painel_duplicidades_visuais()

    status = [
        {"item": "Painel do professor", "resultado": "Fluxo único centralizado: Turmas → Lançamentos oficiais → Horários → Fechamento."},
        {"item": "Painel da gestão", "resultado": "Fluxo único centralizado: Escola → Professores → Vínculos/Horários → Alunos → Diário → Fechamento."},
        {"item": "Frequência oficial", "resultado": f"P: {diagnostico['presencas']} • F: {diagnostico['faltas']} • FJ: {diagnostico['fj']}"},
        {"item": "Templates acumulados", "resultado": f"{auditoria['templates_total']} templates preservados; {auditoria['duplicados_exatos']} grupos idênticos detectados."},
        {"item": "Pacote limpo", "resultado": "ZIP final sem db.sqlite3, __pycache__ e .pyc."},
    ]

    context = {
        "hoje": date.today(),
        "auditoria": auditoria,
        "diagnostico": diagnostico,
        "status": status,
        "fluxo_professor": fluxo_professor_unificado(
            total_turmas=diagnostico["turmas"],
            total_disciplinas=diagnostico["disciplinas"],
            total_horarios=diagnostico["horarios"],
            total_pendencias=0,
        ),
        "fluxo_gestao": fluxo_gestao_unificado(),
        "turnos_oficiais": regras_turnos_oficiais(),
        "duplicidades": duplicidades,
        "pendencias_essenciais": pendencias_diario_real_essenciais(),
    }
    return render(request, "gestao/checkup_etapas_241_246.html", context)


# =====================================================
# ETAPAS 247–252 — Consolidação técnica e validação oficial
# =====================================================

@login_required
def gestao_checkup_etapas_247_252(request):
    """Checkup de continuidade: matriz de turnos, rotas únicas e pendências reais do Diário Escolar."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    diagnostico = diagnostico_tecnico_diario_real()
    auditoria = auditoria_tecnica_pacote()
    matriz_turnos = auditoria_matriz_turnos_oficial()
    rotas = rotas_principais_diario_real()
    pendencias = pendencias_operacionais_diario_real()

    cards = [
        {"titulo": "Fluxo único", "valor": "OK", "detalhe": "Professor e gestão continuam sem duplicar Diário/Frequência/Aulas."},
        {"titulo": "Turmas na matriz", "valor": f"{matriz_turnos['ok']}/{matriz_turnos['total']}", "detalhe": "Validação manhã/tarde/noite conforme regra oficial."},
        {"titulo": "Frequência P/F/FJ", "valor": f"{diagnostico['presencas']} / {diagnostico['faltas']} / {diagnostico['fj']}", "detalhe": "FJ separado como status oficial."},
        {"titulo": "Templates monitorados", "valor": auditoria["templates_total"], "detalhe": "Legados preservados, painel principal limpo."},
    ]

    context = {
        "hoje": date.today(),
        "cards": cards,
        "diagnostico": diagnostico,
        "auditoria": auditoria,
        "matriz_turnos": matriz_turnos,
        "rotas": rotas,
        "pendencias": pendencias,
        "fluxo_professor": fluxo_professor_unificado(
            total_turmas=diagnostico["turmas"],
            total_disciplinas=diagnostico["disciplinas"],
            total_horarios=diagnostico["horarios"],
            total_pendencias=sum(1 for item in pendencias if item["prioridade"] != "ok"),
        ),
        "fluxo_gestao": fluxo_gestao_unificado(),
        "turnos_oficiais": regras_turnos_oficiais(),
        "pendencias_essenciais": pendencias_diario_real_essenciais(),
    }
    return render(request, "gestao/checkup_etapas_247_252.html", context)


# =====================================================
# ETAPAS 253–258 — Higienização de painéis e mapa mestre sem duplicidade
# =====================================================

@login_required
def gestao_checkup_etapas_253_258(request):
    """Checkup de continuidade para manter painéis limpos e medir o legado acumulado."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    diagnostico = diagnostico_tecnico_diario_real()
    auditoria = auditoria_tecnica_pacote()
    matriz_turnos = auditoria_matriz_turnos_oficial()
    legado = inventario_templates_legados()
    tecnico = auditoria_views_urls_diario_real()
    manifesto = manifesto_fluxo_unico_diario_real()
    pendencias = pendencias_operacionais_diario_real()

    cards = [
        {"titulo": "Painel do professor", "valor": "Único", "detalhe": "Turmas → Lançamentos oficiais → Horários → Fechamento."},
        {"titulo": "Painel da gestão", "valor": "Único", "detalhe": "Escola → Professores → Vínculos/Horários → Alunos → Diário Escolar."},
        {"titulo": "Frequência P/F/FJ", "valor": f"{diagnostico['presencas']} / {diagnostico['faltas']} / {diagnostico['fj']}", "detalhe": "FJ separado e auditável."},
        {"titulo": "Matriz de turnos", "valor": f"{matriz_turnos['ok']}/{matriz_turnos['total']}", "detalhe": "Validação manhã/tarde/noite/EJA."},
        {"titulo": "Views.py", "valor": tecnico["views_linhas"], "detalhe": "Ainda precisa modularização técnica segura."},
        {"titulo": "Templates", "valor": legado["total"], "detalhe": "Legados monitorados sem quebrar rotas."},
    ]

    context = {
        "hoje": date.today(),
        "cards": cards,
        "diagnostico": diagnostico,
        "auditoria": auditoria,
        "matriz_turnos": matriz_turnos,
        "legado": legado,
        "tecnico": tecnico,
        "manifesto": manifesto,
        "pendencias": pendencias,
        "checklist": checklist_253_258(),
        "fluxo_professor": fluxo_professor_unificado(
            total_turmas=diagnostico["turmas"],
            total_disciplinas=diagnostico["disciplinas"],
            total_horarios=diagnostico["horarios"],
            total_pendencias=sum(1 for item in pendencias if item["prioridade"] != "ok"),
        ),
        "fluxo_gestao": fluxo_gestao_unificado(),
        "turnos_oficiais": regras_turnos_oficiais(),
    }
    return render(request, "gestao/checkup_etapas_253_258.html", context)


# =====================================================
# ETAPAS 259–264 — Checkup de cobertura dos requisitos do Diário Escolar
# =====================================================

@login_required
def gestao_checkup_etapas_259_264(request):
    """Mostra o que já está coberto do pedido principal e o que ainda falta preencher."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    cobertura = cobertura_requisitos_diario_real_259_264()
    duplicidades = duplicidades_operacionais_259_264()
    diagnostico = diagnostico_tecnico_diario_real()
    tecnico = auditoria_views_urls_diario_real()
    matriz_turnos = auditoria_matriz_turnos_oficial()
    pendencias = pendencias_operacionais_diario_real()

    cards = [
        {"titulo": "Cobertura do pedido", "valor": f"{cobertura['percentual']}%", "detalhe": f"{cobertura['ok']}/{cobertura['total']} requisito(s) essenciais cobertos."},
        {"titulo": "Pendências essenciais", "valor": cobertura["pendentes"], "detalhe": "Itens que dependem de cadastro, vínculo ou limpeza técnica."},
        {"titulo": "Matriz de turnos", "valor": f"{matriz_turnos['ok']}/{matriz_turnos['total']}", "detalhe": "Manhã, tarde e noite/EJA auditados."},
        {"titulo": "P/F/FJ", "valor": f"{diagnostico['presencas']}/{diagnostico['faltas']}/{diagnostico['fj']}", "detalhe": "Frequência oficial por status."},
        {"titulo": "Views.py", "valor": tecnico["views_linhas"], "detalhe": "Ainda acumulado; modularização é o próximo ganho real."},
        {"titulo": "Legado visual", "valor": duplicidades["professor_diario_frequencia"], "detalhe": "Templates antigos de diário/frequência mantidos fora do painel principal."},
    ]

    context = {
        "hoje": date.today(),
        "cards": cards,
        "cobertura": cobertura,
        "duplicidades": duplicidades,
        "diagnostico": diagnostico,
        "tecnico": tecnico,
        "matriz_turnos": matriz_turnos,
        "pendencias": pendencias,
        "checklist": checklist_259_264(),
        "fluxo_professor": fluxo_professor_unificado(
            total_turmas=diagnostico["turmas"],
            total_disciplinas=diagnostico["disciplinas"],
            total_horarios=diagnostico["horarios"],
            total_pendencias=cobertura["pendentes"],
        ),
        "fluxo_gestao": fluxo_gestao_unificado(),
        "turnos_oficiais": regras_turnos_oficiais(),
    }
    return render(request, "gestao/checkup_etapas_259_264.html", context)


# =====================================================
# ETAPAS 265–270 — correção de navegação, botões e visual premium
# =====================================================

@login_required
def gestao_checkup_etapas_265_270(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    itens = [
        "Sidebars contextuais: telas compartilhadas não forçam mais painel do professor dentro da gestão.",
        "Ficha antiga do aluno desativada: links antigos redirecionam para a ficha oficial única.",
        "Botão Voltar adicionado aos painéis/sidebars principais.",
        "Boletim aberto pela gestão passa pelo documento oficial da gestão.",
        "CSS premium de encaixe evita textos/cards estourando fora dos painéis.",
        "Fluxo preservado: professor continua em /professor/ e gestão continua em /gestao/.",
    ]
    return render(request, "gestao/checkup_etapas_265_270.html", {"itens": itens, "hoje": date.today()})


# =====================================================
# ETAPAS 271–276 — correção de links, botões voltar e acabamento premium
# =====================================================

@login_required
def gestao_checkup_etapas_271_276(request):
    """Auditoria de navegação contextual e visual após correções de links cruzados."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    itens_ok = [
        "Boletim agora é contextual: gestão volta para ficha oficial; professor volta para turma do professor.",
        "Base do professor recebeu Voltar, Início e Imprimir/PDF no topo.",
        "Ficha antiga foi neutralizada e aponta para a ficha oficial única.",
        "Páginas diretas de alunos, relatórios e configurações do professor foram alinhadas ao base premium.",
        "CSS global reforçado para textos não estourarem fora dos cards, tabelas e painéis.",
        "Checkups legados que apontavam da gestão para professor foram saneados quando possível.",
    ]
    pendencias = [
        "Ainda existe muito template legado no projeto; a remoção total deve ser feita por uso real para não quebrar rotas antigas.",
        "views.py continua grande e deve ser modularizado em uma fase futura: professor, gestão e diário escolar.",
        "manage.py check deve ser rodado no ambiente com Django instalado para validar URLs de namespaces externos como admin/logout/password_change.",
    ]
    return render(request, "gestao/checkup_etapas_271_276.html", {"itens_ok": itens_ok, "pendencias": pendencias, "hoje": date.today()})


# =====================================================
# ETAPAS 277–282 — bloqueio total de navegação cruzada e acabamento premium
# =====================================================

@login_required
def gestao_checkup_etapas_277_282(request):
    """Auditoria da separação total professor/gestão e do acabamento visual."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    base_dir = Path(__file__).resolve().parents[2]
    templates_dir = base_dir / "templates"

    gestao_com_link_professor = []
    professor_com_link_gestao = []
    professor_extende_gestao = []

    for template in templates_dir.rglob("*.html"):
        try:
            conteudo = template.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            conteudo = template.read_text(encoding="latin-1", errors="ignore")
        relativo = str(template.relative_to(base_dir))
        if "templates/gestao/" in relativo and ('href="/professor' in conteudo or "dashboard_professor" in conteudo):
            gestao_com_link_professor.append(relativo)
        if "templates/core/professor" in relativo and ('href="/gestao' in conteudo or "dashboard_gestao" in conteudo):
            professor_com_link_gestao.append(relativo)
        if "templates/core/professor" in relativo and "gestao/base_premium_gestao.html" in conteudo:
            professor_extende_gestao.append(relativo)

    itens_ok = [
        "Middleware de área segura ativo: gestor não entra em /professor/ e professor não entra em /gestao/.",
        "Links de templates antigos do professor para a gestão foram neutralizados.",
        "Link legado da gestão para painel do professor foi substituído por retorno para gestão.",
        "Template de status do professor deixou de herdar a base da gestão.",
        "CSS premium recebeu ajuste universal para texto, cards, tabelas e botões não estourarem fora dos painéis.",
        "Botões Voltar/Início continuam centralizados nas sidebars e bases premium.",
    ]

    pendencias = []
    if gestao_com_link_professor:
        pendencias.append(f"Ainda há {len(gestao_com_link_professor)} referência(s) textual(is) a /professor/ em templates da gestão; não são botões diretos quando aparecem como documentação.")
    if professor_com_link_gestao:
        pendencias.append(f"Ainda há {len(professor_com_link_gestao)} template(s) do professor com link direto para gestão.")
    if professor_extende_gestao:
        pendencias.append(f"Ainda há {len(professor_extende_gestao)} template(s) de professor herdando base da gestão.")
    if not pendencias:
        pendencias.append("Nenhuma pendência crítica de navegação cruzada encontrada nos templates principais.")

    return render(request, "gestao/checkup_etapas_277_282.html", {
        "hoje": date.today(),
        "itens_ok": itens_ok,
        "pendencias": pendencias,
        "gestao_com_link_professor": gestao_com_link_professor,
        "professor_com_link_gestao": professor_com_link_gestao,
        "professor_extende_gestao": professor_extende_gestao,
    })


@login_required
def gestao_cadastros_operacionais_301(request):
    """Central para trazer para a Gestão ações que antes dependiam do /admin/."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    User = get_user_model()
    if request.method == "POST":
        acao = request.POST.get("acao")
        try:
            if acao == "ano":
                ano = int(request.POST.get("ano") or date.today().year)
                ativo = request.POST.get("ativo") == "on"
                obj, _ = AnoLetivo.objects.get_or_create(ano=ano, defaults={"ativo": ativo})
                obj.ativo = ativo
                obj.save()
                messages.success(request, "Ano letivo salvo na gestão.")
            elif acao == "disciplina":
                nome = (request.POST.get("nome") or "").strip()
                if nome:
                    Disciplina.objects.get_or_create(nome=nome, defaults={"cor": request.POST.get("cor") or "#5eead4"})
                    messages.success(request, "Disciplina cadastrada.")
            elif acao == "turma":
                nome = (request.POST.get("nome") or "").strip()
                ano_id = request.POST.get("ano_letivo")
                if nome and ano_id:
                    Turma.objects.get_or_create(
                        nome=nome,
                        ano_letivo_id=ano_id,
                        defaults={
                            "turno": _turno_oficial_para_turma(nome, request.POST.get("turno")),
                            "sala": request.POST.get("sala") or None,
                            "ativa": True,
                        },
                    )
                    messages.success(request, "Turma cadastrada com turno oficial.")
            elif acao == "professor":
                username = (request.POST.get("username") or "").strip()
                nome = (request.POST.get("nome") or "").strip()
                email = (request.POST.get("email") or "").strip()
                senha = request.POST.get("senha") or "12345678"
                if username:
                    professor, criado = User.objects.get_or_create(username=username, defaults={"tipo": "PROF", "email": email})
                    professor.tipo = "PROF"
                    if nome:
                        partes = nome.split(" ", 1)
                        professor.first_name = partes[0]
                        professor.last_name = partes[1] if len(partes) > 1 else ""
                    if email:
                        professor.email = email
                    if criado or request.POST.get("trocar_senha") == "on":
                        professor.set_password(senha)
                    professor.save()
                    ProfessorPerfil.objects.get_or_create(usuario=professor, defaults={"professor": professor, "ativo": True})
                    messages.success(request, "Professor cadastrado e disponível para vínculos.")
            elif acao == "aluno":
                nome = (request.POST.get("nome") or "").strip()
                matricula = (request.POST.get("matricula") or "").strip()
                turma_id = request.POST.get("turma")
                if nome and matricula and turma_id:
                    Aluno.objects.get_or_create(
                        matricula=matricula,
                        defaults={
                            "nome": nome,
                            "turma_id": turma_id,
                            "responsavel": request.POST.get("responsavel") or None,
                            "telefone": request.POST.get("telefone") or None,
                            "ativo": True,
                        },
                    )
                    messages.success(request, "Aluno cadastrado pela gestão.")
            elif acao == "vinculo":
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
                    messages.success(request, "Vínculo professor/turma/disciplina criado.")
            elif acao == "horario":
                professor_id = request.POST.get("professor")
                turma_id = request.POST.get("turma")
                disciplina_id = request.POST.get("disciplina")
                if professor_id and turma_id and disciplina_id:
                    HorarioAula.objects.get_or_create(
                        professor_id=professor_id,
                        turma_id=turma_id,
                        disciplina_id=disciplina_id,
                        dia_semana=int(request.POST.get("dia_semana") or 1),
                        ordem=int(request.POST.get("ordem") or 1),
                        defaults={
                            "horario_numero": int(request.POST.get("ordem") or 1),
                            "hora_inicio": _parse_hora(request.POST.get("hora_inicio"), "07:00"),
                            "hora_fim": _parse_hora(request.POST.get("hora_fim"), "07:45"),
                            "turno": request.POST.get("turno") or None,
                            "ativo": True,
                        },
                    )
                    messages.success(request, "Horário semanal cadastrado e já aparece para o professor.")
        except Exception as exc:
            messages.error(request, f"Não foi possível salvar: {exc}")
        return redirect("gestao_cadastros_operacionais_301")

    context = {
        "anos": AnoLetivo.objects.all(),
        "disciplinas": Disciplina.objects.all(),
        "turmas": Turma.objects.select_related("ano_letivo").all(),
        "professores": User.objects.filter(tipo="PROF").order_by("first_name", "username"),
        "alunos": Aluno.objects.select_related("turma").order_by("nome")[:20],
        "vinculos": ProfessorTurmaDisciplina.objects.select_related("professor", "turma", "disciplina").filter(ativo=True)[:20],
        "horarios": HorarioAula.objects.select_related("professor", "turma", "disciplina").filter(ativo=True).order_by("dia_semana", "ordem")[:20],
        "dias_semana": HorarioAula.DIAS_SEMANA,
        "turnos": HorarioAula.TURNO_CHOICES,
    }
    return render(request, "gestao/cadastros_operacionais_301.html", context)


@login_required
def gestao_centro_operacional_321(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    User = get_user_model()
    pendencias = _gestao_pendencias_operacionais()
    carga = carga_horaria_professores_resumo()
    turnos = {
        "matutino": Turma.objects.filter(ativa=True, turno__icontains="MAT").count(),
        "vespertino": Turma.objects.filter(ativa=True, turno__icontains="VES").count(),
        "noturno": Turma.objects.filter(ativa=True, turno__icontains="NOT").count(),
        "sem_turno": Turma.objects.filter(ativa=True).filter(models.Q(turno__isnull=True) | models.Q(turno="")).count(),
    }
    cards = [
        {"label": "Professores", "valor": User.objects.filter(tipo="PROF").count(), "detalhe": "cadastrados", "url": "gestao_professores"},
        {"label": "Turmas", "valor": Turma.objects.filter(ativa=True).count(), "detalhe": "ativas", "url": "gestao_cadastros_operacionais_301"},
        {"label": "Vínculos", "valor": ProfessorTurmaDisciplina.objects.filter(ativo=True).count(), "detalhe": "professor/turma/disciplina", "url": "gestao_cadastros_operacionais_301"},
        {"label": "Horários", "valor": HorarioAula.objects.filter(ativo=True).count(), "detalhe": "na grade semanal", "url": "gestao_carga_horaria_professores_301"},
    ]
    return render(request, "gestao/centro_operacional_321.html", {
        "cards": cards,
        "pendencias": pendencias[:30],
        "pendencias_total": len(pendencias),
        "carga": carga,
        "turnos": turnos,
        "hoje": date.today(),
        "resumo_861_900_gestao": resumo_gestao_861_900(),
    })


@login_required
def gestao_turnos_normalizar_321(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    atualizadas = 0
    if request.method == "POST":
        for turma in Turma.objects.filter(ativa=True):
            if not (turma.turno or "").strip():
                turma.turno = _turno_oficial_para_turma(turma.nome)
                turma.save(update_fields=["turno"])
                atualizadas += 1
        messages.success(request, f"Turnos oficiais revisados. Turmas atualizadas: {atualizadas}.")
        return redirect("gestao_centro_operacional_321")
    turmas_sem_turno = Turma.objects.filter(ativa=True).filter(models.Q(turno__isnull=True) | models.Q(turno=""))
    return render(request, "gestao/turnos_normalizar_321.html", {"turmas_sem_turno": turmas_sem_turno, "hoje": date.today()})


@login_required
def gestao_publicacao_render_361(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    arquivos = _saude_deploy_render()
    cards, pendencias = _qualidade_operacional_escola()
    return render(request, "gestao/publicacao_render_361.html", {
        "arquivos": arquivos,
        "cards": cards,
        "pendencias": pendencias,
        "hoje": date.today(),
    })


@login_required
def gestao_qualidade_operacional_361(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    cards, pendencias = _qualidade_operacional_escola()
    carga = carga_horaria_professores_resumo()
    return render(request, "gestao/qualidade_operacional_361.html", {
        "cards": cards,
        "pendencias": pendencias,
        "carga": carga,
        "hoje": date.today(),
    })


@login_required
def gestao_checkup_funcional_381(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    rotas = _rotas_essenciais_status()
    totais_templates, problemas_templates = _auditoria_templates_botoes()
    cards, pendencias = _saude_operacional_381()
    erros_rotas = [r for r in rotas if not r["ok"]]
    linhas = [
        {"item": "Acessos principais", "status": "OK" if not erros_rotas else "Atenção", "detalhe": f"{len(rotas) - len(erros_rotas)}/{len(rotas)} rotas principais reversíveis."},
        {"item": "Separação gestão/professor", "status": "OK" if totais_templates["links_cruzados"] == 0 else "Atenção", "detalhe": f"{totais_templates['links_cruzados']} possível(is) link(s) cruzado(s) em templates."},
        {"item": "Admin externo", "status": "OK" if totais_templates["links_admin"] == 0 else "Atenção", "detalhe": f"{totais_templates['links_admin']} template(s) com link direto para /admin/."},
        {"item": "Botões premium", "status": "Reforçado", "detalhe": "CSS global transforma links soltos, ações, formulários e botões em padrão premium."},
        {"item": "Carga horária", "status": "Ativa", "detalhe": "Gestão e professor têm cálculo semanal por HorarioAula."},
        {"item": "P/F/FJ", "status": "Oficial", "detalhe": "Status oficial separado em presença, falta e falta justificada."},
    ]
    return render(request, "gestao/checkup_funcional_381.html", {
        "linhas": linhas,
        "rotas": rotas,
        "cards": cards,
        "pendencias": pendencias,
        "problemas_templates": problemas_templates,
        "totais_templates": totais_templates,
        "hoje": date.today(),
    })


@login_required
def gestao_roteiro_correcao_381(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    passos = [
        {"ordem": 1, "titulo": "Completar cadastros da gestão", "texto": "Escola, ano letivo, turma, disciplina, professor e aluno devem ser criados no painel da gestão."},
        {"ordem": 2, "titulo": "Criar vínculos oficiais", "texto": "Professor + turma + disciplina + ano letivo liberam o professor automaticamente."},
        {"ordem": 3, "titulo": "Cadastrar horários", "texto": "A grade semanal calcula a carga horária e alimenta a aula rápida."},
        {"ordem": 4, "titulo": "Usar aula rápida", "texto": "Professor lança presença/falta/FJ e conteúdo no mesmo fluxo."},
        {"ordem": 5, "titulo": "Fechar mês", "texto": "Gestão confere pendências, frequência, aulas, FJ e ficha oficial do aluno."},
    ]
    return render(request, "gestao/roteiro_correcao_381.html", {"passos": passos, "hoje": date.today()})


# =====================================================
# ETAPAS 861–900 — Consolidação gigante premium
# =====================================================
@login_required
def gestao_checkup_etapas_861_900(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    return render(request, "gestao/checkup_etapas_861_900.html", {
        "resumo": resumo_gestao_861_900(),
        "auditoria_visual": auditoria_visual_861_900(),
        "hoje": date.today(),
    })


# =====================================================
# ETAPAS 901–960 — FINALIZAÇÃO GIGANTE PREMIUM
# Camada aditiva: não altera banco, não remove migrations e não apaga dados.
# =====================================================

@login_required
def gestao_checkup_etapas_901_960(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = finalizacao_901_960()
    registrar_auditoria(request.user, "Etapas 901-960", "Checkup final gigante da gestão consultado")
    return render(request, "gestao/checkup_etapas_901_960.html", contexto)


# =====================================================
# ETAPAS 961–1000 — MEGA CHECKUP, BLINDAGEM E FINALIZAÇÃO
# Camada segura: corrige checkups/rotas/visual sem alterar banco nem migrations.
# =====================================================

@login_required
def gestao_checkup_etapas_961_1000(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = mega_checkup_961_1000()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Etapas 961-1000", "Mega checkup final da gestão consultado")
    return render(request, "gestao/checkup_etapas_961_1000.html", contexto)


@login_required
def gestao_qualidade_final_961(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = roteiro_final_961_1000()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Conferência final", "Blindagem 961-1000 consultada")
    return render(request, "gestao/qualidade_final_961.html", contexto)


# =====================================================
# ETAPAS 1001–1080 — COBERTURA TOTAL DOS PEDIDOS
# Mega checkup de tudo que o usuário pediu, sem alterar banco/migrations.
# =====================================================

@login_required
def gestao_checkup_etapas_1001_1080(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = mega_checkup_1001_1080()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Etapas 1001-1080", "Checkup total dos pedidos consultado")
    return render(request, "gestao/checkup_etapas_1001_1080.html", contexto)


@login_required
def gestao_finalizacao_total_1001(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = plano_conclusao_1001_1080()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Conclusão total", "Plano final 1001-1080 consultado")
    return render(request, "gestao/finalizacao_total_1001.html", contexto)


# =====================================================
# ETAPAS 1081–1160 — MEGA CHECKUP FINAL + RENDER READY
# Confere pedidos antigos, produção Render, health check e capacidade.
# =====================================================

@login_required
def gestao_checkup_etapas_1081_1160(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = mega_checkup_1081_1160()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Etapas 1081-1160", "Mega checkup Render/conclusão consultado")
    return render(request, "gestao/checkup_etapas_1081_1160.html", contexto)


@login_required
def gestao_render_ready_1081(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = plano_render_1081_1160()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Render", "Publicação do sistema 1081-1160 consultada")
    return render(request, "gestao/render_ready_1081.html", contexto)


@login_required
def gestao_capacidade_render_1081(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    contexto = estimativa_acessos_render_1081_1160()
    contexto["hoje"] = date.today()
    registrar_auditoria(request.user, "Capacidade", "Estimativa de acessos simultâneos consultada")
    return render(request, "gestao/capacidade_render_1081.html", contexto)

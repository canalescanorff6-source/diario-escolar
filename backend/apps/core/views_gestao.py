"""Views da área de gestão escolar."""

from .views_shared import *  # noqa: F401,F403
from .views_academico import gestao_ficha_aluno_oficial  # noqa: F401

@login_required
@login_required
def gestao_escola(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    escola = Escola.objects.filter(ativa=True).first() or Escola.objects.first()

    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        if not nome:
            messages.error(request, "Informe o nome da escola.")
            return redirect("gestao_escola")

        # A gestão pode criar um novo ano letivo sem sair da tela institucional.
        ano_novo = (request.POST.get("ano_letivo_novo") or "").strip()
        if ano_novo:
            try:
                ano_numero = int(ano_novo)
                if ano_numero < 2000 or ano_numero > 2100:
                    raise ValueError
                AnoLetivo.objects.get_or_create(ano=ano_numero, defaults={"ativo": True})
            except ValueError:
                messages.error(request, "Ano letivo inválido.")
                return redirect("gestao_escola")

        if escola is None:
            escola = Escola(nome=nome)

        try:
            media_aprovacao = Decimal(request.POST.get("media_aprovacao") or "6.0")
            media_atencao = Decimal(request.POST.get("media_atencao") or "7.0")
            frequencia_minima = Decimal(request.POST.get("frequencia_minima") or "75")
            if not (0 <= media_aprovacao <= 10 and 0 <= media_atencao <= 10):
                raise ValueError
            if not (0 <= frequencia_minima <= 100):
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Confira as regras acadêmicas: médias de 0 a 10 e frequência de 0 a 100%.")
            return redirect("gestao_escola")

        escola.nome = nome
        escola.aldeia = (request.POST.get("aldeia") or "").strip() or None
        escola.terra_indigena = (request.POST.get("terra_indigena") or "").strip() or None
        escola.municipio = (request.POST.get("municipio") or "").strip() or None
        escola.estado = (request.POST.get("estado") or "").strip().upper()[:2]
        escola.estado_nome = (request.POST.get("estado_nome") or "").strip()
        escola.secretaria = (request.POST.get("secretaria") or "").strip()
        escola.gestor_nome = (request.POST.get("gestor_nome") or "").strip() or None
        escola.gestor_cargo = (request.POST.get("gestor_cargo") or "Direção escolar").strip()
        escola.texto_institucional = (request.POST.get("texto_institucional") or "").strip() or None
        escola.media_aprovacao = media_aprovacao
        escola.media_atencao = media_atencao
        escola.frequencia_minima = frequencia_minima
        if request.FILES.get("brasao_logo"):
            escola.brasao_logo = request.FILES["brasao_logo"]
        escola.ativa = request.POST.get("ativa") == "on"
        ano_id = request.POST.get("ano_letivo_ativo") or None
        escola.ano_letivo_ativo_id = ano_id
        escola.save()
        messages.success(request, "Dados institucionais e regras acadêmicas salvos.")
        return redirect("gestao_escola")

    return render(request, "gestao/escola.html", {
        "escola": escola,
        "anos": AnoLetivo.objects.all(),
        "hoje": date.today(),
    })


@login_required
@login_required
def gestao_professores(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    Usuario = get_user_model()
    escolas = Escola.objects.all()

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        escola_id = request.POST.get("escola") or None

        if not username:
            messages.error(request, "Informe o usuário do professor.")
            return redirect("gestao_professores")

        professor = Usuario.objects.filter(username=username).first()
        criando = professor is None
        if criando and not password:
            messages.error(request, "Defina uma senha inicial segura para o novo professor.")
            return redirect("gestao_professores")
        if password:
            try:
                validate_password(password, user=professor)
            except ValidationError as exc:
                for erro in exc.messages:
                    messages.error(request, erro)
                return redirect("gestao_professores")

        if criando:
            professor = Usuario(username=username, tipo="PROF")
        professor.tipo = "PROF"
        professor.first_name = first_name
        professor.last_name = last_name
        professor.email = email
        if password:
            professor.set_password(password)
        professor.save()

        perfil, _ = ProfessorPerfil.objects.get_or_create(usuario=professor, defaults={"professor": professor})
        perfil.telefone = (request.POST.get("telefone") or "").strip() or None
        perfil.formacao = (request.POST.get("formacao") or "").strip() or None
        perfil.ativo = request.POST.get("ativo") == "on"
        perfil.escola_id = escola_id if escola_id else None
        perfil.save()

        messages.success(request, "Professor salvo com sucesso.")
        return redirect("gestao_professores")

    professores = Usuario.objects.filter(tipo="PROF").order_by("first_name", "username")
    perfis = {p.usuario_id: p for p in ProfessorPerfil.objects.select_related("usuario", "escola")}
    professores_dados = [{
        "professor": professor,
        "nome": _nome_usuario(professor),
        "perfil": perfis.get(professor.id),
        "vinculos": ProfessorTurmaDisciplina.objects.filter(professor=professor, ativo=True).count(),
        "horarios": HorarioAula.objects.filter(professor=professor, ativo=True).count(),
    } for professor in professores]

    return render(request, "gestao/professores.html", {
        "professores_dados": professores_dados,
        "escolas": escolas,
        "hoje": date.today(),
    })


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

    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        matricula = (request.POST.get("matricula") or "").strip()
        turma_id_post = request.POST.get("turma")
        responsavel = (request.POST.get("responsavel") or "").strip()
        telefone = (request.POST.get("telefone") or "").strip()

        if nome and turma_id_post:
            if not matricula:
                base_matricula = f"ALU-{date.today().strftime('%Y%m%d')}"
                sequencia = Aluno.objects.count() + 1
                matricula = f"{base_matricula}-{sequencia:04d}"
                while Aluno.objects.filter(matricula=matricula).exists():
                    sequencia += 1
                    matricula = f"{base_matricula}-{sequencia:04d}"

            aluno, criado = Aluno.objects.get_or_create(
                matricula=matricula,
                defaults={
                    "nome": nome,
                    "turma_id": turma_id_post,
                    "responsavel": responsavel or None,
                    "telefone": telefone or None,
                    "ativo": True,
                },
            )

            if not criado:
                aluno.nome = nome
                aluno.turma_id = turma_id_post
                aluno.responsavel = responsavel or None
                aluno.telefone = telefone or None
                aluno.ativo = True
                aluno.save()

            messages.success(request, "Aluno cadastrado/atualizado com sucesso.")
            return redirect("gestao_alunos")

        messages.error(request, "Informe pelo menos o nome do aluno e a turma.")
        return redirect("gestao_alunos")

    busca = request.GET.get("busca", "").strip()
    turma_id = request.GET.get("turma")

    alunos = Aluno.objects.filter(ativo=True).select_related("turma")

    if busca:
        alunos = alunos.filter(nome__icontains=busca)

    if turma_id:
        alunos = alunos.filter(turma_id=turma_id)

    regras = obter_regras_academicas()
    alunos_dados = []
    for aluno in alunos[:120]:
        indicadores = _indicadores_aluno(aluno)
        media = indicadores["media"]
        frequencia = indicadores["frequencia"]
        situacao = indicadores["situacao"]

        if situacao in {"Recuperação", "Frequência insuficiente"}:
            status = "Atenção"
            classe = "risk-high"
        elif (
            media is not None and media < float(regras.media_atencao)
        ) or (
            frequencia is not None and frequencia < min(100.0, float(regras.frequencia_minima) + 10.0)
        ):
            status = "Monitorar"
            classe = "risk-medium"
        elif situacao == "Sem notas":
            status = "Sem notas"
            classe = "risk-medium"
        else:
            status = "Estável"
            classe = "risk-low"

        alunos_dados.append({
            "aluno": aluno,
            "media": media,
            "faltas": indicadores["faltas"],
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
    regras = obter_regras_academicas()
    limite_frequencia_atencao = min(Decimal("100"), regras.frequencia_minima + Decimal("10"))
    for aluno in Aluno.objects.filter(ativo=True).select_related("turma"):
        notas = Nota.objects.filter(aluno=aluno).exclude(valor__isnull=True)
        media = _media_decimal([n.valor for n in notas])
        frequencia = _percentual_frequencia(aluno=aluno)
        motivos = []
        nivel = "INFO"
        if media is not None and media < regras.media_aprovacao:
            motivos.append(f"média abaixo da aprovação ({media})")
            nivel = "CRITICO"
        elif media is not None and media < regras.media_atencao:
            motivos.append(f"média em atenção ({media})")
            nivel = "ATENCAO"
        if Decimal(str(frequencia)) < regras.frequencia_minima:
            motivos.append(f"frequência abaixo do mínimo ({frequencia}%)")
            nivel = "CRITICO"
        elif Decimal(str(frequencia)) < limite_frequencia_atencao:
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
def gestao_mapa_recuperacao(request):
    """Mapa oficial de alunos em recuperação/atenção pedagógica."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turma_id = request.GET.get("turma")
    turmas = Turma.objects.all().prefetch_related("alunos")
    turma = turmas.filter(id=turma_id).first() if turma_id else turmas.first()
    linhas = []
    regras = obter_regras_academicas()
    if turma:
        for aluno in turma.alunos.filter(ativo=True):
            diag = _diagnostico_recuperacao(aluno)
            if diag["media"] < float(regras.media_aprovacao) or diag["faltas"] >= 10 or diag["disciplinas"]:
                linhas.append({"aluno": aluno, **diag})

    if request.method == "POST" and turma:
        DocumentoGerado.objects.create(
            tipo="RELATORIO",
            titulo=f"Mapa de recuperação • {turma.nome}",
            turma=turma,
            gerado_por=request.user,
            observacoes="Documento pedagógico de acompanhamento e recuperação.",
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


# =====================================================
# CHECKUP FINAL — Compatibilidade de links antigos/legados
# =====================================================


@login_required
def gestao_aluno_painel_integrado(request, aluno_id):
    return gestao_ficha_aluno_oficial(request, aluno_id)


@login_required
def gestao_cadastros(request):
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
                senha = request.POST.get("senha") or ""
                if username:
                    professor, criado = User.objects.get_or_create(username=username, defaults={"tipo": "PROF", "email": email})
                    professor.tipo = "PROF"
                    if nome:
                        partes = nome.split(" ", 1)
                        professor.first_name = partes[0]
                        professor.last_name = partes[1] if len(partes) > 1 else ""
                    if email:
                        professor.email = email
                    if criado and not senha:
                        raise ValueError("Defina uma senha inicial segura para o professor.")
                    if senha and (criado or request.POST.get("trocar_senha") == "on"):
                        from django.contrib.auth.password_validation import validate_password
                        validate_password(senha, user=professor)
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
        return redirect("gestao_cadastros")

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
    return render(request, "gestao/cadastros.html", context)



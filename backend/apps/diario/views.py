from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from datetime import date

from apps.academico.models import Turma

from .models import Diario

from .services import DiarioIAService


@login_required
def diario_home(request):

    diarios = Diario.objects.select_related("turma").order_by("-data", "-id")

    turmas = Turma.objects.prefetch_related("alunos").all()

    context = {

        "diarios": diarios,

        "turmas": turmas,

    }

    return render(
        request,
        "diario/home.html",
        context
    )


@login_required
def novo_diario(request):

    turmas = Turma.objects.all()

    turma_selecionada = request.GET.get("turma")

    if request.method == "POST":

        turma_id = request.POST.get("turma")

        titulo = request.POST.get("titulo")

        disciplina = request.POST.get("disciplina")

        data_aula = request.POST.get("data") or date.today()

        bimestre = request.POST.get("bimestre") or 1

        quantidade_aulas = request.POST.get("quantidade_aulas") or 1

        conteudo = request.POST.get("conteudo")

        objetivos = request.POST.get("objetivos")

        habilidades = request.POST.get("habilidades")

        metodologia = request.POST.get("metodologia")

        recursos = request.POST.get("recursos")

        avaliacao = request.POST.get("avaliacao")

        tarefa_casa = request.POST.get("tarefa_casa")

        observacoes = request.POST.get("observacoes")

        status = request.POST.get("status") or "CONCLUIDA"

        turma = get_object_or_404(
            Turma,
            id=turma_id
        )

        resumo_base = "\n\n".join(
            item for item in [
                titulo,
                conteudo,
                objetivos,
                habilidades,
                metodologia,
                avaliacao,
                observacoes,
            ]
            if item
        )

        resumo_ia = DiarioIAService.gerar_resumo(
            resumo_base or conteudo
        )

        Diario.objects.create(

            turma=turma,

            professor=request.user,

            data=data_aula,

            titulo=titulo,

            disciplina=disciplina,

            bimestre=bimestre,

            quantidade_aulas=quantidade_aulas,

            conteudo=conteudo,

            objetivos=objetivos,

            habilidades=habilidades,

            metodologia=metodologia,

            recursos=recursos,

            avaliacao=avaliacao,

            tarefa_casa=tarefa_casa,

            observacoes=observacoes,

            status=status,

            resumo_ia=resumo_ia,

        )

        messages.success(
            request,
            "Conteúdo de aula salvo com sucesso."
        )

        return redirect(
            "diario_home"
        )

    context = {

        "turmas": turmas,

        "turma_selecionada": turma_selecionada,

        "hoje": date.today(),

    }

    return render(
        request,
        "diario/novo.html",
        context
    )

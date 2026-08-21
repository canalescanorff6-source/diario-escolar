import csv

from django.http import HttpResponse

"""Views de relatórios, documentos e exportações."""

from .views_shared import *  # noqa: F401,F403

# =====================================================
# BOLETIM PREMIUM DO ALUNO
# =====================================================

@login_required
def boletim_aluno(request, aluno_id):

    if not (usuario_professor(request.user) or usuario_gestor(request.user)):
        return render(request, "core/acesso_negado.html")

    aluno = get_object_or_404(
        Aluno.objects.select_related("turma", "turma__ano_letivo"),
        id=aluno_id
    )

    turma = aluno.turma
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")

    disciplinas = Disciplina.objects.all().order_by("nome")

    regras = obter_regras_academicas()
    linhas = []
    soma_medias_anuais = Decimal("0")
    total_medias_anuais = 0
    total_faltas_geral = 0

    for disciplina in disciplinas:

        notas = {
            nota.bimestre: nota
            for nota in Nota.objects.filter(
                aluno=aluno,
                disciplina=disciplina
            )
        }

        periodos = []
        soma_periodos = Decimal("0")
        total_periodos = 0
        faltas_disciplina = Frequencia.objects.filter(
            aluno=aluno,
            disciplina=disciplina,
            presente=False
        ).count()

        total_faltas_geral += faltas_disciplina

        for numero in [1, 2, 3, 4]:
            nota = notas.get(numero)
            media = nota.valor if nota and nota.valor is not None else None

            if media is not None:
                soma_periodos += media
                total_periodos += 1

            periodos.append({
                "numero": numero,
                "media": media,
                "faltas": faltas_disciplina if numero == 1 else "",
            })

        media_anual = None
        media_final = None
        status = "Pendente"
        status_classe = "status-pendente"

        if total_periodos > 0:
            media_anual = round(soma_periodos / total_periodos, 2)
            media_final = media_anual
            soma_medias_anuais += media_anual
            total_medias_anuais += 1

            situacao = classificar_situacao(media_anual, None, tem_notas=True, tem_frequencia=False)
            if situacao == "Aprovado":
                status = "Aprovado"
                status_classe = "status-aprovado"
            elif media_anual < regras.media_aprovacao:
                status = "Recuperação"
                status_classe = "status-atencao"
            else:
                status = "Atenção"
                status_classe = "status-atencao"

        if notas or faltas_disciplina:
            linhas.append({
                "disciplina": disciplina,
                "periodos": periodos,
                "media_anual": media_anual,
                "recuperacao": "",
                "media_final": media_final,
                "faltas": faltas_disciplina,
                "status": status,
                "status_classe": status_classe,
            })

    media_geral = None
    if total_medias_anuais > 0:
        media_geral = round(soma_medias_anuais / total_medias_anuais, 2)

    context = {
        "aluno": aluno,
        "turma": turma,
        "linhas": linhas,
        "media_geral": media_geral,
        "total_faltas_geral": total_faltas_geral,
        "ano_letivo": turma.ano_letivo if turma else None,
        "hoje": date.today(),
    }

    return render(
        request,
        "core/boletim_aluno.html",
        context
    )


# =====================================================
# BOLETIM TURMA
# =====================================================

@login_required
def boletim_ia(request, turma_id):
    """Análise pedagógica da turma, visível somente para usuários autorizados."""
    if not (usuario_professor(request.user) or usuario_gestor(request.user)):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(Turma, id=turma_id)
    if not _usuario_pode_ver_turma(request.user, turma):
        return render(request, "core/acesso_negado.html")

    return render(request, "core/analise_turma.html", {
        "turma": turma,
        "resumo": AnaliseInteligenteService.resumo_turma(turma),
        "alunos_risco": AnaliseInteligenteService.alunos_em_risco(turma),
    })


# =====================================================
# GESTÃO ESCOLAR — PÁGINAS ADMINISTRATIVAS FUNCIONAIS
# =====================================================


@login_required
def gestao_relatorios(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.all().prefetch_related("alunos")
    alunos = Aluno.objects.filter(ativo=True).select_related("turma")

    context = {
        "hoje": date.today(),
        "escola": Escola.objects.filter(ativa=True).first(),
        "turmas": turmas,
        "alunos": alunos[:80],
        "total_turmas": turmas.count(),
        "total_alunos": alunos.count(),
        "total_diarios": Diario.objects.count(),
        "total_conteudos": ConteudoAula.objects.count(),
    }

    return render(request, "gestao/relatorios.html", context)


@login_required
def gestao_documentos(request):

    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    if request.method == "POST":
        tipo = request.POST.get("tipo") or "OUTRO"
        titulo = request.POST.get("titulo")
        turma_id = request.POST.get("turma") or None
        aluno_id = request.POST.get("aluno") or None
        observacoes = request.POST.get("observacoes")

        if titulo:
            documento = DocumentoGerado.objects.create(
                tipo=tipo,
                titulo=titulo,
                turma_id=turma_id,
                aluno_id=aluno_id,
                observacoes=observacoes,
                gerado_por=request.user,
            )
            registrar_auditoria(request.user, "Documentos", "Registro de documento", objeto=documento.titulo)
            messages.success(request, "Documento registrado com sucesso.")
            return redirect("gestao_documentos")

    context = {
        "documentos": DocumentoGerado.objects.select_related("turma", "aluno", "gerado_por")[:120],
        "turmas": Turma.objects.all(),
        "alunos": Aluno.objects.filter(ativo=True).select_related("turma"),
        "tipos": DocumentoGerado.TIPOS,
        "status_opcoes": DocumentoGerado.STATUS,
        "hoje": date.today(),
    }

    return render(request, "gestao/documentos.html", context)


@login_required
def gestao_documento_boletim_oficial(request, aluno_id):
    """Boletim oficial imprimível inspirado no boletim real enviado como referência."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    escola = Escola.objects.filter(ativa=True).first()
    notas = Nota.objects.filter(aluno=aluno).select_related("disciplina", "turma").order_by("disciplina__nome", "bimestre")
    disciplinas = Disciplina.objects.filter(id__in=notas.values_list("disciplina_id", flat=True)).order_by("nome")

    regras = obter_regras_academicas()
    linhas = []
    for disciplina in disciplinas:
        notas_disciplina = notas.filter(disciplina=disciplina)
        periodos = []
        medias_periodo = []
        faltas_total = 0
        for numero in [1, 2, 3, 4]:
            nota = notas_disciplina.filter(bimestre=numero).first()
            media = nota.valor if nota else None
            medias_periodo.append(media)
            faltas = Frequencia.objects.filter(aluno=aluno, disciplina=disciplina, presente=False).count()
            faltas_total = faltas
            periodos.append({"numero": numero, "nota": nota, "media": media, "faltas": faltas})
        media_anual = _media_decimal(medias_periodo)
        precisa_recuperacao = media_anual is not None and media_anual < regras.media_aprovacao
        linhas.append({
            "disciplina": disciplina,
            "periodos": periodos,
            "media_anual": media_anual,
            "recuperacao": "Sim" if precisa_recuperacao else "Não",
            "media_final": media_anual,
            "faltas": faltas_total,
        })

    medias_gerais = [linha["media_anual"] for linha in linhas if linha["media_anual"] is not None]
    media_geral = _media_decimal(medias_gerais)
    faltas_gerais = Frequencia.objects.filter(aluno=aluno, presente=False).count()
    frequencia = _percentual_frequencia(aluno=aluno)

    DocumentoGerado.objects.get_or_create(
        tipo="BOLETIM",
        titulo=f"Boletim oficial • {aluno.nome}",
        aluno=aluno,
        turma=aluno.turma,
        defaults={"gerado_por": request.user, "observacoes": "Gerado pela exportação oficial do sistema."},
    )
    registrar_auditoria(request.user, "Documentos oficiais", "Boletim oficial gerado", objeto=aluno.nome)

    context = {
        "escola": escola,
        "aluno": aluno,
        "turma": aluno.turma,
        "ano_letivo": getattr(aluno.turma, "ano_letivo", None),
        "linhas": linhas,
        "media_geral": media_geral,
        "faltas_gerais": faltas_gerais,
        "frequencia": frequencia,
        "protocolo": _protocolo_documento("BOL", aluno.id),
        "hoje": date.today(),
    }
    return render(request, "gestao/documento_boletim_oficial.html", context)


@login_required
def gestao_documento_diario_oficial(request, turma_id):
    """Diário oficial imprimível para secretaria/gestão sem alterar o diário do professor."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turma = get_object_or_404(Turma.objects.select_related("ano_letivo", "professor"), id=turma_id)
    escola = Escola.objects.filter(ativa=True).first()
    alunos = turma.alunos.filter(ativo=True).order_by("nome")
    disciplinas = Disciplina.objects.filter(
        id__in=ProfessorTurmaDisciplina.objects.filter(turma=turma, ativo=True).values_list("disciplina_id", flat=True)
    ).distinct().order_by("nome")
    if not disciplinas.exists():
        disciplinas = Disciplina.objects.all().order_by("nome")[:8]

    horarios = HorarioAula.objects.filter(turma=turma, ativo=True).select_related("disciplina", "professor").order_by("dia_semana", "ordem")
    conteudos = ConteudoAula.objects.filter(turma=turma).select_related("disciplina", "professor").order_by("data", "disciplina__nome")[:160]
    frequencias = Frequencia.objects.filter(turma=turma).select_related("aluno", "disciplina")

    alunos_linhas = []
    for aluno in alunos:
        total = frequencias.filter(aluno=aluno).count()
        faltas = frequencias.filter(aluno=aluno, presente=False).count()
        alunos_linhas.append({
            "aluno": aluno,
            "faltas": faltas,
            "frequencia": round(((total - faltas) / total) * 100, 1) if total else 100,
        })

    DocumentoGerado.objects.get_or_create(
        tipo="DIARIO",
        titulo=f"Diário oficial • {turma.nome}",
        turma=turma,
        defaults={"gerado_por": request.user, "observacoes": "Gerado pela exportação oficial do sistema."},
    )
    registrar_auditoria(request.user, "Documentos oficiais", "Diário oficial gerado", objeto=turma.nome)

    context = {
        "escola": escola,
        "turma": turma,
        "ano_letivo": turma.ano_letivo,
        "professor": turma.professor,
        "alunos_linhas": alunos_linhas,
        "disciplinas": disciplinas,
        "horarios": horarios,
        "conteudos": conteudos,
        "frequencia_turma": _percentual_frequencia(turma=turma),
        "protocolo": _protocolo_documento("DIA", turma.id),
        "hoje": date.today(),
    }
    return render(request, "gestao/documento_diario_oficial.html", context)


@login_required
def gestao_relatorio_executivo_oficial(request):
    """Relatório executivo imprimível com indicadores reais do projeto."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas = Turma.objects.all().prefetch_related("alunos")
    alunos = Aluno.objects.filter(ativo=True).select_related("turma")
    professores = get_user_model().objects.filter(tipo="PROF")
    total_freq = Frequencia.objects.count()
    faltas = Frequencia.objects.filter(presente=False).count()
    frequencia_geral = round(((total_freq - faltas) / total_freq) * 100, 1) if total_freq else 100

    medias = [n.valor for n in Nota.objects.exclude(valor__isnull=True)]
    media_geral = _media_decimal(medias)

    turmas_linhas = []
    for turma in turmas:
        qs_freq = Frequencia.objects.filter(turma=turma)
        total_turma = qs_freq.count()
        faltas_turma = qs_freq.filter(presente=False).count()
        notas_turma = Nota.objects.filter(turma=turma).exclude(valor__isnull=True)
        turmas_linhas.append({
            "turma": turma,
            "alunos": turma.alunos.filter(ativo=True).count(),
            "frequencia": round(((total_turma - faltas_turma) / total_turma) * 100, 1) if total_turma else 100,
            "media": _media_decimal([n.valor for n in notas_turma]),
            "faltas": faltas_turma,
            "conteudos": ConteudoAula.objects.filter(turma=turma).count(),
        })

    registrar_auditoria(request.user, "Relatórios", "Relatório executivo oficial gerado", objeto="Gestão")

    context = {
        "escola": Escola.objects.filter(ativa=True).first(),
        "hoje": date.today(),
        "protocolo": _protocolo_documento("REL", request.user.id),
        "total_turmas": turmas.count(),
        "total_alunos": alunos.count(),
        "total_professores": professores.count(),
        "total_conteudos": ConteudoAula.objects.count(),
        "frequencia_geral": frequencia_geral,
        "media_geral": media_geral,
        "notificacoes_pendentes": NotificacaoGestao.objects.filter(resolvida=False).count(),
        "documentos": DocumentoGerado.objects.count(),
        "turmas_linhas": turmas_linhas,
    }
    return render(request, "gestao/relatorio_executivo_oficial.html", context)


@login_required
def gestao_documento_declaracao_matricula(request, aluno_id):
    """Declaração de matrícula imprimível, aproveitando os cadastros já existentes."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    aluno = get_object_or_404(Aluno.objects.select_related("turma", "turma__ano_letivo"), id=aluno_id)
    escola = Escola.objects.filter(ativa=True).first()
    protocolo = _protocolo_documento("DECL", aluno.id)

    DocumentoGerado.objects.get_or_create(
        tipo="OUTRO",
        titulo=f"Declaração de matrícula • {aluno.nome}",
        aluno=aluno,
        turma=aluno.turma,
        defaults={"gerado_por": request.user, "observacoes": f"Protocolo {protocolo}"},
    )
    registrar_auditoria(request.user, "Documentos oficiais", "Declaração de matrícula gerada", objeto=aluno.nome, descricao=protocolo)

    return render(request, "gestao/declaracao_matricula.html", {
        "hoje": date.today(),
        "aluno": aluno,
        "escola": escola,
        "protocolo": protocolo,
    })


@login_required
def professor_relatorios(request):
    if not usuario_professor(request.user):
        return render(request, "core/acesso_negado.html")

    turmas_qs = _turmas_do_professor(request.user).prefetch_related("alunos")
    alunos = Aluno.objects.filter(turma__in=turmas_qs, ativo=True)
    conteudos = ConteudoAula.objects.filter(professor=request.user, turma__in=turmas_qs)
    faltas = Frequencia.objects.filter(turma__in=turmas_qs, presente=False)

    return render(request, "core/professor_relatorios.html", {
        "hoje": date.today(),
        "turmas": turmas_qs,
        "total_turmas": turmas_qs.count(),
        "total_alunos": alunos.count(),
        "total_conteudos": conteudos.count(),
        "total_faltas": faltas.count(),
    })


# =====================================================
# EXPORTAÇÃO GERAL — GESTÃO E PROFESSOR
# Saída oficial em Excel (.xlsx) e PDF sem importação por planilha.
# =====================================================

from django.http import HttpResponse
from xml.sax.saxutils import escape as _xml_escape
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO

try:
    from apps.academico.models import FechamentoMensal
except Exception:  # compatibilidade com bancos antigos sem a migration aplicada
    FechamentoMensal = None


def _export_value(value):
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d/%m/%Y")
        except Exception:
            pass
    return str(value)


def _safe_sheet_name(name):
    cleaned = str(name or "Planilha")
    for ch in '[]:*?/\\':
        cleaned = cleaned.replace(ch, ' ')
    return cleaned.strip()[:31] or "Planilha"


def _xlsx_bytes(sheets):
    """Gera um arquivo .xlsx simples usando apenas biblioteca padrão."""
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
''' + "".join([f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>\n' for i in range(1, len(sheets)+1)]) + "</Types>")
        z.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''')
        workbook_sheets = []
        workbook_rels = []
        for idx, (sheet_name, rows) in enumerate(sheets, start=1):
            safe_name = _safe_sheet_name(sheet_name)
            workbook_sheets.append(f'<sheet name="{_xml_escape(safe_name)}" sheetId="{idx}" r:id="rId{idx}"/>')
            workbook_rels.append(f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>')
            sheet_rows = []
            for r_idx, row in enumerate(rows or [["Sem dados cadastrados"]], start=1):
                cells = []
                for c_idx, value in enumerate(row, start=1):
                    n = c_idx
                    col = ""
                    while n:
                        n, rem = divmod(n - 1, 26)
                        col = chr(65 + rem) + col
                    val = _xml_escape(_export_value(value))
                    cells.append(f'<c r="{col}{r_idx}" t="inlineStr"><is><t>{val}</t></is></c>')
                sheet_rows.append(f'<row r="{r_idx}">' + "".join(cells) + "</row>")
            z.writestr(f"xl/worksheets/sheet{idx}.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>''' + "".join(sheet_rows) + "</sheetData></worksheet>")
        z.writestr("xl/workbook.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>''' + "".join(workbook_sheets) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">''' + "".join(workbook_rels) + '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs></styleSheet>''')
    return output.getvalue()


def _pdf_escape(text):
    return _export_value(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_bytes(title, sections):
    lines = [title, "Gerado pelo Diário Escolar Pro", ""]
    for section_title, rows in sections:
        lines.append(section_title)
        if not rows or len(rows) == 1:
            lines.append("  Sem dados cadastrados")
        else:
            headers = rows[0]
            for row in rows[1:80]:
                pairs = []
                for h, v in zip(headers, row):
                    value = _export_value(v)
                    if len(value) > 42:
                        value = value[:39] + "..."
                    pairs.append(f"{h}: {value}")
                line = " | ".join(pairs)
                while len(line) > 108:
                    lines.append("  " + line[:108])
                    line = line[108:]
                lines.append("  " + line)
        lines.append("")

    per_page = 46
    pages = [lines[i:i+per_page] for i in range(0, len(lines), per_page)] or [[title]]
    objects = []
    page_refs = []
    font_obj_number = 3 + len(pages) * 2
    for page_index, page_lines in enumerate(pages):
        page_obj_number = 3 + page_index * 2
        content_obj_number = page_obj_number + 1
        page_refs.append(f"{page_obj_number} 0 R")
        text_ops = ["BT", "/F1 9 Tf", "12 TL", "50 790 Td"]
        for line in page_lines:
            text_ops.append(f"({_pdf_escape(line)}) Tj")
            text_ops.append("T*")
        text_ops.append("ET")
        stream = "\n".join(text_ops).encode("latin-1", errors="replace")
        objects.append((page_obj_number, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_obj_number} 0 R >> >> /Contents {content_obj_number} 0 R >>".encode()))
        objects.append((content_obj_number, b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"))
    objects.insert(0, (1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    objects.insert(1, (2, f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {len(pages)} >>".encode()))
    objects.append((font_obj_number, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))
    objects.sort(key=lambda item: item[0])
    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for num, obj in objects:
        offsets[num] = pdf.tell()
        pdf.write(f"{num} 0 obj\n".encode())
        pdf.write(obj)
        pdf.write(b"\nendobj\n")
    xref_pos = pdf.tell()
    max_obj = max(offsets)
    pdf.write(f"xref\n0 {max_obj+1}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for i in range(1, max_obj + 1):
        pdf.write(f"{offsets.get(i, 0):010d} 00000 n \n".encode())
    pdf.write(f"trailer\n<< /Size {max_obj+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return pdf.getvalue()


def _xlsx_response(filename, sheets):
    response = HttpResponse(_xlsx_bytes(sheets), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response


def _pdf_response(filename, title, sections):
    response = HttpResponse(_pdf_bytes(title, sections), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response


def _gestao_export_sheets():
    User = get_user_model()
    gestores = User.objects.filter(tipo__in=["ADMIN", "COORD", "SEC"]).order_by("username")
    professores = User.objects.filter(tipo="PROF").order_by("username")
    sheets = []
    sheets.append(("Escola", [["Nome", "Aldeia", "Terra indígena", "Gestão", "Secretaria"]] + [[e.nome, e.aldeia, e.terra_indigena, e.gestor_nome, e.secretaria] for e in Escola.objects.all()]))
    sheets.append(("Gestores", [["Usuário", "Nome", "Tipo", "Ativo"]] + [[u.username, u.get_full_name(), u.get_tipo_display(), "Sim" if u.is_active else "Não"] for u in gestores]))
    sheets.append(("Professores", [["Usuário", "Nome", "E-mail", "Ativo"]] + [[u.username, u.get_full_name(), u.email, "Sim" if u.is_active else "Não"] for u in professores]))
    sheets.append(("Alunos", [["Nome", "Matrícula", "Turma", "Responsável", "Telefone"]] + [[a.nome, a.matricula, a.turma.nome if a.turma_id else "", a.responsavel, a.telefone] for a in Aluno.objects.select_related("turma").order_by("nome")[:5000]]))
    sheets.append(("Turmas", [["Turma", "Ano letivo", "Turno", "Sala", "Alunos"]] + [[t.nome, t.ano_letivo.ano if t.ano_letivo_id else "", t.turno, t.sala, t.alunos.count()] for t in Turma.objects.select_related("ano_letivo").prefetch_related("alunos").order_by("nome")]))
    sheets.append(("Disciplinas", [["Nome", "Cor"]] + [[d.nome, d.cor] for d in Disciplina.objects.order_by("nome")]))
    sheets.append(("Vinculos", [["Professor", "Turma", "Disciplina", "Ano letivo", "Ativo"]] + [[v.professor.get_full_name() or v.professor.username, v.turma.nome, v.disciplina.nome, v.ano_letivo.ano if v.ano_letivo_id else "", "Sim" if v.ativo else "Não"] for v in ProfessorTurmaDisciplina.objects.select_related("professor", "turma", "disciplina", "ano_letivo")]))
    sheets.append(("Horarios", [["Professor", "Turma", "Disciplina", "Dia", "Início", "Fim", "Turno"]] + [[h.professor.get_full_name() or h.professor.username, h.turma.nome, h.disciplina.nome, h.get_dia_semana_display(), h.hora_inicio, h.hora_fim, h.turno] for h in HorarioAula.objects.select_related("professor", "turma", "disciplina").order_by("dia_semana", "hora_inicio")]))
    sheets.append(("Frequencias", [["Aluno", "Turma", "Disciplina", "Data", "Status", "Observação"]] + [[f.aluno.nome, f.turma.nome if f.turma_id else "", f.disciplina.nome, f.data, f.status, f.observacao] for f in Frequencia.objects.select_related("aluno", "turma", "disciplina").order_by("-data")[:5000]]))
    sheets.append(("Aulas", [["Data", "Professor", "Turma", "Disciplina", "Conteúdo", "Observações"]] + [[c.data, c.professor.get_full_name() or c.professor.username, c.turma.nome, c.disciplina.nome, c.descricao, c.observacoes] for c in ConteudoAula.objects.select_related("professor", "turma", "disciplina").order_by("-data")[:5000]]))
    if FechamentoMensal:
        sheets.append(("Fechamento", [["Mês", "Ano", "Professor", "Turma", "Disciplina", "Status", "Aulas dadas", "Frequências"]] + [[f.mes, f.ano, f.professor.get_full_name() or f.professor.username, f.turma.nome, f.disciplina.nome, f.status, f.aulas_dadas, f.frequencias_lancadas] for f in FechamentoMensal.objects.select_related("professor", "turma", "disciplina").order_by("-ano", "-mes")]))
    return sheets


def _professor_export_sheets(user):
    vinculos = ProfessorTurmaDisciplina.objects.filter(professor=user, ativo=True).select_related("turma", "disciplina", "ano_letivo")
    turmas_ids = list(vinculos.values_list("turma_id", flat=True))
    disciplinas_ids = list(vinculos.values_list("disciplina_id", flat=True))
    sheets = []
    sheets.append(("Minhas turmas", [["Turma", "Ano letivo", "Turno", "Alunos"]] + [[t.nome, t.ano_letivo.ano if t.ano_letivo_id else "", t.turno, t.alunos.count()] for t in Turma.objects.filter(id__in=turmas_ids).select_related("ano_letivo").prefetch_related("alunos")]))
    sheets.append(("Disciplinas", [["Turma", "Disciplina", "Ano letivo"]] + [[v.turma.nome, v.disciplina.nome, v.ano_letivo.ano if v.ano_letivo_id else ""] for v in vinculos]))
    sheets.append(("Horarios", [["Turma", "Disciplina", "Dia", "Início", "Fim", "Turno"]] + [[h.turma.nome, h.disciplina.nome, h.get_dia_semana_display(), h.hora_inicio, h.hora_fim, h.turno] for h in HorarioAula.objects.filter(professor=user, ativo=True).select_related("turma", "disciplina").order_by("dia_semana", "hora_inicio")]))
    sheets.append(("Frequencias", [["Aluno", "Turma", "Disciplina", "Data", "Status", "Observação"]] + [[f.aluno.nome, f.turma.nome if f.turma_id else "", f.disciplina.nome, f.data, f.status, f.observacao] for f in Frequencia.objects.filter(turma_id__in=turmas_ids, disciplina_id__in=disciplinas_ids).select_related("aluno", "turma", "disciplina").order_by("-data")[:5000]]))
    sheets.append(("Aulas", [["Data", "Turma", "Disciplina", "Conteúdo", "Observações"]] + [[c.data, c.turma.nome, c.disciplina.nome, c.descricao, c.observacoes] for c in ConteudoAula.objects.filter(professor=user).select_related("turma", "disciplina").order_by("-data")[:5000]]))
    if FechamentoMensal:
        sheets.append(("Fechamento", [["Mês", "Ano", "Turma", "Disciplina", "Status", "Aulas dadas", "Frequências"]] + [[f.mes, f.ano, f.turma.nome, f.disciplina.nome, f.status, f.aulas_dadas, f.frequencias_lancadas] for f in FechamentoMensal.objects.filter(professor=user).select_related("turma", "disciplina")]))
    return sheets


@login_required
def gestao_exportar_geral_excel(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    registrar_auditoria(request.user, "Exportações", "Exportação geral Excel")
    return _xlsx_response("diario_gestao_exportacao_geral", _gestao_export_sheets())


@login_required
def gestao_exportar_geral_pdf(request):
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")
    registrar_auditoria(request.user, "Exportações", "Exportação geral PDF")
    return _pdf_response("diario_gestao_exportacao_geral", "Exportação geral da gestão", _gestao_export_sheets())


@login_required
def professor_exportar_geral_excel(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    return _xlsx_response("diario_professor_exportacao_geral", _professor_export_sheets(request.user))


@login_required
def professor_exportar_geral_pdf(request):
    if not usuario_professor(request.user):
        return redirect("dashboard_gestao") if usuario_gestor(request.user) else render(request, "core/acesso_negado.html")
    return _pdf_response("diario_professor_exportacao_geral", "Exportação geral do professor", _professor_export_sheets(request.user))


@login_required
def gestao_auditoria_exportacao(request):
    """Exporta a trilha de auditoria em CSV UTF-8 para a gestão escolar."""
    if not usuario_gestor(request.user):
        return render(request, "core/acesso_negado.html")

    modulo = (request.GET.get("modulo") or "").strip()
    auditorias = AuditoriaSistema.objects.select_related("usuario").all()
    if modulo:
        auditorias = auditorias.filter(modulo__icontains=modulo)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="auditoria-diario-escolar.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Data/hora", "Usuário", "Módulo", "Ação", "Objeto", "Descrição"])
    for item in auditorias.iterator(chunk_size=500):
        usuario = "Sistema"
        if item.usuario_id:
            usuario = item.usuario.get_full_name() or item.usuario.username
        writer.writerow([
            timezone.localtime(item.criado_em).strftime("%d/%m/%Y %H:%M:%S"),
            usuario,
            item.modulo,
            item.acao,
            item.objeto or "",
            item.descricao or "",
        ])

    registrar_auditoria(
        request.user,
        "Auditoria",
        "Trilha de auditoria exportada",
        descricao=f"Filtro de módulo: {modulo or 'todos'}",
    )
    return response

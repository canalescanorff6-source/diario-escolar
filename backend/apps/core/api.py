import json
from datetime import date, datetime
from functools import wraps

from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.academico.models import (
    Aluno,
    ConteudoAula,
    Frequencia,
    HorarioAula,
    ProfessorTurmaDisciplina,
    Turma,
)
from apps.usuarios.models import ApiToken


def _json_body(request):
    try:
        return json.loads((request.body or b"{}").decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError):
        return None


def _error(message, status=400, code="invalid_request"):
    return JsonResponse({"ok": False, "error": code, "message": message}, status=status)


def _login_rate_key(username):
    import hashlib
    normalized = (username or "").strip().lower().encode("utf-8")
    return "mobile-login:" + hashlib.sha256(normalized).hexdigest()


def _login_rate_limited(username):
    key = _login_rate_key(username)
    attempts = int(cache.get(key, 0) or 0)
    limit = max(int(getattr(settings, "MOBILE_LOGIN_MAX_ATTEMPTS", 10)), 1)
    return attempts >= limit


def _record_login_failure(username):
    key = _login_rate_key(username)
    window = max(int(getattr(settings, "MOBILE_LOGIN_WINDOW_SECONDS", 300)), 60)
    try:
        cache.add(key, 0, timeout=window)
        cache.incr(key)
        cache.touch(key, timeout=window)
    except Exception:
        # Falha de cache não pode derrubar o login; autenticação continua protegida
        # pelas credenciais do Django e pelos controles do provedor/servidor.
        pass


def _clear_login_failures(username):
    try:
        cache.delete(_login_rate_key(username))
    except Exception:
        pass


def _bearer_token(request):
    value = request.headers.get("Authorization", "")
    if not value.lower().startswith("bearer "):
        return ""
    return value.split(" ", 1)[1].strip()


def api_auth_required(professor_only=False):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            token = ApiToken.autenticar(_bearer_token(request))
            if not token:
                return _error("Sessão inválida ou expirada.", 401, "unauthorized")
            request.api_token = token
            request.api_user = token.usuario
            if professor_only and token.usuario.tipo != "PROF":
                return _error("Esta operação é exclusiva para professores.", 403, "forbidden")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _serialize_horario(horario):
    return {
        "id": horario.id,
        "dia_semana": horario.dia_semana,
        "dia_semana_label": horario.get_dia_semana_display(),
        "ordem": horario.ordem,
        "hora_inicio": horario.hora_inicio.strftime("%H:%M") if horario.hora_inicio else None,
        "hora_fim": horario.hora_fim.strftime("%H:%M") if horario.hora_fim else None,
        "turno": horario.turno,
        "turma": {"id": horario.turma_id, "nome": horario.turma.nome},
        "disciplina": {"id": horario.disciplina_id, "nome": horario.disciplina.nome},
    }


def _professor_tem_vinculo(professor, turma_id, disciplina_id):
    return ProfessorTurmaDisciplina.objects.filter(
        professor=professor,
        turma_id=turma_id,
        disciplina_id=disciplina_id,
        ativo=True,
    ).exists()


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    payload = _json_body(request)
    if payload is None:
        return _error("JSON inválido.")
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return _error("Informe usuário e senha.")
    if _login_rate_limited(username):
        return _error("Muitas tentativas de acesso. Aguarde alguns minutos e tente novamente.", 429, "rate_limited")

    usuario = authenticate(request, username=username, password=password)
    if not usuario or not usuario.is_active:
        _record_login_failure(username)
        return _error("Usuário ou senha inválidos.", 401, "invalid_credentials")
    _clear_login_failures(username)
    if usuario.tipo != "PROF":
        return _error(
            "O aplicativo móvel desta versão é exclusivo para professores.",
            403,
            "professor_only",
        )

    # Limita a quantidade de sessões móveis ativas por usuário.
    ativos = usuario.api_tokens.filter(revogado=False, expira_em__gt=timezone.now()).order_by("-criado_em")
    for antigo in ativos[5:]:
        antigo.revogado = True
        antigo.save(update_fields=["revogado"])

    token, bruto = ApiToken.emitir(usuario, dias=30)
    return JsonResponse({
        "ok": True,
        "token": bruto,
        "expires_at": token.expira_em.isoformat(),
        "user": {
            "id": usuario.id,
            "username": usuario.username,
            "name": usuario.get_full_name() or usuario.username,
            "type": usuario.tipo,
        },
    })


@csrf_exempt
@require_http_methods(["POST"])
@api_auth_required()
def api_logout(request):
    request.api_token.revogado = True
    request.api_token.save(update_fields=["revogado"])
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
@api_auth_required()
def api_me(request):
    usuario = request.api_user
    return JsonResponse({
        "ok": True,
        "user": {
            "id": usuario.id,
            "username": usuario.username,
            "name": usuario.get_full_name() or usuario.username,
            "email": usuario.email,
            "type": usuario.tipo,
        },
    })


@require_http_methods(["GET"])
@api_auth_required(professor_only=True)
def api_professor_aulas_hoje(request):
    professor = request.api_user
    hoje = timezone.localdate()
    # Python weekday: segunda=0. Modelo: segunda=1.
    dia = hoje.weekday() + 1
    horarios = HorarioAula.objects.select_related("turma", "disciplina").filter(
        professor=professor,
        ativo=True,
        dia_semana=dia,
    ).order_by("ordem", "hora_inicio")
    return JsonResponse({
        "ok": True,
        "date": hoje.isoformat(),
        "items": [_serialize_horario(item) for item in horarios],
    })


@require_http_methods(["GET"])
@api_auth_required(professor_only=True)
def api_professor_turmas(request):
    professor = request.api_user
    vinculos = ProfessorTurmaDisciplina.objects.select_related("turma", "disciplina", "turma__ano_letivo").filter(
        professor=professor,
        ativo=True,
        turma__ativa=True,
    ).order_by("turma__nome", "disciplina__nome")
    grupos = {}
    for vinculo in vinculos:
        item = grupos.setdefault(vinculo.turma_id, {
            "id": vinculo.turma_id,
            "nome": vinculo.turma.nome,
            "turno": vinculo.turma.turno,
            "ano_letivo": vinculo.turma.ano_letivo.ano if vinculo.turma.ano_letivo_id else None,
            "disciplinas": [],
        })
        item["disciplinas"].append({"id": vinculo.disciplina_id, "nome": vinculo.disciplina.nome})
    return JsonResponse({"ok": True, "items": list(grupos.values())})


@require_http_methods(["GET"])
@api_auth_required(professor_only=True)
def api_professor_turma_alunos(request, turma_id):
    professor = request.api_user
    if not ProfessorTurmaDisciplina.objects.filter(professor=professor, turma_id=turma_id, ativo=True).exists():
        return _error("Turma não vinculada a este professor.", 403, "forbidden")
    turma = Turma.objects.filter(id=turma_id, ativa=True).first()
    if not turma:
        return _error("Turma não encontrada.", 404, "not_found")
    alunos = Aluno.objects.filter(turma=turma, ativo=True).order_by("nome")
    return JsonResponse({
        "ok": True,
        "turma": {"id": turma.id, "nome": turma.nome},
        "items": [{"id": a.id, "nome": a.nome, "matricula": a.matricula} for a in alunos],
    })


@csrf_exempt
@require_http_methods(["POST"])
@api_auth_required(professor_only=True)
def api_professor_registrar_aula(request):
    professor = request.api_user
    payload = _json_body(request)
    if payload is None:
        return _error("JSON inválido.")

    try:
        turma_id = int(payload.get("turma_id"))
        disciplina_id = int(payload.get("disciplina_id"))
    except (TypeError, ValueError):
        return _error("Turma e disciplina são obrigatórias.")

    if not _professor_tem_vinculo(professor, turma_id, disciplina_id):
        return _error("Turma ou disciplina não vinculada a este professor.", 403, "forbidden")

    horario = None
    horario_id = payload.get("horario_id")
    if horario_id:
        horario = HorarioAula.objects.filter(
            id=horario_id,
            professor=professor,
            turma_id=turma_id,
            disciplina_id=disciplina_id,
            ativo=True,
        ).first()
        if not horario:
            return _error("Horário inválido para este vínculo.", 400, "invalid_schedule")

    try:
        data_aula = datetime.strptime(payload.get("data") or date.today().isoformat(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return _error("Data inválida. Use AAAA-MM-DD.")

    try:
        aula_numero = int(payload.get("aula_numero") or (horario.ordem if horario else 1))
        aula_numero = max(1, min(20, aula_numero))
        quantidade_aulas = max(1, min(10, int(payload.get("quantidade_aulas") or 1)))
    except (TypeError, ValueError):
        return _error("Número/quantidade de aulas inválido.")

    descricao = (payload.get("conteudo") or "").strip()
    observacoes = (payload.get("observacoes") or "").strip()
    frequencias = payload.get("frequencias") or []
    if not isinstance(frequencias, list):
        return _error("O campo frequencias deve ser uma lista.")

    alunos_validos = set(Aluno.objects.filter(turma_id=turma_id, ativo=True).values_list("id", flat=True))
    registros = []
    for item in frequencias:
        try:
            aluno_id = int(item.get("aluno_id"))
        except (AttributeError, TypeError, ValueError):
            return _error("Há um aluno inválido na chamada.")
        if aluno_id not in alunos_validos:
            return _error("A chamada contém aluno que não pertence à turma.", 400, "invalid_student")
        status = (item.get("status") or "P").upper()
        if status not in {"P", "F", "FJ"}:
            return _error("Status de frequência inválido. Use P, F ou FJ.")
        registros.append((aluno_id, status, (item.get("observacao") or "").strip()))

    with transaction.atomic():
        for aluno_id, status, observacao in registros:
            Frequencia.objects.update_or_create(
                aluno_id=aluno_id,
                disciplina_id=disciplina_id,
                data=data_aula,
                aula_numero=aula_numero,
                defaults={
                    "turma_id": turma_id,
                    "status": status,
                    "observacao": observacao,
                },
            )
        if descricao:
            ConteudoAula.objects.update_or_create(
                professor=professor,
                turma_id=turma_id,
                disciplina_id=disciplina_id,
                data=data_aula,
                aula_numero=aula_numero,
                defaults={
                    "descricao": descricao,
                    "observacoes": observacoes,
                    "quantidade_aulas": quantidade_aulas,
                },
            )

    return JsonResponse({
        "ok": True,
        "saved": {
            "frequencias": len(registros),
            "conteudo": bool(descricao),
            "date": data_aula.isoformat(),
            "aula_numero": aula_numero,
        },
    })


@require_http_methods(["GET"])
@api_auth_required(professor_only=True)
def api_professor_bootstrap(request):
    professor = request.api_user
    hoje = timezone.localdate()
    vinculos = ProfessorTurmaDisciplina.objects.select_related("turma", "disciplina").filter(
        professor=professor, ativo=True, turma__ativa=True
    ).order_by("turma__nome", "disciplina__nome")
    horarios = HorarioAula.objects.select_related("turma", "disciplina").filter(
        professor=professor, ativo=True
    ).order_by("dia_semana", "ordem", "hora_inicio")
    turmas_ids = list(vinculos.values_list("turma_id", flat=True).distinct())
    alunos = Aluno.objects.filter(turma_id__in=turmas_ids, ativo=True).order_by("turma_id", "nome")

    return JsonResponse({
        "ok": True,
        "generated_at": timezone.now().isoformat(),
        "today": hoje.isoformat(),
        "user": {"id": professor.id, "name": professor.get_full_name() or professor.username},
        "vinculos": [
            {
                "turma_id": v.turma_id,
                "turma_nome": v.turma.nome,
                "disciplina_id": v.disciplina_id,
                "disciplina_nome": v.disciplina.nome,
            }
            for v in vinculos
        ],
        "horarios": [_serialize_horario(h) for h in horarios],
        "alunos": [
            {"id": a.id, "turma_id": a.turma_id, "nome": a.nome, "matricula": a.matricula}
            for a in alunos
        ],
    })

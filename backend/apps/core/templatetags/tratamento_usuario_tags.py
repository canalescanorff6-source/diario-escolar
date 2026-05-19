from django import template

register = template.Library()


_NOMES_FEMININOS = {
    "ana", "maria", "julia", "júlia", "juliana", "mariana", "larissa", "leticia", "letícia",
    "beatriz", "bruna", "bianca", "camila", "carla", "carolina", "cecilia", "cecília",
    "daniela", "debora", "débora", "eduarda", "eliane", "elisangela", "elisângela",
    "erica", "érica", "fernanda", "francisca", "gabriela", "giovana", "giovanna",
    "helena", "isabela", "isabella", "jaqueline", "jessica", "jéssica", "joana",
    "katia", "kátia", "laura", "luana", "luciana", "luzia", "marcia", "márcia",
    "monica", "mônica", "patricia", "patrícia", "paula", "raquel", "renata", "rita",
    "sandra", "simone", "sueli", "suelen", "talita", "tatiana", "teresa", "tereza",
    "valeria", "valéria", "vanessa", "vera", "vitoria", "vitória", "yasmin",
}

_NOMES_MASCULINOS = {
    "ademir", "adriano", "alan", "alex", "alexandre", "anderson", "andre", "andré",
    "antonio", "antônio", "augusto", "bruno", "carlos", "cleiton", "daniel", "davi",
    "diego", "douglas", "edson", "eduardo", "elias", "emanuel", "fabio", "fábio",
    "felipe", "fernando", "francisco", "gabriel", "gilberto", "gustavo", "henrique",
    "igor", "israel", "joao", "joão", "jorge", "jose", "josé", "leandro", "leonardo",
    "lucas", "luiz", "luis", "marcelo", "marcos", "mateus", "matheus", "miguel",
    "paulo", "pedro", "rafael", "raimundo", "renato", "ricardo", "roberto", "rodrigo",
    "samuel", "sergio", "sérgio", "thiago", "tiago", "vinicius", "vinícius", "vitor", "victor",
}

_NOMES_MASCULINOS_TERMINADOS_EM_A = {
    "lucas", "jonas", "thomas", "tomás", "nicolas", "nícolas", "dias", "matias", "ias",
    "josias", "jeremias", "elias", "tobias", "sillas", "silas", "dimas",
}


def _clean(value):
    return str(value or "").strip()


def _nome_usuario(user):
    if not user:
        return ""
    full_name = ""
    try:
        full_name = user.get_full_name()
    except Exception:
        full_name = ""
    for value in [
        full_name,
        getattr(user, "nome", ""),
        getattr(user, "first_name", ""),
        getattr(user, "username", ""),
        getattr(user, "email", ""),
    ]:
        value = _clean(value)
        if value:
            if "@" in value and not value.startswith("@"):  # e-mail como último recurso
                return value.split("@", 1)[0].replace(".", " ").replace("_", " ").title()
            return value.title() if value.islower() else value
    return "Usuário"


def _primeiro_nome(user):
    nome = _nome_usuario(user)
    return _clean(nome.split()[0]).lower()


def _provavel_feminino(user):
    primeiro = _primeiro_nome(user)
    if not primeiro:
        return False
    if primeiro in _NOMES_FEMININOS:
        return True
    if primeiro in _NOMES_MASCULINOS or primeiro in _NOMES_MASCULINOS_TERMINADOS_EM_A:
        return False
    # Regra simples para nomes brasileiros: muitos nomes femininos terminam em "a".
    # Quando não houver certeza, mantemos o masculino padrão para não quebrar o layout.
    return primeiro.endswith("a")


@register.filter
def nome_exibicao(user):
    return _nome_usuario(user)


@register.filter
def tratamento_professor(user):
    return "Professora" if _provavel_feminino(user) else "Professor"


@register.filter
def tratamento_gestao(user):
    return "Gestora" if _provavel_feminino(user) else "Gestor"

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cria ou atualiza o gestor inicial sem gerar credenciais padrão."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default="gestor")
        parser.add_argument("--senha", default="", help="Ou configure GESTOR_INICIAL_SENHA no ambiente.")
        parser.add_argument("--email", default="")
        parser.add_argument("--nome", default="Gestor Escolar")

    def handle(self, *args, **options):
        User = get_user_model()
        username = (options["usuario"] or "").strip()
        password = options["senha"] or os.environ.get("GESTOR_INICIAL_SENHA", "")
        if not username:
            raise CommandError("Informe um usuário válido.")
        if not password:
            raise CommandError("Informe --senha ou configure GESTOR_INICIAL_SENHA.")

        probe = User(username=username, email=options["email"] or "")
        try:
            validate_password(password, user=probe)
        except ValidationError as exc:
            raise CommandError("Senha recusada: " + " ".join(exc.messages)) from exc

        user, created = User.objects.get_or_create(username=username)
        user.tipo = "ADMIN"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if options["email"]:
            user.email = options["email"]
        nome = (options["nome"] or "").strip()
        if nome:
            partes = nome.split(maxsplit=1)
            user.first_name = partes[0]
            user.last_name = partes[1] if len(partes) > 1 else ""
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(("Criado" if created else "Atualizado") + f" gestor inicial: {username}"))
        self.stdout.write("Cadastre escola, professores, turmas, disciplinas e horários pela área de gestão.")

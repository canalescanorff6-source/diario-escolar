from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cria um usuário gestor inicial sem cadastrar dados escolares de teste."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default="gestor")
        parser.add_argument("--senha", default="gestor123")
        parser.add_argument("--email", default="")
        parser.add_argument("--nome", default="Gestor Escolar")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["usuario"].strip()
        password = options["senha"]
        if not username:
            raise CommandError("Informe um usuário válido.")
        user, created = User.objects.get_or_create(username=username, defaults={
            "email": options["email"],
            "tipo": "ADMIN",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        })
        user.tipo = "ADMIN"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if options["email"]:
            user.email = options["email"]
        nome = options["nome"].strip()
        if nome:
            partes = nome.split(maxsplit=1)
            user.first_name = partes[0]
            user.last_name = partes[1] if len(partes) > 1 else ""
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(("Criado" if created else "Atualizado") + f" gestor inicial: {username}"))
        self.stdout.write("Depois entre no sistema e cadastre escola, professores, turmas, disciplinas e horários manualmente.")

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

from apps.core.licenca_gestao import gerar_serial_gestao


class Command(BaseCommand):
    help = "Gera um serial/key para liberar o acesso da gestão por uma quantidade de dias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--gestor",
            default="",
            help="E-mail ou username da conta da gestão. Se vazio, o serial serve para qualquer gestão.",
        )
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Quantidade de dias que o serial/key vai liberar. Padrão: 30.",
        )
        parser.add_argument(
            "--observacao",
            default="",
            help="Observação interna, por exemplo nome da escola ou comprovante.",
        )
        parser.add_argument(
            "--sem-email",
            action="store_true",
            help="Não envia por e-mail; apenas mostra o serial no terminal.",
        )
        parser.add_argument(
            "--destino",
            default="",
            help="E-mail que vai receber o serial. Padrão: GESTAO_AUTORIZACAO_EMAIL.",
        )

    def handle(self, *args, **options):
        dias = max(int(options["dias"] or 30), 1)
        gestor = (options["gestor"] or "").strip().lower()
        observacao = (options["observacao"] or "").strip()
        serial = gerar_serial_gestao(gestor, dias=dias, observacao=observacao)
        destino = (options["destino"] or getattr(settings, "GESTAO_AUTORIZACAO_EMAIL", "") or "").strip()

        self.stdout.write(self.style.SUCCESS("Serial/key gerado com sucesso:"))
        self.stdout.write(serial)
        self.stdout.write("")
        self.stdout.write(f"Dias liberados: {dias}")
        self.stdout.write(f"Conta da gestão: {gestor or 'qualquer conta de gestão'}")

        if options["sem_email"]:
            return

        if not destino:
            raise CommandError("Nenhum e-mail de destino configurado. Use --destino ou configure GESTAO_AUTORIZACAO_EMAIL.")

        assunto = "Serial/key de ativação — Diário IA Escolar"
        mensagem = (
            "Serial/key de ativação da gestão escolar\n\n"
            f"Dias liberados: {dias}\n"
            f"Conta da gestão: {gestor or 'qualquer conta de gestão'}\n"
            f"Observação: {observacao or '-'}\n\n"
            "Serial/key:\n"
            f"{serial}\n\n"
            "Use este código somente na tela oficial de ativação do Diário IA Escolar."
        )
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[destino],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Serial enviado para {destino}."))

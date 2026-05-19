import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


def _mask(value):
    value = str(value or "")
    if not value:
        return "(vazio)"
    if len(value) <= 6:
        return "***"
    return value[:3] + "***" + value[-3:]


def _gerar_codigo_6_digitos():
    return f"{secrets.randbelow(1_000_000):06d}"


class Command(BaseCommand):
    help = "Envia um e-mail de teste com código numérico de 6 dígitos para validar o SMTP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--para",
            default=None,
            help="E-mail de destino. Se omitido, usa GESTAO_AUTORIZACAO_EMAIL.",
        )

    def handle(self, *args, **options):
        destino = (options.get("para") or getattr(settings, "GESTAO_AUTORIZACAO_EMAIL", "") or "").strip()
        codigo = _gerar_codigo_6_digitos()

        if not destino:
            raise CommandError("Configure GESTAO_AUTORIZACAO_EMAIL ou use --para email@exemplo.com.")

        self.stdout.write("Configuração atual de e-mail:")
        self.stdout.write(f"  EMAIL_BACKEND={getattr(settings, 'EMAIL_BACKEND', '')}")
        self.stdout.write(f"  EMAIL_HOST={getattr(settings, 'EMAIL_HOST', '') or '(vazio)'}")
        self.stdout.write(f"  EMAIL_PORT={getattr(settings, 'EMAIL_PORT', '')}")
        self.stdout.write(f"  EMAIL_USE_TLS={getattr(settings, 'EMAIL_USE_TLS', '')}")
        self.stdout.write(f"  EMAIL_HOST_USER={_mask(getattr(settings, 'EMAIL_HOST_USER', ''))}")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL={getattr(settings, 'DEFAULT_FROM_EMAIL', '')}")
        self.stdout.write(f"  DESTINO={destino}")

        try:
            enviados = send_mail(
                subject="Teste de e-mail — Diário IA Escolar",
                message=(
                    "Teste de envio do Diário IA Escolar.\n\n"
                    "Se você recebeu esta mensagem, o SMTP está funcionando.\n\n"
                    f"Código numérico de teste: {codigo}\n\n"
                    "Atenção: este código é apenas para testar o envio de e-mail. "
                    "Na tela real, o sistema gera outro código de 6 dígitos e valida pela sessão do navegador.\n"
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[destino],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f"Falha ao enviar e-mail: {exc}") from exc

        if not enviados:
            raise CommandError("O Django não confirmou o envio do e-mail.")

        backend_name = str(getattr(settings, "EMAIL_BACKEND", ""))
        if "console.EmailBackend" in backend_name:
            self.stdout.write(self.style.WARNING(
                "Teste gerado no terminal. Para envio real, configure EMAIL_HOST, "
                "EMAIL_HOST_USER e EMAIL_HOST_PASSWORD com SMTP."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"E-mail de teste enviado para {destino}."))

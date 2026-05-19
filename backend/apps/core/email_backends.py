from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives


def _parse_email(value):
    name, email = parseaddr(str(value or ""))
    return (name or "", email or str(value or "").strip())


def _recipient_item(value):
    name, email = _parse_email(value)
    item = {"email": email}
    if name:
        item["name"] = name
    return item


class BrevoEmailBackend(BaseEmailBackend):
    """Backend de e-mail via API HTTPS da Brevo.

    Útil no Render Free, onde SMTP pelas portas 25/465/587 é bloqueado.
    Variáveis esperadas:
      BREVO_API_KEY=chave_da_brevo
      BREVO_SENDER_EMAIL=email_remetente_verificado
      BREVO_SENDER_NAME=Diário IA Escolar
    """

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "BREVO_API_KEY", "")
        api_url = getattr(settings, "BREVO_API_URL", "https://api.brevo.com/v3/smtp/email")
        sender_name = getattr(settings, "BREVO_SENDER_NAME", "Diário IA Escolar")
        sender_email = getattr(settings, "BREVO_SENDER_EMAIL", "")

        default_name, default_email = _parse_email(getattr(settings, "DEFAULT_FROM_EMAIL", ""))
        sender_email = sender_email or default_email
        sender_name = sender_name or default_name or "Diário IA Escolar"

        if not api_key or not sender_email:
            if self.fail_silently:
                return 0
            raise RuntimeError("Configure BREVO_API_KEY e BREVO_SENDER_EMAIL para enviar e-mail pela Brevo.")

        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        }

        enviados = 0
        for message in email_messages:
            if not message.recipients():
                continue

            payload = {
                "sender": {"name": sender_name, "email": sender_email},
                "to": [_recipient_item(addr) for addr in message.to],
                "subject": message.subject,
                "textContent": message.body or " ",
            }
            if message.cc:
                payload["cc"] = [_recipient_item(addr) for addr in message.cc]
            if message.bcc:
                payload["bcc"] = [_recipient_item(addr) for addr in message.bcc]
            if message.reply_to:
                reply_name, reply_email = _parse_email(message.reply_to[0])
                payload["replyTo"] = {"email": reply_email, **({"name": reply_name} if reply_name else {})}

            if isinstance(message, EmailMultiAlternatives):
                for content, mimetype in message.alternatives:
                    if mimetype == "text/html":
                        payload["htmlContent"] = content
                        break

            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=getattr(settings, "EMAIL_TIMEOUT", 20))
                response.raise_for_status()
            except Exception:
                if not self.fail_silently:
                    raise
                continue
            enviados += 1

        return enviados

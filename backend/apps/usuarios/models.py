from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):

    class TipoUsuario(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        PROF = 'PROF', 'Professor'
        COORD = 'COORD', 'Coordenador'
        SEC = 'SEC', 'Secretaria'

    tipo = models.CharField(
        max_length=10,
        choices=TipoUsuario.choices,
        default=TipoUsuario.PROF
    )

    foto = models.ImageField(
        upload_to="professores/",
        null=True,
        blank=True
    )

    gestao_teste_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Início do teste da gestão",
    )
    gestao_acesso_expira_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Acesso da gestão expira em",
    )
    gestao_acesso_bloqueado = models.BooleanField(
        default=False,
        verbose_name="Acesso da gestão bloqueado",
    )
    gestao_serial_ultimo = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Último serial aplicado",
    )

    def __str__(self):
        return f"{self.username} - {self.get_tipo_display()}"

    # Helpers profissionais (usaremos no dashboard)
    @property
    def is_admin(self):
        return self.tipo == self.TipoUsuario.ADMIN

    @property
    def is_professor(self):
        return self.tipo == self.TipoUsuario.PROF

    @property
    def is_coordenador(self):
        return self.tipo == self.TipoUsuario.COORD

    @property
    def is_secretaria(self):
        return self.tipo == self.TipoUsuario.SEC

class ApiToken(models.Model):
    """Token opaco para o aplicativo Android.

    O valor bruto nunca é persistido; apenas o SHA-256 é salvo no banco.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )
    chave_hash = models.CharField(max_length=64, unique=True, db_index=True)
    prefixo = models.CharField(max_length=12, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ultimo_uso_em = models.DateTimeField(null=True, blank=True)
    expira_em = models.DateTimeField()
    revogado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Token do aplicativo"
        verbose_name_plural = "Tokens do aplicativo"

    @classmethod
    def emitir(cls, usuario, dias=30):
        import hashlib
        import secrets
        from datetime import timedelta
        from django.utils import timezone

        bruto = secrets.token_urlsafe(36)
        digest = hashlib.sha256(bruto.encode("utf-8")).hexdigest()
        token = cls.objects.create(
            usuario=usuario,
            chave_hash=digest,
            prefixo=bruto[:12],
            expira_em=timezone.now() + timedelta(days=max(int(dias), 1)),
        )
        return token, bruto

    @classmethod
    def autenticar(cls, bruto):
        import hashlib
        from django.utils import timezone

        if not bruto:
            return None
        digest = hashlib.sha256(bruto.encode("utf-8")).hexdigest()
        token = cls.objects.select_related("usuario").filter(
            chave_hash=digest,
            revogado=False,
            expira_em__gt=timezone.now(),
            usuario__is_active=True,
        ).first()
        if token:
            token.ultimo_uso_em = timezone.now()
            token.save(update_fields=["ultimo_uso_em"])
        return token

    def __str__(self):
        return f"{self.usuario.username} • {self.prefixo}…"

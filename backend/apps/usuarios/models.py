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
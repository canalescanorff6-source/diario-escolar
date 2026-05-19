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
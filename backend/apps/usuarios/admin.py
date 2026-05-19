from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin profissional para criar e gerenciar usuários do Diário IA.

    Corrige o problema de criação pelo /admin/: agora o Django usa o fluxo
    padrão de criação com senha criptografada, confirmação de senha e campos
    de perfil do sistema.
    """

    list_display = (
        "username",
        "nome_completo",
        "email",
        "tipo_badge",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    list_filter = (
        "tipo",
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )
    ordering = ("username",)
    list_per_page = 30
    save_on_top = True

    fieldsets = UserAdmin.fieldsets + (
        (
            "Diário IA — Perfil escolar",
            {
                "fields": ("tipo", "foto"),
                "description": "Defina se o usuário acessa o painel do Professor ou o painel de Gestão.",
            },
        ),
    )

    add_fieldsets = (
        (
            "Acesso",
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        (
            "Dados do usuário",
            {
                "classes": ("wide",),
                "fields": ("first_name", "last_name", "email", "tipo"),
            },
        ),
        (
            "Permissões administrativas",
            {
                "classes": ("collapse",),
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
    )

    def nome_completo(self, obj):
        nome = obj.get_full_name().strip()
        return nome or "—"
    nome_completo.short_description = "Nome"

    def tipo_badge(self, obj):
        cores = {
            "ADMIN": ("#5eead4", "Administrador"),
            "SEC": ("#67e8f9", "Secretaria"),
            "COORD": ("#a7f3d0", "Coordenação"),
            "PROF": ("#fde68a", "Professor"),
        }
        cor, label = cores.get(obj.tipo, ("#cbd5e1", obj.get_tipo_display()))
        return format_html(
            '<span style="display:inline-flex;align-items:center;padding:4px 9px;border-radius:999px;'
            'background:rgba(15,23,42,.72);border:1px solid {};color:{};font-weight:800;font-size:11px">{}</span>',
            cor,
            cor,
            label,
        )
    tipo_badge.short_description = "Perfil"


    def save_model(self, request, obj, form, change):
        """Ao criar/editar professor no admin, garante perfil pedagógico automático."""
        super().save_model(request, obj, form, change)
        try:
            if obj.tipo == "PROF":
                from apps.academico.models import ProfessorPerfil, Escola
                escola = Escola.objects.filter(ativa=True).first()
                ProfessorPerfil.objects.get_or_create(
                    usuario=obj,
                    defaults={"escola": escola, "ativo": True},
                )
        except Exception:
            pass


admin.site.site_header = "Diário IA Escolar"
admin.site.site_title = "Diário IA Admin"
admin.site.index_title = "Administração Premium"

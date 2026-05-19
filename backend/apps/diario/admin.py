from django.contrib import admin

from .models import Diario


@admin.register(Diario)
class DiarioAdmin(admin.ModelAdmin):

    list_display = (

        'id',
        'turma',
        'professor',
        'data',
        'titulo',

    )

    search_fields = (

        'titulo',
        'turma__nome',

    )

    list_filter = (

        'data',
        'turma',

    )
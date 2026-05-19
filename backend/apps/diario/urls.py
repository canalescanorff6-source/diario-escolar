from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.diario_home,
        name='diario_home'
    ),

    path(
        'novo/',
        views.novo_diario,
        name='novo_diario'
    ),

]
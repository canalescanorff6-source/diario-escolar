from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.contrib.auth.views import LogoutView
from django.views.static import serve as media_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout/', LogoutView.as_view(), name='logout_direct'),

    # LOGIN / LOGOUT DO DJANGO
    path('accounts/', include('django.contrib.auth.urls')),

    # CORE
    path('', include('apps.core.urls')),

    # DIARIO
    path(
        'diario-inteligente/',
        include('apps.diario.urls')
    ),

]
# Uploads do sistema (imagens de perfil) — necessário para uso local e para implantação simples.
# Para produção com muitos uploads, use Persistent Disk ou armazenamento externo.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

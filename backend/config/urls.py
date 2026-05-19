from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.contrib.auth.views import LogoutView
from django.views.static import serve as media_serve
from django.http import HttpResponse


def health_check_runsite(request):
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('healthz', health_check_runsite, name='healthz_no_slash'),
    path('healthz/', health_check_runsite, name='healthz'),
    path('health', health_check_runsite, name='health_no_slash'),
    path('health/', health_check_runsite, name='health'),

    # Django Admin protegido: /admin/ não é usado.
    # A URL real vem de CRIADOR_ADMIN_URL, normalmente /admin-criador/.
    path(settings.CRIADOR_ADMIN_URL, admin.site.urls),

    path('logout/', LogoutView.as_view(), name='logout_direct'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('apps.core.urls')),
    path('diario-inteligente/', include('apps.diario.urls')),
]

# Uploads do sistema (imagens de perfil).
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

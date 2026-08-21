from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.http import HttpResponse
from django.urls import include, path, re_path


def health_check(request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = []
if getattr(settings, "RUNSITE_STATIC_URL_FALLBACK", False):
    urlpatterns.append(re_path(r"^static/(?P<path>.*)$", staticfiles_serve, {"insecure": True}))

urlpatterns += [
    path("healthz", health_check, name="healthz_no_slash"),
    path("health/", health_check, name="health"),
    path(settings.CRIADOR_ADMIN_URL, admin.site.urls),
    path("logout/", LogoutView.as_view(), name="logout_direct"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/v1/", include("apps.core.api_urls")),
    path("", include("apps.core.urls")),
]

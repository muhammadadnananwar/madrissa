from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve

from attendance import iclock

from cms.urls import site_urlpatterns
from website.urls import public_urlpatterns

admin.site.site_header = "University of Muhammadia Saifia"
admin.site.site_title = "Madrasa Admin"

API_APPS = ["core", "accounts", "academics", "people", "attendance", "leaves", "lms", "liveclasses", "exams", "hifz",
            "finance", "library", "hostel", "transport", "inventory", "communication", "website", "cms"]

urlpatterns = [
    path("healthz", lambda request: JsonResponse({"status": "ok"})),  # deploy health check
    path("django-admin/", admin.site.urls),
    # Biometric terminals (ZKTeco ADMS push protocol) — fixed paths expected by the devices
    re_path(r"^iclock/cdata(?:\.aspx)?/?$", iclock.cdata),
    re_path(r"^iclock/getrequest(?:\.aspx)?/?$", iclock.getrequest),
    re_path(r"^iclock/devicecmd(?:\.aspx)?/?$", iclock.devicecmd),
    path("api/public/", include(public_urlpatterns)),
    # Anonymous API of the public website (React site in /website) — paths without trailing slash
    path("api/site/public/", include(site_urlpatterns)),
    *[path("api/", include(f"{app}.urls")) for app in API_APPS],
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

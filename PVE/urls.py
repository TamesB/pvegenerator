# Author: Tames Boon

import debug_toolbar
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from PVE.views import LandingView

urlpatterns = [
    path("__debug__/", include(debug_toolbar.urls)),
    path("", LandingView, name="landingpage"),
    path("beheer/", include("app.urls")),
    path("beheer/project/", include("project.urls")),
    path("beheer/generator/", include("generator.urls")),
    path("beheer/users/", include("users.urls")),
    path("admin/", admin.site.urls),
    path("syntrus/", include("syntrus.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.EXPORTS_URL, document_root=settings.EXPORTS_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

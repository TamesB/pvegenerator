# Author: Tames Boon

from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', include('app.urls')),
    path('project/', include('project.urls')),
    path('generator/', include('generator.urls')),
    path('users/', include('users.urls')),
    path('admin/', admin.site.urls),
    path('invitations/', include('invitations.urls', namespace='invitations')),
    path('.well-known/pki-validation/F75439F78E0109B1AA900632C75F34A5.txt', views.AppDoen, name="certif")
]

if settings.DEBUG:
    urlpatterns += static(settings.EXPORTS_URL, document_root=settings.EXPORTS_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
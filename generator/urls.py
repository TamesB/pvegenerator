# Author: Tames Boon

from django.urls import path

from . import views

# Urls for the specific app
urlpatterns = [
    path("generate/<int:client_pk>/<int:version_pk>", views.GeneratePVEView, name="generate"),
    path("download/<str:filename>", views.download_file, name="download"),
    path(
        "download/b/<str:zipFilename>", views.download_attachments, name="downloadattachments"
    ),
    path("compare/<int:version_pk>", views.compareFormView, name="compare"),
]

# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path("generate/<int:versie_pk>", views.GeneratePVEView, name="generate"),
    path("download/<str:filename>", views.download_file, name="download"),
    path(
        "download/b/<str:zipFilename>", views.download_bijlagen, name="downloadbijlagen"
    ),
    path("compare/<int:versie_pk>", views.compareView, name="compare"),
    path("compare/<int:versie_pk>/<int:pk>", views.compareFormView, name="compareform"),
]

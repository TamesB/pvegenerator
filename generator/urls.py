# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('generate', views.GeneratePVEView, name='generate'),
    path('download/<str:filename>', views.download_file, name='download'),
]

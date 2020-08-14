# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('start', views.StartProjectView, name="startproject"),
    path('connectpve/<int:pk>', views.ConnectPVEView, name="connectpve"),
    path('overview', views.ProjectOverviewView, name="projectoverview"),
    path('overview/all', views.AllProjectsView, name="allprojects"),
    path('<int:pk>', views.ProjectViewView, name="projectview"),
    path('<int:pk>/pve', views.download_pve, name='downloadpve'),
]

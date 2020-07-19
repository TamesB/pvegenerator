# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('start', views.StartProjectView, name="startproject"),
    path('overview', views.ProjectOverviewView, name="projectoverview"),
    path('<int:pk>', views.ProjectViewView, name="projectview"),
]

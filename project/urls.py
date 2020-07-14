# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('project', views.ProjectHomepageView, name="projecthomepage"),
    path('project/start', views.StartProjectView, name="startproject"),
    path('project/overview', views.ProjectOverviewView, name="projectoverview"),
    path('project/<int:id>', views.ProjectViewView, name="projectview"),
]

# Author: Tames Boon

from django.urls import path

from . import views

# Urls for the specific app
urlpatterns = [
    path("overview", views.ProjectOverviewView, name="projectoverview"),
    path("overview/all", views.AllProjectsView, name="allprojects"),
    path("<int:pk>", views.ProjectViewView, name="projectview"),
]

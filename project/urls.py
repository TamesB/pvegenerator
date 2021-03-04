# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path("start", views.StartProjectView, name="startproject"),
    path("connectpve/<int:pk>", views.ConnectPVEView, name="connectpve"),
    path("overview", views.ProjectOverviewView, name="projectoverview"),
    path("overview/all", views.AllProjectsView, name="allprojects"),
    path("<int:pk>", views.ProjectViewView, name="projectview"),
    path("<int:project_id>/annotations", views.viewAnnotations, name="viewannotations"),
    path(
        "<int:project_id>/items/<int:item_id>/view",
        views.viewItemAnnotations,
        name="viewitemannotations",
    ),
    path(
        "<int:project_id>/annotations/<int:item_id>/add",
        views.addAnnotationPve,
        name="addannotation",
    ),
    path(
        "<int:project_id>/searchitem", views.searchProjectPveItem, name="searchpveitem"
    ),
    path("myannotations", views.viewOwnAnnotations, name="myannotations"),
    path(
        "myannotations/<int:project_id>/<int:ann_id>/edit",
        views.editAnnotationPve,
        name="editannotation",
    ),
    path(
        "myannotations/<int:project_id>/<int:ann_id>/delete",
        views.deleteAnnotationPve,
        name="deleteannotation",
    ),
    path("<int:pk>/pve", views.download_pve, name="downloadpve"),
]

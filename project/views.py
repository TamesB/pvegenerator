import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from pyproj import Transformer

from app.models import Bouwsoort, Doelgroep, PVEItem, TypeObject, ActieveVersie
from generator.forms import PVEParameterForm

from . import forms, models

@staff_member_required
def ProjectOverviewView(request):
    if not models.Project.objects.filter(
        permitted__username__contains=request.user.username
    ).exists():
        raise Http404("Je heb geen projecten waar je toegang tot heb.")

    context = {}
    context["projects"] = models.Project.objects.filter(
        permitted__username__contains=request.user.username
    )
    return render(request, "projectoverview.html", context)


@staff_member_required
def AllProjectsView(request):
    if request.user.type_user != "B":
        raise Http404("404.")

    projects = models.Project.objects.all()
    locations = [
        [project.name, project.plaats.x, project.plaats.y] for project in projects
    ]

    context = {}
    context["projects"] = models.Project.objects.all()
    context["locations"] = locations
    return render(request, "allprojectoverview.html", context)


@staff_member_required
def ProjectViewView(request, pk):
    if request.user.type_user != "B":
        if not models.Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    project = get_object_or_404(models.Project, pk=pk)

    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")
    x, y = transformer.transform(project.plaats.x, project.plaats.y)

    location = {}
    location["type"] = "Point"
    location["coordinates"] = [x, y]

    context = {}
    context["project"] = project
    context["location"] = location
    return render(request, "viewproject.html", context)
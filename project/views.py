from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
import datetime
import os
from django.conf import settings
import mimetypes
from . import models
from . import forms

@login_required
def StartProjectView(request):
    if request.method == 'POST':
        form = forms.StartProjectForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            project = models.Project()
            project.naam = form.cleaned_data["naam"]
            project.nummer = form.cleaned_data["nummer"]
            project.plaats = form.cleaned_data["plaats"]
            project.vhe = form.cleaned_data["vhe"]
            project.pensioenfonds = form.cleaned_data["pensioenfonds"]
            project.statuscontract = models.ContractStatus.objects.filter(contrstatus="TKO").first()
            project.permitted = request.user
            print(form.cleaned_data["plaats"])
            project.save()

            context = {}
            context["project"] = project
            return render(request, 'viewproject.html', context)

    # form
    form = forms.StartProjectForm()

    context = {}
    context["form"] = form
    return render(request, 'startproject.html', context)

@login_required
def ProjectOverviewView(request):
    if not models.Project.objects.filter(permitted__username__contains=request.user.username):
        return Http404("Je heb geen projecten waar je toegang tot heb.")
    
    context = {}
    context["projects"] = models.Project.objects.filter(permitted__username__contains=request.user.username)
    return render(request, 'projectoverview.html', context)

@login_required
def ProjectViewView(request, pk):
    pk = int(pk)

    if not models.Project.objects.filter(id=pk):
        return Http404('404')

    if not models.Project.objects.filter(id=pk, permitted__username__contains=request.user.username):
        return Http404('Geen toegang tot dit project')

    project = models.Project.objects.filter(id=pk).first()
    
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")
    x,y = transformer.transform(project.plaats.x, project.plaats.y)

    context = {}
    context["project"] = project
    context["x"] = x
    context["y"] = y
    return render(request, 'viewproject.html', context)
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
from app.models import PVEItem, Bouwsoort, TypeObject, Doelgroep
from generator.forms import PVEParameterForm
from . import forms
from users.forms import KoppelDerdeUser
from users.models import CustomUser

from pyproj import CRS, Transformer
from utils import writePdf, writeDiffPdf, createBijlageZip
import zipfile

@login_required
def StartProjectView(request):

    if request.user.type_user != 'OG' and request.user.type_user != 'B':
        raise Http404("404.")

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
            project.statuscontract = models.ContractStatus.objects.filter(contrstatus="LOI").first()
            project.save()
            project.permitted.add(request.user)

            return HttpResponseRedirect(reverse('connectpve', args=(project.id,)))

    # form
    form = forms.StartProjectForm()

    context = {}
    context["form"] = form
    return render(request, 'startproject.html', context)

@login_required
def ConnectPVEView(request, pk):
    if request.user.type_user != 'OG' and request.user.type_user != 'B':
        raise Http404("404.")

    project = models.Project.objects.filter(id=pk).first()

    if project.pveconnected == True:
        context = {}
        context["project"] = project
        return render(request, 'viewproject.html', context)

    if request.method == 'POST':
        form = PVEParameterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # get parameters, find all pveitems with that
            (Bouwsoort1, TypeObject1, Doelgroep1, Bouwsoort2, TypeObject2, Doelgroep2, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort1"], form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"], form.cleaned_data["Bouwsoort2"], form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )

            # add bouwsoort to the project
            project.bouwsoort1 = Bouwsoort.objects.filter(parameter=Bouwsoort1).first()

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = PVEItem.objects.filter(
                basisregel=True)
            basic_PVE = basic_PVE.union(
                PVEItem.objects.filter(
                    Bouwsoort__parameter__contains=Bouwsoort1))

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(
                        Bouwsoort__parameter__contains=Bouwsoort2))
                project.bouwsoort2 = Bouwsoort.objects.filter(parameter=Bouwsoort2).first()

            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject1))
                project.typeObject1 = TypeObject.objects.filter(parameter=TypeObject1).first()

            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject2))
                project.typeObject2 = TypeObject.objects.filter(parameter=TypeObject2).first()

            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep1))
                project.doelgroep1 = Doelgroep.objects.filter(parameter=Doelgroep1).first()

            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep2))
                project.doelgroep2 = Doelgroep.objects.filter(parameter=Doelgroep2).first()


            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(Q(AED=True)))
                
                project.AED = True

            if Smarthome:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(Q(Smarthome=True)))
                # add the parameter to the project
                project.Smarthome = True

            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(Q(EntreeUpgrade=True)))
                project.EntreeUpgrade = True

            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(Q(Pakketdient=True)))
                project.Pakketdient = True

            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    PVEItem.objects.filter(Q(JamesConcept=True)))
                project.JamesConcept = True

            # add the project to all the pve items
            for item in basic_PVE:
                item.projects.add(project)

            # succesfully connected, save the project
            project.pveconnected = True
            project.save()

            context = {}
            context["project"] = project
            return render(request, 'viewproject.html', context)

    # form
    form = PVEParameterForm()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, 'connectpve.html', context)

@login_required
def ProjectOverviewView(request):
    if not models.Project.objects.filter(permitted__username__contains=request.user.username):
        raise Http404("Je heb geen projecten waar je toegang tot heb.")
    
    context = {}
    context["projects"] = models.Project.objects.filter(permitted__username__contains=request.user.username)
    return render(request, 'projectoverview.html', context)

@login_required
def AllProjectsView(request):
    if request.user.type_user != 'B':
        raise Http404("404.")
    
    projects = models.Project.objects.all()
    locations = [[project.naam, project.plaats.x, project.plaats.y] for project in projects]

    context = {}
    context["projects"] = models.Project.objects.all()
    context["locations"] = locations
    return render(request, 'allprojectoverview.html', context)

@login_required
def ProjectViewView(request, pk):
    pk = int(pk)

    if not models.Project.objects.filter(id=pk):
        raise Http404('404')

    if request.user.type_user != 'B':
        if not models.Project.objects.filter(id=pk, permitted__username__contains=request.user.username):
            raise Http404('404')

    project = models.Project.objects.filter(id=pk).first()
    
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")
    x,y = transformer.transform(project.plaats.x, project.plaats.y)

    location = {}
    location["type"] = "Point"
    location["coordinates"] = [x, y]

    context = {}
    context["project"] = project
    context["location"] = location
    return render(request, 'viewproject.html', context)

@login_required
def koppelDerdeView(request, pk):
    pk = int(pk)

    if not models.Project.objects.filter(id=pk):
        raise Http404('404')

    if not request.user.type_user == 'OG' and not request.user.type_user == 'B':
        raise Http404('404')
    
    project = models.Project.objects.filter(id=pk).first()

    if request.method == 'POST':
        form = KoppelDerdeUser(request.POST)
        if form.is_valid():
            form.save()
            user = CustomUser.objects.filter(username=form.cleaned_data["username"]).first()
            project.permitted.add(user)
            messages.warning(request, 'Derde gekoppeld aan project. Stuur een email met de credenties naar uw klant.')
            return HttpResponseRedirect(reverse('projectview', args=(project.id,)))
    else:
        form = KoppelDerdeUser()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, 'koppelDerdeForm.html', context)
    
@login_required
def download_pve(request, pk):
    if not models.Project.objects.filter(id=pk):
        raise Http404('404')
    
    if request.user.type_user != 'B':
        if not models.Project.objects.filter(id=pk, permitted__username__contains=request.user.username):
            raise Http404('404')

    project = models.Project.objects.filter(id=pk).first()
    basic_PVE = PVEItem.objects.filter(projects__id__contains=pk)

    # make sure pve is ordered
    basic_PVE = basic_PVE.order_by('id')
    # make pdf
    parameters = []

    if project.bouwsoort1:
        parameters += f"{project.bouwsoort1.parameter} (Hoofd)",
    if project.bouwsoort2:
        parameters += f"{project.bouwsoort2.parameter} (Sub)",
    if project.typeObject1:
        parameters += f"{project.typeObject1.parameter} (Hoofd)",
    if project.typeObject2:
        parameters += f"{project.typeObject2.parameter} (Sub)",
    if project.doelgroep1:
        parameters += f"{project.doelgroep1.parameter} (Hoofd)",
    if project.doelgroep2:
        parameters += f"{project.doelgroep2.parameter} (Sub)",

    date = datetime.datetime.now()

    fileExt = "%s%s%s%s%s%s" % (
        date.strftime("%H"),
        date.strftime("%M"),
        date.strftime("%S"),
        date.strftime("%d"),
        date.strftime("%m"),
        date.strftime("%Y")
    )

    filename = f"PVE-{fileExt}"
    zipFilename = f"BIJLAGEN-{fileExt}"

    pdfmaker = writePdf.PDFMaker()
    pdfmaker.makepdf(filename, basic_PVE, parameters)

    # get bijlagen
    bijlagen = [str(item.bijlage) for item in basic_PVE if item.bijlage]
    #remove duplicates
    bijlagen = list(dict.fromkeys(bijlagen))

    if bijlagen:
        zipmaker = createBijlageZip.ZipMaker()
        zipmaker.makeZip(zipFilename, bijlagen)
    else:
        zipFilename = False

    # and render the result page
    context = {}
    context["itemsPVE"] = basic_PVE
    context["filename"] = filename
    context["zipFilename"] = zipFilename
    return render(request, 'PVEResult.html', context)

@login_required
def searchProjectPveItem(request, project_id):
    if not models.Project.objects.filter(id=project_id):
        raise Http404("404")

    if request.user.type_user != 'B':
        if not models.Project.objects.filter(id=project_id, permitted__username__contains=request.user.username):
            raise Http404('404')

    if request.method == 'POST':
        form = forms.SearchPVEItemForm(request.POST)
        if form.is_valid():
            inhoud = form.cleaned_data["inhoud"]

            items = PVEItem.objects.filter(inhoud__contains=inhoud)

            context = {}
            context["items"] = items
            context["project_id"] = project_id
            return render(request, "projectItemResults.html", context)
    else:
        form = forms.SearchPVEItemForm()

    context = {}
    context["project_id"] = project_id
    context["form"] = form
    return render(request, 'projectItemSearch.html', context)


@login_required
def viewAnnotations(request, project_id):
    if not models.Project.objects.filter(id=project_id):
        raise Http404("404")

    if request.user.type_user != 'B':
        if not models.Project.objects.filter(id=project_id, permitted__username__contains=request.user.username):
            raise Http404('404')
    
    annotations = models.PVEItemAnnotation.objects.filter(project__id=project_id).order_by('-datum')
    context = {}
    context["annotations"] = annotations
    context["project_id"] = project_id
    return render(request, 'viewAnnotations.html', context)

@login_required
def viewItemAnnotations(request, project_id, item_id):
    if not models.Project.objects.filter(id=project_id):
        raise Http404("404")

    if request.user.type_user != 'B':
        if not models.Project.objects.filter(id=project_id, permitted__username__contains=request.user.username):
            raise Http404('404')
    
    if not PVEItem.objects.filter(id=item_id):
        raise Http404("404")

    item = PVEItem.objects.filter(id=item_id).first()
    annotations = models.PVEItemAnnotation.objects.filter(project__id=project_id).order_by('-datum')
    annotationsitem = models.PVEItemAnnotation.objects.filter(project__id=project_id, item__id=item_id)
    annotationsitem = annotationsitem.order_by('datum')

    context = {}
    context["PVEItem"] = item
    context["annotations"] = annotations
    context["annotationsitem"] = annotationsitem
    context["project_id"] = project_id
    return render(request, 'annotationItemView.html', context)

@login_required
def addAnnotationPve(request, project_id, item_id):
    if not models.Project.objects.filter(id=project_id):
        raise Http404("404")

    if request.user.type_user != 'B':
        if not models.Project.objects.filter(id=project_id, permitted__username__contains=request.user.username):
            raise Http404('404')

    if not PVEItem.objects.filter(id=item_id):
        raise Http404("404") 

    if request.method == 'POST':
        form = forms.PVEItemAnnotationForm(request.POST)
        if form.is_valid():
            annotation = models.PVEItemAnnotation()
            annotation.gebruiker = request.user
            annotation.project = models.Project.objects.filter(id=project_id).first()
            annotation.annotation = form.cleaned_data["annotation"]
            annotation.item = PVEItem.objects.filter(id=item_id).first()
            if form.cleaned_data["kostenConsequenties"]:
                annotation.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
            annotation.save()

            messages.warning(request, 'Opmerking toegevoegd.')
            return HttpResponseRedirect(reverse('searchpveitem', args=(project_id,)))
    else:
        form = forms.PVEItemAnnotationForm()

    context = {}
    context["form"] = form
    context["project_id"] = project_id
    context["item_id"] = item_id
    return render(request, 'addAnnotation.html', context)
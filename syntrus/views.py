import datetime
import mimetypes
import secrets

import boto3
import botocore
import pytz
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files import storage
from django.core.mail import send_mail
from django.db import connection
from django.db.models import Q, Sum
from django.forms import formset_factory, modelformset_factory
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from geopy.geocoders import Nominatim

from app import models
from project.models import (Beleggers, BijlageToAnnotation, Project,
                            PVEItemAnnotation)
from syntrus import forms
from syntrus.forms import (AddOrganisatieForm, BijlageToAnnotationForm,
                           BijlageToReplyForm, FirstFreezeForm,
                           KoppelDerdeUserForm, StartProjectForm)
from syntrus.models import (FAQ, BijlageToReply, CommentReply, CommentStatus,
                            FrozenComments, Room)
from users.forms import AcceptInvitationForm
from users.models import CustomUser, Invitation, Organisatie
from utils import createBijlageZip, writePdf
from utils.createBijlageZip import ZipMaker
from utils.writePdf import PDFMaker

utc = pytz.UTC


def LoginView(request):
    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            return redirect("dashboard_syn")

    if request.method == "POST":
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            if "@" in form.cleaned_data["username"]:
                (email, password) = (
                    form.cleaned_data["username"],
                    form.cleaned_data["password"],
                )
                user = authenticate(request, email=email, password=password)
            else:
                (username, password) = (
                    form.cleaned_data["username"],
                    form.cleaned_data["password"],
                )
                user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("dashboard_syn")
            else:
                messages.warning(request, "Invalid login credentials")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # render the page
    context = {}
    context["form"] = forms.LoginForm()

    return render(request, "login_syn.html", context)


@login_required
def DashboardView(request):
    context = {}

    if Project.objects.filter(
        permitted__username__contains=request.user.username, belegger__naam="Syntrus"
    ).exists():
        projects = (
            Project.objects.filter(belegger__naam="Syntrus")
            .filter(permitted__username__contains=request.user.username)
            .distinct()
        )
        context["projects"] = projects

    if PVEItemAnnotation.objects.filter(gebruiker=request.user).exists():
        opmerkingen = PVEItemAnnotation.objects.filter(
            gebruiker=request.user, project__belegger__naam="Syntrus"
        )
        context["opmerkingen"] = opmerkingen

    if request.user.type_user == "B":
        return render(request, "dashboardBeheerder_syn.html", context)
    if request.user.type_user == "SB":
        return render(request, "dashboardBeheerder_syn.html", context)
    if request.user.type_user == "SOG":
        return render(request, "dashboardOpdrachtgever_syn.html", context)
    if request.user.type_user == "SD":
        return render(request, "dashboardDerde_syn.html", context)


@login_required(login_url="login_syn")
def FAQView(request):

    faqquery = FAQ.objects.all()
    if request.user.type_user == "SB":
        faqquery = FAQ.objects.filter(gebruikersrang="SB")
    if request.user.type_user == "SOG":
        faqquery = FAQ.objects.filter(gebruikersrang="SOG")
    if request.user.type_user == "SD":
        faqquery = FAQ.objects.filter(gebruikersrang="SD")

    context = {}
    context["faqquery"] = faqquery
    return render(request, "FAQ_syn.html", context)


@login_required(login_url="login_syn")
def LogoutView(request):
    logout(request)
    return redirect("login_syn")


@login_required(login_url="login_syn")
def ManageOrganisaties(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    context = {}
    context["organisaties"] = Organisatie.objects.all()
    return render(request, "organisatieManager.html", context)


@login_required(login_url="login_syn")
def AddOrganisatie(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.AddOrganisatieForm(request.POST)

        if form.is_valid():
            new_organisatie = Organisatie()
            new_organisatie.naam = form.cleaned_data["naam"]
            new_organisatie.save()
            return redirect("manageorganisaties_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["organisaties"] = Organisatie.objects.all()
    context["form"] = AddOrganisatieForm()
    return render(request, "organisatieAdd.html", context)


@login_required(login_url="login_syn")
def DeleteOrganisatie(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    organisatie = get_object_or_404(Organisatie, id=pk)

    if request.method == "POST":
        organisatie.delete()
        return redirect("manageorganisaties_syn")

    context = {}
    context["organisatie"] = organisatie
    context["organisaties"] = Organisatie.objects.all()
    return render(request, "organisatieDelete.html", context)


@login_required(login_url="login_syn")
def ManageProjects(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    context = {}
    context["projecten"] = Project.objects.all().order_by("-datum_recent_verandering")
    return render(request, "beheerProjecten_syn.html", context)


@login_required(login_url="login_syn")
def AddProjectManager(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, id=pk)

    if request.method == "POST":
        form = forms.AddProjectmanagerToProjectForm(request.POST)

        if form.is_valid():
            project.projectmanager = form.cleaned_data["projectmanager"]
            project.permitted.add(form.cleaned_data["projectmanager"])
            project.save()

            send_mail(
                f"Syntrus Projecten - Uitnodiging voor project {project}",
                f"""{ request.user } heeft u uitgenodigd projectmanager te zijn van het project { project } van Syntrus.
                
                U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan en de eerste PvE check uit te voeren.
                Link: https://pvegenerator.net/syntrus/project/{project.id}""",
                "admin@pvegenerator.net",
                [f'{form.cleaned_data["projectmanager"].email}'],
                fail_silently=False,
            )
            return redirect("manageprojecten_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["projecten"] = Project.objects.all().order_by("-datum_recent_verandering")
    context["project"] = project
    context["form"] = forms.AddProjectmanagerToProjectForm()
    return render(request, "beheerAddProjmanager.html", context)


@login_required(login_url="login_syn")
def AddOrganisatieToProject(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, id=pk)

    if request.method == "POST":
        form = forms.AddOrganisatieToProjectForm(request.POST)

        if form.is_valid():
            # voeg project toe aan organisatie
            organisatie = form.cleaned_data["organisatie"]
            organisatie.projecten.add(project)
            organisatie.save()

            # voeg organisatie toe aan project
            project.organisaties.add(organisatie)
            project.save()

            # geef alle werknemers toegang aan het project
            werknemers = organisatie.gebruikers.all()

            for werknemer in werknemers:
                project.permitted.add(werknemer)
                project.save()

                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {project}",
                    f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van Syntrus.
                    
                    U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/project/{project.id}""",
                    "admin@pvegenerator.net",
                    [f"{werknemer.email}"],
                    fail_silently=False,
                )

            return redirect("manageprojecten_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["projecten"] = Project.objects.all().order_by("-datum_recent_verandering")
    context["project"] = project
    context["form"] = forms.AddOrganisatieToProjectForm()
    return render(request, "beheerAddOrganisatieToProject.html", context)


@login_required(login_url="login_syn")
def ManageWerknemers(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    context = {}
    context["werknemers"] = CustomUser.objects.filter(
        Q(type_user="SD") | Q(type_user="SOG")
    ).order_by("-last_visit")
    return render(request, "beheerWerknemers_syn.html", context)


# Create your views here.
@login_required(login_url="login_syn")
def GeneratePVEView(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    versie = models.ActieveVersie.objects.get(belegger__naam="Syntrus").versie

    if request.method == "POST":
        # get user entered form
        form = forms.PVEParameterForm(request.POST)
        form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()

        # check validity
        if form.is_valid():
            # get parameters, find all pveitems with that
            (
                Bouwsoort1,
                TypeObject1,
                Doelgroep1,
                Bouwsoort2,
                TypeObject2,
                Doelgroep2,
                Bouwsoort3,
                TypeObject3,
                Doelgroep3,
                Smarthome,
                AED,
                EntreeUpgrade,
                Pakketdient,
                JamesConcept,
            ) = (
                form.cleaned_data["Bouwsoort1"],
                form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"],
                form.cleaned_data["Bouwsoort2"],
                form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"],
                form.cleaned_data["Bouwsoort3"],
                form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"],
                form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"],
                form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"],
                form.cleaned_data["JamesConcept"],
            )

            versie = models.ActieveVersie.objects.get(belegger__naam="Syntrus").versie
            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = (
                models.PVEItem.objects.select_related("hoofdstuk")
                .select_related("paragraaf")
                .filter(Q(versie=versie) & Q(basisregel=True))
            )
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.select_related("hoofdstuk")
                .select_related("paragraaf")
                .filter(versie=versie, Bouwsoort__parameter__contains=Bouwsoort1)
            )

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Bouwsoort__parameter__contains=Bouwsoort2)
                )
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Bouwsoort__parameter__contains=Bouwsoort3)
                )
            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, TypeObject__parameter__contains=TypeObject1)
                )
            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, TypeObject__parameter__contains=TypeObject2)
                )
            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, TypeObject__parameter__contains=TypeObject3)
                )
            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Doelgroep__parameter__contains=Doelgroep1)
                )
            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Doelgroep__parameter__contains=Doelgroep2)
                )
            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Doelgroep__parameter__contains=Doelgroep3)
                )
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(AED=True))
                )
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(Smarthome=True))
                )
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(EntreeUpgrade=True))
                )
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(Pakketdient=True))
                )
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(JamesConcept=True))
                )

            basic_PVE = basic_PVE.order_by("id")
            # make pdf
            parameters = []
            if Bouwsoort1:
                parameters += (f"{Bouwsoort1.parameter} (Hoofd)",)
            if Bouwsoort2:
                parameters += (f"{Bouwsoort2.parameter} (Sub)",)
            if Bouwsoort3:
                parameters += (f"{Bouwsoort3.parameter} (Sub)",)
            if TypeObject1:
                parameters += (f"{TypeObject1.parameter} (Hoofd)",)
            if TypeObject2:
                parameters += (f"{TypeObject2.parameter} (Sub)",)
            if TypeObject3:
                parameters += (f"{TypeObject3.parameter} (Sub)",)
            if Doelgroep1:
                parameters += (f"{Doelgroep1.parameter} (Hoofd)",)
            if Doelgroep2:
                parameters += (f"{Doelgroep2.parameter} (Sub)",)
            if Doelgroep3:
                parameters += (f"{Doelgroep3.parameter} (Sub)",)

            date = datetime.datetime.now()
            fileExt = "%s%s%s%s%s%s" % (
                date.strftime("%H"),
                date.strftime("%M"),
                date.strftime("%S"),
                date.strftime("%d"),
                date.strftime("%m"),
                date.strftime("%Y"),
            )
            filename = f"PvE-{fileExt}"
            zipFilename = f"PvE_Compleet-{fileExt}"
            pdfmaker = writePdf.PDFMaker()
            opmerkingen = {}
            bijlagen = {}
            reacties = {}
            reactiebijlagen = {}

            pdfmaker.makepdf(
                filename,
                basic_PVE,
                versie.id,
                opmerkingen,
                bijlagen,
                reacties,
                reactiebijlagen,
                parameters,
                [],
            )

            # get bijlagen
            bijlagen = [item for item in basic_PVE if item.bijlage]
            if bijlagen:
                zipmaker = createBijlageZip.ZipMaker()
                zipmaker.makeZip(zipFilename, filename, bijlagen)
            else:
                zipFilename = False

            # and render the result page
            context = {}
            context["itemsPVE"] = basic_PVE
            context["filename"] = filename
            context["zipFilename"] = zipFilename
            return render(request, "PVEResult_syn.html", context)
        else:
            messages.warning(request, "Vul de verplichte keuzes in.")

    form = forms.PVEParameterForm()
    form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()

    # if get method, just render the empty form
    context = {}
    context["form"] = form
    context["versie"] = versie
    return render(request, "GeneratePVE_syn.html", context)


@login_required
def download_pve_overview(request):
    projects = Project.objects.filter(
        permitted__username__contains=request.user.username
    ).distinct()

    context = {}
    context["projects"] = projects
    return render(request, "downloadPveOverview_syn.html", context)


@login_required
def download_pve(request, pk):
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    project = get_object_or_404(Project, id=pk)
    versie = project.pve_versie

    basic_PVE = (
        models.PVEItem.objects.select_related("hoofdstuk")
        .select_related("paragraaf")
        .filter(projects__id__contains=pk)
        .order_by("id")
    )

    # make pdf
    parameters = []

    parameters += (f"Project: {project.naam}",)

    date = datetime.datetime.now()

    fileExt = "%s%s%s%s%s%s" % (
        date.strftime("%H"),
        date.strftime("%M"),
        date.strftime("%S"),
        date.strftime("%d"),
        date.strftime("%m"),
        date.strftime("%Y"),
    )

    filename = f"PvE-{fileExt}"
    zipFilename = f"PvE_Compleet-{fileExt}"

    # Opmerkingen in kleur naast de regels
    opmerkingen = {}
    bijlagen = {}
    reacties = {}
    reactiebijlagen = {}
    kostenverschil = 0

    comments = (
        PVEItemAnnotation.objects.select_related("item")
        .select_related("status")
        .select_related("gebruiker")
        .filter(project=project)
    )

    for opmerking in comments:
        opmerkingen[opmerking.item.id] = opmerking
        if opmerking.kostenConsequenties:
            kostenverschil += opmerking.kostenConsequenties
        if opmerking.bijlage:
            bijlage = BijlageToAnnotation.objects.get(ann=opmerking)
            bijlagen[opmerking.item.id] = bijlage

    replies = (
        CommentReply.objects.select_related("gebruiker")
        .select_related("onComment")
        .select_related("onComment__item")
        .filter(commentphase__project=project)
    )

    for reply in replies:
        if reply.onComment.item.id in reacties.keys():
            reacties[reply.onComment.item.id].append(reply)
        else:
            reacties[reply.onComment.item.id] = [reply]

        if reply.bijlage:
            bijlage = BijlageToReply.objects.get(reply=reply)
            reactiebijlagen[reply.id] = bijlage

    geaccepteerde_regels_ids = []

    if project.frozenLevel > 0:
        commentphase = FrozenComments.objects.filter(
            project=project, level=project.frozenLevel
        ).first()
        geaccepteerde_regels_ids = [
            accepted_id.id for accepted_id in commentphase.accepted_comments.all()
        ]

    pdfmaker = writePdf.PDFMaker()

    # verander CONCEPT naar DEFINITIEF als het project volbevroren is.
    if project.fullyFrozen == True:
        pdfmaker.Topright = "DEFINITIEF"
    else:
        pdfmaker.Topright = f"CONCEPT SNAPSHOT {date.strftime('%d')}-{date.strftime('%m')}-{date.strftime('%Y')}"
        pdfmaker.TopRightPadding = 75

    pdfmaker.kostenverschil = kostenverschil
    pdfmaker.makepdf(
        filename,
        basic_PVE,
        versie.id,
        opmerkingen,
        bijlagen,
        reacties,
        reactiebijlagen,
        parameters,
        geaccepteerde_regels_ids,
    )

    # get bijlagen
    bijlagen = [item for item in basic_PVE if item.bijlage]

    if BijlageToAnnotation.objects.filter(ann__project=project).exists():
        bijlagen = BijlageToAnnotation.objects.filter(ann__project=project)
        for item in bijlagen:
            bijlagen.append(item)

    if BijlageToReply.objects.filter(reply__onComment__project=project).exists():
        replybijlagen = BijlageToReply.objects.filter(reply__onComment__project=project)
        for bijlage in replybijlagen:
            bijlagen.append(bijlage)

    if bijlagen:
        zipmaker = createBijlageZip.ZipMaker()
        zipmaker.makeZip(zipFilename, filename, bijlagen)
    else:
        zipFilename = False

    # and render the result page
    context = {}
    context["itemsPVE"] = basic_PVE
    context["filename"] = filename
    context["zipFilename"] = zipFilename
    context["project"] = project
    return render(request, "PVEResult_syn.html", context)


@login_required(login_url="login_syn")
def ViewProjectOverview(request):
    projects = Project.objects.filter(
        belegger__naam="Syntrus", permitted__username__contains=request.user.username
    ).distinct()

    context = {}
    context["projects"] = projects
    return render(request, "MyProjecten_syn.html", context)


@login_required(login_url="login_syn")
def ViewProject(request, pk):
    if not Project.objects.filter(
        id=pk,
        belegger__naam="Syntrus",
        permitted__username__contains=request.user.username,
    ).exists():
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, id=pk)

    medewerkers = [medewerker.username for medewerker in project.permitted.all()]

    context = {}

    if project.frozenLevel == 0:
        pve_item_count = models.PVEItem.objects.filter(
            projects__id__contains=pk
        ).count()
        comment_count = PVEItemAnnotation.objects.filter(project__id=pk).count()
        context["pve_item_count"] = pve_item_count
        context["comment_count"] = comment_count
        if project.pveconnected:
            context["done_percentage"] = int(100 * (comment_count) / pve_item_count)
        else:
            context["done_percentage"] = 0

    if project.frozenLevel >= 1:
        frozencomments_accepted = (
            FrozenComments.objects.filter(project__id=project.id)
            .order_by("-level")
            .first()
            .accepted_comments.count()
        )
        frozencomments_todo = (
            FrozenComments.objects.filter(project__id=project.id)
            .order_by("-level")
            .first()
            .todo_comments.count()
        )
        frozencomments_total = (
            frozencomments_todo
            + frozencomments_accepted
            + FrozenComments.objects.filter(Q(project__id=project.id))
            .order_by("-level")
            .first()
            .comments.count()
        )
        context["frozencomments_accepted"] = frozencomments_accepted
        context["frozencomments_todo"] = frozencomments_todo
        context["frozencomments_total"] = frozencomments_total
        context["frozencomments_percentage"] = int(
            100 * (frozencomments_accepted) / frozencomments_total
        )

        freeze_ready = False
        if frozencomments_total == frozencomments_accepted:
            freeze_ready = True

        context["freeze_ready"] = freeze_ready

    context["project"] = project
    context["medewerkers"] = medewerkers
    return render(request, "ProjectPagina_syn.html", context)


@login_required(login_url="login_syn")
def AddCommentOverview(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user).exists():
        projects = Project.objects.filter(permitted__username__contains=request.user)
        context["projects"] = projects

    return render(request, "plusOpmerkingOverview_syn.html", context)


@login_required(login_url="login_syn")
def MyComments(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user != project.projectmanager:
        return render(request, "404_syn.html")

        # multiple forms
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("item_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(
                dict(
                    item_id=item_id,
                    annotation=opmrk,
                    status=status,
                    init_accepted=init_accepted,
                    kostenConsequenties=kosten,
                )
            )
            for item_id, opmrk, status, init_accepted, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("init_accepted"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]
        for form in ann_forms:
            # true comment if either comment or voldoet
            if form.cleaned_data["status"] or form.cleaned_data["init_accepted"]:
                ann = PVEItemAnnotation.objects.filter(
                    item=models.PVEItem.objects.filter(
                        id=form.cleaned_data["item_id"]
                    ).first()
                ).first()
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(
                    id=form.cleaned_data["item_id"]
                ).first()
                if form.cleaned_data["annotation"]:
                    ann.annotation = form.cleaned_data["annotation"]
                if form.cleaned_data["status"]:
                    ann.status = form.cleaned_data["status"]
                # bijlage uit cleaned data halen en opslaan!
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                ann.save()

        return redirect("mijnopmerkingen_syn", pk=project.id)

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    comments = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("-datum")
    for comment in comments:
        ann_forms.append(
            forms.PVEItemAnnotationForm(
                initial={
                    "item_id": comment.item.id,
                    "annotation": comment.annotation,
                    "status": comment.status,
                    "init_accepted": comment.init_accepted,
                    "kostenConsequenties": comment.kostenConsequenties,
                }
            )
        )

        form_item_ids.append(comment.item.id)

    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = comments
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).count()
    return render(request, "MyComments.html", context)


@login_required(login_url="login_syn")
def MyCommentsDelete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    aantal_opmerkingen_gedaan = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).count()

    context = {}
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    return render(request, "MyCommentsDelete.html", context)


@login_required(login_url="login_syn")
def deleteAnnotationPve(request, project_id, ann_id):
    # check if project exists
    project = get_object_or_404(Project, id=project_id)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=project_id, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(
        id=ann_id, gebruiker=request.user
    ).exists():
        raise Http404("404")

    comment = PVEItemAnnotation.objects.filter(id=ann_id).first()

    if request.method == "POST":
        messages.warning(request, f"Opmerking van {comment.project} verwijderd.")
        comment.delete()
        return HttpResponseRedirect(
            reverse("mijnopmerkingendelete_syn", args=(project.id,))
        )

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["comment"] = comment
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten

    return render(request, "deleteAnnotationModal_syn.html", context)


@login_required(login_url="login_syn")
def AddAnnotationAttachment(request, projid, annid):
    project = get_object_or_404(Project, pk=projid)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    annotation = PVEItemAnnotation.objects.filter(project=project, pk=annid).first()
    comments = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")

    if annotation.gebruiker != request.user:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.BijlageToAnnotationForm(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["bijlage"]:
                form.save()
                annotation.bijlage = True
                annotation.save()
                return redirect("mijnopmerkingen_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    form = BijlageToAnnotationForm(initial={"ann": annotation})
    context["annotation"] = annotation
    context["form"] = form
    context["project"] = project
    context["comments"] = comments
    return render(request, "addBijlagetoAnnotation_syn.html", context)


@login_required(login_url="login_syn")
def VerwijderAnnotationAttachment(request, projid, annid):
    # check if project exists
    project = get_object_or_404(Project, pk=projid)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=projid, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(
        id=annid, gebruiker=request.user
    ).exists():
        raise Http404("404")

    comment = PVEItemAnnotation.objects.filter(id=annid).first()
    attachment = BijlageToAnnotation.objects.filter(ann_id=annid).first()

    if request.method == "POST":
        messages.warning(request, f"Bijlage van {attachment.ann} verwijderd.")
        comment.bijlage = False
        comment.save()
        attachment.delete()
        return HttpResponseRedirect(
            reverse("mijnopmerkingendelete_syn", args=(project.id,))
        )

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["comment"] = comment
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten

    return render(request, "deleteAttachmentAnnotation_syn.html", context)


@login_required(login_url="login_syn")
def DownloadAnnotationAttachment(request, projid, annid):
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    item = BijlageToAnnotation.objects.filter(
        ann__project__id=projid, ann__id=annid
    ).first()
    expiration = 10000
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=settings.AWS_S3_REGION_NAME,
        config=botocore.client.Config(
            signature_version=settings.AWS_S3_SIGNATURE_VERSION
        ),
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": str(item.bijlage)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)


@login_required(login_url="login_syn")
def AllComments(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    if PVEItemAnnotation.objects.filter(project=project):
        gebruiker = PVEItemAnnotation.objects.filter(project=project).first()
        auteur = gebruiker.gebruiker
        context["gebruiker"] = gebruiker
        context["comments"] = PVEItemAnnotation.objects.filter(
            project=project
        ).order_by("-datum")

    context["items"] = models.PVEItem.objects.filter(
        projects__id__contains=project.id
    ).order_by("id")
    context["project"] = project
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = PVEItemAnnotation.objects.filter(
        project=project
    ).count()
    return render(request, "AllCommentsOfProject_syn.html", context)


@login_required(login_url="login_syn")
def AddComment(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if request.user != project.projectmanager:
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if not models.PVEItem.objects.filter(projects__id__contains=pk).exists():
        return render(request, "404_syn.html")

    # multiple forms
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("item_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(
                dict(
                    item_id=item_id,
                    annotation=opmrk,
                    status=status,
                    kostenConsequenties=kosten,
                )
            )
            for item_id, opmrk, status, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        for form in ann_forms:
            # true comment if either status or voldoet
            if form.cleaned_data["status"]:
                if PVEItemAnnotation.objects.filter(
                    item=models.PVEItem.objects.filter(
                        id=form.cleaned_data["item_id"]
                    ).first()
                ):
                    ann = PVEItemAnnotation.objects.filter(
                        item=models.PVEItem.objects.filter(
                            id=form.cleaned_data["item_id"]
                        ).first()
                    ).first()
                else:
                    ann = PVEItemAnnotation()
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(
                    id=form.cleaned_data["item_id"]
                ).first()

                if form.cleaned_data["annotation"]:
                    ann.annotation = form.cleaned_data["annotation"]
                if form.cleaned_data["status"]:
                    ann.status = form.cleaned_data["status"]
                # bijlage uit cleaned data halen en opslaan!
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                ann.save()
        messages.warning(
            request,
            "Opmerkingen opgeslagen. U kunt later altijd terug naar deze pagina of naar de opmerkingpagina om uw opmerkingen te bewerken voordat u ze opstuurt.",
        )
        # remove duplicate entries
        return redirect("mijnopmerkingen_syn", pk=project.id)

    items = (
        models.PVEItem.objects.select_related("hoofdstuk")
        .select_related("paragraaf")
        .filter(projects__id__contains=pk)
        .order_by("id")
    )
    annotations = {}

    for annotation in (
        PVEItemAnnotation.objects.select_related("item")
        .select_related("status")
        .filter(Q(project=project) & Q(gebruiker=request.user))
    ):
        annotations[annotation.item] = annotation

    ann_forms = []
    hoofdstuk_ordered_items = {}

    for item in items:
        opmerking = None

        # create forms
        if item not in annotations.keys():
            ann_forms.append(forms.PVEItemAnnotationForm(initial={"item_id": item.id}))
        else:
            opmerking = annotations[item]
            ann_forms.append(
                forms.PVEItemAnnotationForm(
                    initial={
                        "item_id": opmerking.item.id,
                        "annotation": opmerking.annotation,
                        "status": opmerking.status,
                        "kostenConsequenties": opmerking.kostenConsequenties,
                    }
                )
            )

        # create ordered items
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                hoofdstuk_ordered_items[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk]:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(
                        [item, item.id, opmerking.status, item.bijlage]
                    )
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(
                        [item, item.id, None, item.bijlage]
                    )
            else:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [
                        [item, item.id, opmerking.status, item.bijlage]
                    ]
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [
                        [item, item.id, None, item.bijlage]
                    ]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk].append(
                        [item, item.id, opmerking.status, item.bijlage]
                    )
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk].append(
                        [item, item.id, None, item.bijlage]
                    )
            else:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [
                        [item, item.id, opmerking.status, item.bijlage]
                    ]
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [
                        [item, item.id, None, item.bijlage]
                    ]

    # easy entrance to item ids
    form_item_ids = [item.id for item in items]

    aantal_opmerkingen_gedaan = len(annotations.keys())

    if aantal_opmerkingen_gedaan < items.count():
        progress = "niet_klaar"
    else:
        progress = "klaar"

    context["forms"] = ann_forms
    context["items"] = items
    context["progress"] = progress
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    context["form_item_ids"] = form_item_ids
    context["hoofdstuk_ordered_items"] = hoofdstuk_ordered_items
    context["project"] = project
    return render(request, "plusOpmerking_syn.html", context)


@login_required(login_url="login_syn")
def AddProject(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.StartProjectForm(request.POST)

        if form.is_valid():
            form.save()

            project = Project.objects.all().order_by("-id")[0]
            project.permitted.add(request.user)
            project.belegger = Beleggers.objects.filter(naam="Syntrus").first()

            geolocator = Nominatim(user_agent="tamesbpvegenerator")
            if (
                "city"
                in geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}")
                .raw["address"]
                .keys()
            ):
                project.plaatsnamen = geolocator.reverse(
                    f"{project.plaats.y}, {project.plaats.x}"
                ).raw["address"]["city"]
            else:
                project.plaatsnamen = geolocator.reverse(
                    f"{project.plaats.y}, {project.plaats.x}"
                ).raw["address"]["town"]

            project.save()
            return redirect("connectpve_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = StartProjectForm()
    return render(request, "plusProject_syn.html", context)


@login_required(login_url="login_syn")
def InviteUsersToProject(request, pk):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    project = Project.objects.filter(id=pk).first()

    if request.method == "POST":
        form = forms.InviteProjectStartForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            organisaties = form.cleaned_data["organisaties"]
            projectmanager = form.cleaned_data["projectmanager"]
            permitted = form.cleaned_data["permitted"]

            project.projectmanager = projectmanager

            for organisatie in organisaties:
                project.organisaties.add(organisatie)

            for permit in permitted:
                project.permitted.add(permit)

            project.save()

            if organisaties:
                organisaties = [organisatie for organisatie in organisaties]
                gebruikers = []

                for organisatie in organisaties:
                    gebruikerSet = [user for user in organisatie.gebruikers.all()]
                    gebruikers.append(gebruikerSet)
                    organisatie.projecten.add(project)
                    organisatie.save()

                for gebruiker in gebruikers:
                    send_mail(
                        f"Syntrus Projecten - Uitnodiging voor project {project}",
                        f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van Syntrus.
                        
                        U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}""",
                        "admin@pvegenerator.net",
                        [f"{gebruiker.email}"],
                        fail_silently=False,
                    )

            if projectmanager:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {project}",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor het project { project } van Syntrus.
                    
                    U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/project/{project.id}""",
                    "admin@pvegenerator.net",
                    [f"{projectmanager.email}"],
                    fail_silently=False,
                )

            if permitted:
                gebruikers = [user for user in permitted]

                for gebruiker in gebruikers:
                    send_mail(
                        f"Syntrus Projecten - Uitnodiging voor project {project}",
                        f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van Syntrus.
                        
                        U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}""",
                        "admin@pvegenerator.net",
                        [f"{gebruiker.email}"],
                        fail_silently=False,
                    )

            return redirect("connectpve_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
    form = forms.InviteProjectStartForm()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, "InviteUsersToProject_syn.html", context)


@login_required(login_url="login_syn")
def ConnectPVE(request, pk):
    allowed_users = ["B", "SB", "SOG"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, pk=pk)

    # we get the active version of the pve based on what is active right now
    versie = models.ActieveVersie.objects.get(belegger__naam="Syntrus").versie

    if project.pveconnected:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.PVEParameterForm(request.POST)
        form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()

        # check whether it's valid:
        if form.is_valid():
            # get parameters, find all pveitems with that
            (
                Bouwsoort1,
                TypeObject1,
                Doelgroep1,
                Bouwsoort2,
                TypeObject2,
                Doelgroep2,
                Bouwsoort3,
                TypeObject3,
                Doelgroep3,
                Smarthome,
                AED,
                EntreeUpgrade,
                Pakketdient,
                JamesConcept,
            ) = (
                form.cleaned_data["Bouwsoort1"],
                form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"],
                form.cleaned_data["Bouwsoort2"],
                form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"],
                form.cleaned_data["Bouwsoort3"],
                form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"],
                form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"],
                form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"],
                form.cleaned_data["JamesConcept"],
            )

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(
                Q(versie=versie) & Q(basisregel=True)
            )
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.filter(
                    versie=versie, Bouwsoort__parameter__contains=Bouwsoort1
                )
            )
            project.bouwsoort1 = models.Bouwsoort.objects.filter(
                versie=versie, parameter=Bouwsoort1
            ).first()

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, Bouwsoort__parameter__contains=Bouwsoort2
                    )
                )
                project.bouwsoort2 = models.Bouwsoort.objects.filter(
                    versie=versie, parameter=Bouwsoort2
                ).first()

            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, Bouwsoort__parameter__contains=Bouwsoort3
                    )
                )
                project.bouwsoort2 = models.Bouwsoort.objects.filter(
                    versie=versie, parameter=Bouwsoort3
                ).first()

            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, TypeObject__parameter__contains=TypeObject1
                    )
                )
                project.typeObject1 = models.TypeObject.objects.filter(
                    versie=versie, parameter=TypeObject1
                ).first()

            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, TypeObject__parameter__contains=TypeObject2
                    )
                )
                project.typeObject2 = models.TypeObject.objects.filter(
                    versie=versie, parameter=TypeObject2
                ).first()

            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, TypeObject__parameter__contains=TypeObject3
                    )
                )
                project.typeObject2 = models.TypeObject.objects.filter(
                    versie=versie, parameter=TypeObject3
                ).first()

            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, Doelgroep__parameter__contains=Doelgroep1
                    )
                )
                project.doelgroep1 = models.Doelgroep.objects.filter(
                    versie=versie, parameter=Doelgroep1
                ).first()

            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, Doelgroep__parameter__contains=Doelgroep2
                    )
                )
                project.doelgroep2 = models.Doelgroep.objects.filter(
                    versie=versie, parameter=Doelgroep2
                ).first()

            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie=versie, Doelgroep__parameter__contains=Doelgroep3
                    )
                )
                project.doelgroep2 = models.Doelgroep.objects.filter(
                    versie=versie, parameter=Doelgroep3
                ).first()
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(versie=versie) & Q(AED=True))
                )
                project.AED = True

            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(versie=versie) & Q(Smarthome=True))
                )
                # add the parameter to the project
                project.Smarthome = True

            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(versie=versie) & Q(EntreeUpgrade=True)
                    )
                )
                project.EntreeUpgrade = True

            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(versie=versie) & Q(Pakketdient=True)
                    )
                )
                project.Pakketdient = True

            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(versie=versie) & Q(JamesConcept=True)
                    )
                )
                project.JamesConcept = True

            # add the project to all the pve items
            for item in basic_PVE:
                item.projects.add(project)

            # succesfully connected, save the project
            project.pveconnected = True

            # set current pve version to project
            project.pve_versie = versie
            project.save()
            return redirect("projectenaddprojmanager_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
    form = forms.PVEParameterForm()
    form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()

    context = {}
    context["form"] = form
    context["project"] = project
    context["versie"] = versie
    return render(request, "ConnectPVE_syn.html", context)


@login_required(login_url="login_syn")
def AddAccount(request):
    allowed_users = ["B", "SB", "SOG"]
    staff_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    if request.method == "POST":
        # get user entered form
        if request.user.type_user in staff_users:
            form = forms.PlusAccountForm(request.POST)
        else:
            form = forms.KoppelDerdeUserForm(request.POST)
        # check validity
        if form.is_valid():
            invitation = Invitation()
            invitation.inviter = request.user
            invitation.invitee = form.cleaned_data["invitee"]
            invitation.rang = form.cleaned_data["rang"]

            if form.cleaned_data["project"]:
                invitation.project = form.cleaned_data["project"]
            if form.cleaned_data["organisatie"]:
                invitation.organisatie = form.cleaned_data["organisatie"]

            # Als syntrus beheerder invitatie doet kan hij ook rang geven (projectmanager/derde)
            manager = False

            if request.user.type_user in staff_users:
                if form.cleaned_data["rang"] == "SOG":
                    manager = True

            expiry_length = 10
            expire_date = timezone.now() + timezone.timedelta(expiry_length)
            invitation.expires = expire_date
            invitation.key = secrets.token_urlsafe(30)
            invitation.save()
            project = form.cleaned_data["project"]

            if manager:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor de PvE tool",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor een of meerdere projecten van Syntrus.
                    
                    Klik op de uitnodigingslink om rechtstreeks de tool in te gaan.
                    Link: https://pvegenerator.net/syntrus/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    "admin@pvegenerator.net",
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )
            else:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor de PvE tool",
                    f"""{ request.user } nodigt u uit voor het commentaar leveren en het checken van het Programma van Eisen voor een of meerdere projecten van Syntrus.
                    
                    Klik op de uitnodigingslink om rechtstreeks de tool in te gaan.
                    Link: https://pvegenerator.net/syntrus/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    "admin@pvegenerator.net",
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )

            messages.warning(
                request,
                f"Uitnodiging verstuurd naar { form.cleaned_data['invitee'] }. De uitnodiging zal verlopen in { expiry_length } dagen.)",
            )
            return redirect("managewerknemers_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    projecten = Project.objects.filter(
        permitted__username__contains=request.user.username
    )

    if request.user.type_user in staff_users:
        form = forms.PlusAccountForm()
    else:
        form = forms.KoppelDerdeUserForm()

    # set projects to own
    form.fields["project"].queryset = projecten
    context = {}
    context["form"] = form

    if request.user.type_user in staff_users:
        return render(request, "plusAccount_syn.html", context)
    else:
        return render(request, "plusDerde_syn.html", context)


@login_required(login_url="login_syn")
def AddUserOrganisatie(request, pk):
    allowed_users = ["B", "SB"]
    staff_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")
    if not Organisatie.objects.filter(id=pk):
        return render(request, "404_syn.html")

    organisatie = Organisatie.objects.filter(id=pk).first()
    organisaties = Organisatie.objects.all()

    if request.method == "POST":
        # get user entered form
        form = forms.AddUserToOrganisatieForm(request.POST)

        # check validity
        if form.is_valid():
            werknemer = form.cleaned_data["werknemer"]
            organisatie.gebruikers.add(werknemer)

            # add new user to all projects the organisation works with
            projects = organisatie.projecten.all()

            for project in projects:
                if werknemer not in project.permitted.all():
                    project.permitted.add(werknemer)
                    project.save()

            organisatie.save()

            send_mail(
                f"Syntrus Projecten - Toegevoegd aan organisatie {organisatie.naam}",
                f"""{ request.user } heeft u toegevoegd aan de organisatie {organisatie.naam}.
                
                Een organisatie kan toegevoegd worden aan projecten en werknemers krijgen dan automatisch toegang tot deze projecten.
                U kunt uw huidige projecten bekijken bij https://pvegenerator.net/syntrus/projects""",
                "admin@pvegenerator.net",
                [f"{werknemer.email}"],
                fail_silently=False,
            )
            return redirect("manageorganisaties_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    form = forms.AddUserToOrganisatieForm()

    context = {}
    context["form"] = form
    context["pk"] = pk
    context["organisatie"] = organisatie
    context["organisaties"] = organisaties
    return render(request, "organisatieAddUser.html", context)


def AcceptInvite(request, key):
    if not key or not Invitation.objects.filter(key=key):
        return render(request, "404_syn.html")

    invitation = Invitation.objects.filter(key=key).first()

    if utc.localize(datetime.datetime.now()) > invitation.expires:
        return render(request, "404verlopen_syn.html")

    if request.method == "POST":
        form = AcceptInvitationForm(request.POST)

        if form.is_valid():
            # strip the email by its first part to automatically create a username
            sep = "@"
            username = invitation.invitee.split(sep, 1)[0]
            user = CustomUser.objects.create_user(
                username, password=form.cleaned_data["password1"]
            )
            user.email = invitation.invitee
            if invitation.organisatie:
                user.organisatie = invitation.organisatie
            user.save()

            user = authenticate(
                request, username=username, password=form.cleaned_data["password1"]
            )

            if invitation.rang:
                user.type_user = invitation.rang
                user.save()

            if invitation.project:
                project = invitation.project
                project.permitted.add(user)
                project.save()

                if invitation.rang:
                    if invitation.rang == "SOG":
                        project.projectmanager = user
                        project.save()

            if invitation.organisatie:
                organisatie = invitation.organisatie
                organisatie.gebruikers.add(user)
                organisatie.save()

            invitation.delete()

            send_mail(
                f"Syntrus Projecten - Uw Logingegevens",
                f"""Reeds heeft u zich aangemeld bij de PvE tool.
                Voor het vervolgens inloggen op de tool is uw gebruikersnaam: {user.username}
                en het wachtwoord wat u heeft aangegeven bij het aanmelden.""",
                "admin@pvegenerator.net",
                [f"{invitation.invitee}"],
                fail_silently=False,
            )
            if user is not None:
                login(request, user)
                return redirect("viewprojectoverview_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    return render(request, "acceptInvitation_syn.html", context)


@login_required(login_url="login_syn")
def FirstFreeze(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.projectmanager:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            if form.cleaned_data["confirm"]:
                # freeze opmerkingen op niveau 1
                project.frozenLevel = 1
                project.save()

                # create new frozen comments and the level to 1
                frozencomments = FrozenComments()
                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()
                changed_comments = (
                    PVEItemAnnotation.objects.select_related("item")
                    .filter(Q(project=project))
                    .all()
                )

                changed_items_ids = [comment.item.id for comment in changed_comments]
                unchanged_items = models.PVEItem.objects.filter(
                    projects__id__contains=pk
                ).exclude(id__in=changed_items_ids)
                # add all initially changed comments to it
                for comment in changed_comments:
                    frozencomments.comments.add(comment)

                # create todo pveannotations for ignored items, change to bulk_create for optimization
                for item in unchanged_items:
                    comment = PVEItemAnnotation()
                    comment.project = project
                    comment.item = item
                    comment.gebruiker = request.user
                    comment.init_accepted = True
                    comment.save()

                    frozencomments.todo_comments.add(comment)

                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()

                allprojectusers = project.permitted.all()
                filteredDerden = [
                    user.email for user in allprojectusers if user.type_user == "SD"
                ]
                send_mail(
                    f"Syntrus Projecten - Uitnodiging opmerkingscheck voor project {project}",
                    f"""{ request.user } heeft de initiele statussen van de PvE-regels ingevuld en nodigt u uit deze te checken voor het project { project } van Syntrus.
                    
                    Klik op de link om rechtstreeks de statussen langs te gaan.
                    Link: https://pvegenerator.net/syntrus/project/{project.id}/check
                    """,
                    "admin@pvegenerator.net",
                    filteredDerden,
                    fail_silently=False,
                )

                messages.warning(
                    request,
                    f"Uitnodiging voor opmerkingen checken verstuurd naar de derden via email.",
                )
                return redirect("viewproject_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = FirstFreezeForm(request.POST)
    context["pk"] = pk
    context["project"] = project
    return render(request, "FirstFreeze.html", context)


@login_required(login_url="login_syn")
def CheckComments(request, proj_id):
    context = {}

    # get the project
    project = get_object_or_404(Project, pk=proj_id)

    # check first if user is permitted to the project
    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # get the frozencomments and the level
    if not FrozenComments.objects.filter(project__id=proj_id):
        return render(request, "404_syn.html")

    # get the highest ID of the frozencomments phases; the current phase
    frozencomments = (
        FrozenComments.objects.filter(project__id=proj_id).order_by("-level").first()
    )

    # uneven level = turn of SD, even level = turn of SOG
    if (frozencomments.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user != "SD":
            return render(request, "404_syn.html")
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != "SOG":
            return render(request, "404_syn.html")

    # the POST method
    if request.method == "POST":
        comment_id_list = [number for number in request.POST.getlist("comment_id")]

        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.CommentReplyForm(
                dict(
                    comment_id=comment_id,
                    annotation=opmrk,
                    status=status,
                    accept=accept,
                    kostenConsequenties=kostenConsequenties,
                )
            )
            for comment_id, opmrk, status, accept, kostenConsequenties in zip(
                request.POST.getlist("comment_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("accept"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        for form in ann_forms:
            if (
                form.cleaned_data["status"]
                or form.cleaned_data["accept"] == "True"
                or form.cleaned_data["annotation"]
                or form.cleaned_data["kostenConsequenties"]
            ):
                # get the original comment it was on
                originalComment = PVEItemAnnotation.objects.filter(
                    id=form.cleaned_data["comment_id"]
                ).first()

                if CommentReply.objects.filter(
                    onComment__id=form.cleaned_data["comment_id"],
                    commentphase=frozencomments,
                    gebruiker=request.user,
                ).exists():
                    ann = CommentReply.objects.filter(
                        onComment__id=form.cleaned_data["comment_id"],
                        commentphase=frozencomments,
                        gebruiker=request.user,
                    ).first()
                else:
                    ann = CommentReply()
                    ann.commentphase = frozencomments
                    ann.gebruiker = request.user
                    ann.onComment = originalComment

                if form.cleaned_data["status"]:
                    ann.status = form.cleaned_data["status"]
                if form.cleaned_data["annotation"]:
                    ann.comment = form.cleaned_data["annotation"]
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                if form.cleaned_data["accept"] == "True":
                    ann.accept = True
                else:
                    ann.accept = False
                ann.save()

        messages.warning(
            request,
            "Opmerkingen opgeslagen. U kunt later altijd terug naar deze pagina of naar de opmerkingpagina om uw opmerkingen te bewerken voordat u ze opstuurt.",
        )
        # redirect to project after posting replies for now
        return redirect("myreplies_syn", pk=project.id)

    # the GET method
    non_accepted_comments = (
        frozencomments.comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )
    accepted_comments = (
        frozencomments.accepted_comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )
    todo_comments = (
        frozencomments.todo_comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )

    # create the forms
    ann_forms_accept = make_ann_forms(accepted_comments, frozencomments)
    ann_forms_non_accept = make_ann_forms(non_accepted_comments, frozencomments)
    ann_forms_todo = make_ann_forms(todo_comments, frozencomments)

    # order items for the template
    hoofdstuk_ordered_items_non_accept = order_comments_for_commentcheck(
        non_accepted_comments, proj_id
    )
    hoofdstuk_ordered_items_accept = order_comments_for_commentcheck(
        accepted_comments, proj_id
    )
    hoofdstuk_ordered_items_todo = order_comments_for_commentcheck(
        todo_comments, proj_id
    )

    context["items"] = models.PVEItem.objects.filter(
        projects__id__contains=project.id
    ).order_by("id")
    context["project"] = project
    context["accepted_comments"] = accepted_comments
    context["non_accepted_comments"] = non_accepted_comments
    context["todo_comments"] = todo_comments
    context["forms_accept"] = ann_forms_accept
    context["forms_non_accept"] = ann_forms_non_accept
    context["forms_todo"] = ann_forms_todo
    context["hoofdstuk_ordered_items_non_accept"] = hoofdstuk_ordered_items_non_accept
    context["hoofdstuk_ordered_items_accept"] = hoofdstuk_ordered_items_accept
    context["hoofdstuk_ordered_items_todo"] = hoofdstuk_ordered_items_todo
    context["totale_kosten"] = PVEItemAnnotation.objects.filter(
        project=project
    ).aggregate(Sum("kostenConsequenties"))["kostenConsequenties__sum"]
    return render(request, "CheckComments_syn.html", context)


def order_comments_for_commentcheck(comments_entry, proj_id):
    # loop for reply ordering for the pagedesign
    hoofdstuk_ordered_items_non_accept = {}
    made_on_comments = {}
    commentreplies = (
        CommentReply.objects.select_related("onComment")
        .filter(onComment__project__id=proj_id)
        .all()
    )

    for reply in commentreplies:
        if reply.onComment in made_on_comments.keys():
            made_on_comments[reply.onComment].append([reply])
        else:
            made_on_comments[reply.onComment] = [reply]

    for comment in comments_entry:
        last_accept = False
        # set the PVEItem from the comment
        item = comment.item

        temp_bijlage_list = []
        temp_commentbulk_list_non_accept = []
        string = ""

        if comment.status:
            string = f"Status: {comment.status}"

        # add all replies to this comment
        if comment in made_on_comments.keys():
            commentreplys = CommentReply.objects.filter(Q(onComment=comment)).all()
            last_reply = commentreplys.order_by("-datum").first()

            if last_reply.status != None:
                string = f"Nieuwe Status: {last_reply.status}"

            if last_reply.accept == True:
                last_accept = True

            for reply in commentreplys:
                temp_commentbulk_list_non_accept.append(reply.comment)

                if reply.bijlage:
                    temp_bijlage_list.append(reply.id)

            string += f", Opmerkingen: "

            comment_added = False
            for comment_str in temp_commentbulk_list_non_accept:
                if comment_str:
                    string += f""""{ comment_str }", """
                    comment_added = True

            if not comment_added:
                string = string[:-15]
            else:
                string = string[:-2]

        # sort
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items_non_accept.keys():
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items_non_accept[item.hoofdstuk]:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk][
                    item.paragraaf
                ].append(
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        item.bijlage,
                    ]
                )
            else:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk][item.paragraaf] = [
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        item.bijlage,
                    ]
                ]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items_non_accept:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk].append(
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        item.bijlage,
                    ]
                )
            else:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk] = [
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        item.bijlage,
                    ]
                ]

    return hoofdstuk_ordered_items_non_accept


def make_ann_forms(comments, frozencomments):
    ann_forms = []
    made_on_comments = {}
    commentreplies = CommentReply.objects.select_related("onComment").filter(
        Q(commentphase=frozencomments)
    )

    for reply in commentreplies:
        made_on_comments[reply.onComment] = reply

    for comment in comments:
        # look if the persons reply already exists, for later saving
        if comment not in made_on_comments.keys():
            ann_forms.append(
                forms.CommentReplyForm(
                    initial={
                        "comment_id": comment.id,
                        "accept": "False",
                        "status": comment.status,
                    }
                )
            )
        else:
            reply = made_on_comments[comment]

            if reply.accept == True:
                ann_forms.append(
                    forms.CommentReplyForm(
                        initial={
                            "comment_id": comment.id,
                            "annotation": reply.comment,
                            "accept": "True",
                            "status": reply.status,
                            "kostenConsequenties": reply.kostenConsequenties,
                        }
                    )
                )
            else:
                ann_forms.append(
                    forms.CommentReplyForm(
                        initial={
                            "comment_id": comment.id,
                            "annotation": reply.comment,
                            "accept": "False",
                            "status": reply.status,
                            "kostenConsequenties": reply.kostenConsequenties,
                        }
                    )
                )
    return ann_forms


@login_required
def MyReplies(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )

    # multiple forms
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("comment_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.CommentReplyForm(
                dict(
                    comment_id=comment_id,
                    annotation=opmrk,
                    status=status,
                    accept=accept,
                    kostenConsequenties=kostenConsequenties,
                )
            )
            for comment_id, opmrk, status, accept, kostenConsequenties in zip(
                request.POST.getlist("comment_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("accept"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]
        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]
        for form in ann_forms:
            if (
                form.cleaned_data["accept"] == "True"
                or form.cleaned_data["status"]
                or form.cleaned_data["annotation"]
                or form.cleaned_data["kostenConsequenties"]
            ):
                # true comment if either comment or voldoet
                original_comment = PVEItemAnnotation.objects.filter(
                    id=form.cleaned_data["comment_id"]
                ).first()
                reply = CommentReply.objects.filter(
                    Q(commentphase=commentphase) & Q(onComment=original_comment)
                ).first()

                if form.cleaned_data["annotation"]:
                    reply.comment = form.cleaned_data["annotation"]

                if form.cleaned_data["status"]:
                    reply.status = form.cleaned_data["status"]

                if form.cleaned_data["kostenConsequenties"]:
                    reply.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                if form.cleaned_data["accept"] == "True":
                    reply.accept = True
                else:
                    reply.accept = False

                reply.save()

        return redirect("myreplies_syn", pk=project.id)

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    replies = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")
    for reply in replies:
        if reply.accept == True:
            ann_forms.append(
                forms.CommentReplyForm(
                    initial={
                        "comment_id": reply.onComment.id,
                        "annotation": reply.comment,
                        "status": reply.status,
                        "accept": "True",
                        "kostenConsequenties": reply.kostenConsequenties,
                    }
                )
            )
        else:
            ann_forms.append(
                forms.CommentReplyForm(
                    initial={
                        "comment_id": reply.onComment.id,
                        "annotation": reply.comment,
                        "status": reply.status,
                        "accept": "False",
                        "kostenConsequenties": reply.kostenConsequenties,
                    }
                )
            )
        form_item_ids.append(reply.onComment.id)

    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["replies"] = replies
    context["project"] = project
    context["bijlages"] = bijlages
    context["aantal_opmerkingen_gedaan"] = replies.count()
    return render(request, "MyReplies.html", context)


@login_required
def MyRepliesDelete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )
    replies = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["replies"] = replies
    context["project"] = project
    context["bijlages"] = bijlages
    context["aantal_opmerkingen_gedaan"] = replies.count()
    return render(request, "MyRepliesDelete.html", context)


@login_required
def DeleteReply(request, pk, reply_id):
    # check if project exists
    project = get_object_or_404(Project, id=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(
        id=reply_id, gebruiker=request.user
    ).exists():
        raise Http404("404")

    reply = CommentReply.objects.filter(id=reply_id).first()
    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )

    if request.method == "POST":
        messages.warning(
            request, f"Opmerking van {reply.onComment.project} verwijderd."
        )
        reply.delete()
        return HttpResponseRedirect(
            reverse("replydeleteoverview_syn", args=(project.id,))
        )

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["reply"] = reply
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=pk)
    context["replies"] = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")
    context["project"] = project
    context["bijlages"] = bijlages
    return render(request, "MyRepliesDeleteReply.html", context)


@login_required
def AddReplyAttachment(request, pk, reply_id):
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )
    reply = CommentReply.objects.filter(id=reply_id).first()
    replies = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")

    if reply.gebruiker != request.user:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.BijlageToReplyForm(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["bijlage"]:
                form.save()
                reply.bijlage = True
                reply.save()
                return redirect("myreplies_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    form = BijlageToReplyForm(initial={"reply": reply})
    context["reply"] = reply
    context["form"] = form
    context["project"] = project
    context["replies"] = replies
    return render(request, "MyRepliesAddAttachment.html", context)


@login_required
def DeleteReplyAttachment(request, pk, reply_id):
    # check if project exists
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(
        id=reply_id, gebruiker=request.user
    ).exists():
        raise Http404("404")

    reply = CommentReply.objects.filter(id=reply_id).first()
    attachment = BijlageToReply.objects.filter(reply__id=reply_id).first()
    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )

    if request.method == "POST":
        messages.warning(request, f"Bijlage verwijderd.")
        reply.bijlage = False
        reply.save()
        attachment.delete()
        return HttpResponseRedirect(
            reverse("replydeleteoverview_syn", args=(project.id,))
        )

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["reply"] = reply
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["replies"] = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")
    context["project"] = project
    context["bijlages"] = bijlages
    return render(request, "MyRepliesDeleteAttachment.html", context)


@login_required
def DownloadReplyAttachment(request, pk, reply_id):
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    item = BijlageToReply.objects.filter(reply__id=reply_id).first()
    expiration = 10000
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=settings.AWS_S3_REGION_NAME,
        config=botocore.client.Config(
            signature_version=settings.AWS_S3_SIGNATURE_VERSION
        ),
    )

    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": str(item.bijlage)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)


@login_required
def SendReplies(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            if form.cleaned_data["confirm"]:
                project.frozenLevel = project.frozenLevel + 1
                project.save()

                commentphase = (
                    FrozenComments.objects.filter(project=project)
                    .order_by("-level")
                    .first()
                )

                # create a new phase with 1 higher level
                new_phase = FrozenComments()
                new_phase.level = commentphase.level + 1
                new_phase.project = project
                new_phase.save()

                # split comments in previously accepted and non accepted
                non_accepted_comments_ids = []
                accepted_comment_ids = []
                todo_comment_ids = []
                total_comments_ids = []

                comments = (
                    CommentReply.objects.select_related("onComment")
                    .select_related("status")
                    .filter(commentphase=commentphase)
                )

                for comment in comments:
                    if comment.accept:
                        accepted_comment_ids.append(comment.onComment.id)
                    else:
                        non_accepted_comments_ids.append(comment.onComment.id)

                    # change original comments status if reply has it
                    if comment.status:
                        original_comment = comment.onComment
                        original_comment.status = comment.status
                        original_comment.save()

                    # add costs to original comment if reply has it.
                    if comment.kostenConsequenties:
                        original_comment = comment.onComment
                        original_comment.kostenConsequenties = (
                            comment.kostenConsequenties
                        )
                        original_comment.save()

                    total_comments_ids.append(comment.onComment.id)

                non_reacted_comments = PVEItemAnnotation.objects.filter(
                    project__id=pk
                ).exclude(id__in=total_comments_ids)
                for comment in non_reacted_comments:
                    if not comment.status:
                        todo_comment_ids.append(comment.id)
                    else:
                        accepted_comment_ids.append(comment.id)

                # add all the comments and divide up into accepted or non accepted or todo
                for comment in non_accepted_comments_ids:
                    new_phase.comments.add(comment)

                new_phase.save()

                for comment in accepted_comment_ids:
                    new_phase.accepted_comments.add(comment)

                new_phase.save()

                for comment in todo_comment_ids:
                    new_phase.todo_comments.add(comment)

                new_phase.save()

                if request.user.type_user == "SOG":
                    allprojectusers = project.permitted.all()
                    filteredDerden = [
                        user.email for user in allprojectusers if user.type_user == "SD"
                    ]
                    send_mail(
                        f"Syntrus Projecten - Reactie van opmerkingen op PvE ontvangen voor project {project}",
                        f"""U heeft reactie ontvangen van de opmerkingen van de projectmanager voor project {project}
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        filteredDerden,
                        fail_silently=False,
                    )
                elif request.user.type_user == "SD":
                    projectmanager = project.projectmanager

                    send_mail(
                        f"Syntrus Projecten - Reactie van opmerkingen op PvE ontvangen voor project {project}",
                        f"""U heeft reactie ontvangen van de opmerkingen van de derde partijen voor project {project}
                        
                        Klik op de link om rechtstreeks de opmerkingen te checken.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        [f"{projectmanager.email}"],
                        fail_silently=False,
                    )

                messages.warning(
                    request,
                    f"Opmerkingen doorgestuurd. De ontvanger heeft een e-mail ontvangen om uw opmerkingen te checken.",
                )
                return redirect("viewproject_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = FirstFreezeForm(request.POST)
    context["pk"] = pk
    context["project"] = project
    # set Nieuwe Statussen as the status of PVEItemannotations
    return render(request, "SendReplies.html", context)


@login_required
def FinalFreeze(request, pk):
    project = get_object_or_404(Project, id=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    commentphase = (
        FrozenComments.objects.filter(project=project).order_by("-level").first()
    )

    # check if the current commentphase has everything accepted
    if commentphase.comments or commentphase.todo_comments:
        raise Http404("404")

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            project.fullyFrozen = True
            project.save()
            
            allprojectusers = project.permitted.all()
            filteredDerden = [
                user.email for user in allprojectusers if user.type_user == "SD"
            ]
            send_mail(
                f"Syntrus Projecten - Project {project} is bevroren, download het PvE",
                f"""Alle regels in het project {project} zijn akkoord mee gegaan en de projectmanager heeft het project afgesloten.
                
                Klik op de link om het PvE met alle opmerkingen en bijlages te downloaden.
                Link: https://pvegenerator.net/syntrus/project/{project.id}/pve
                """,
                "admin@pvegenerator.net",
                filteredDerden,
                fail_silently=False,
            )
            projectmanager = project.projectmanager

            send_mail(
                f"Syntrus Projecten - Project {project} is bevroren, download het PvE",
                f"""Alle regels in het project {project} zijn akkoord mee gegaan en de projectmanager heeft het project afgesloten.
                
                Klik op de link om het PvE met alle opmerkingen en bijlages te downloaden.
                Link: https://pvegenerator.net/syntrus/project/{project.id}/pve
                """,
                "admin@pvegenerator.net",
                [f"{projectmanager.email}"],
                fail_silently=False,
            )
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context["form"] = FirstFreezeForm()
    context["pk"] = project.id
    context["project"] = project
    return render(request, "FinalFreeze.html", context)

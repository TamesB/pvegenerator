from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import formset_factory, modelformset_factory
from syntrus import forms
from project.models import Project, PVEItemAnnotation, Beleggers, BijlageToAnnotation
from users.models import Invitation, CustomUser, Organisatie
from users.forms import AcceptInvitationForm
from syntrus.models import FAQ, Room, CommentStatus, FrozenComments, CommentReply
from syntrus.forms import AddOrganisatieForm, KoppelDerdeUserForm, StartProjectForm, BijlageToAnnotationForm, FirstFreezeForm
from app import models
import datetime
from django.utils import timezone
from geopy.geocoders import Nominatim
from django.db.models import Q
from utils import writePdf
from utils import createBijlageZip
from utils.writePdf import PDFMaker
from utils.createBijlageZip import ZipMaker
import secrets
from django.core.files import storage
from django.core.mail import send_mail
import pytz
from django.conf import settings
import mimetypes
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import botocore

utc=pytz.UTC


def LoginView(request):
    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            return redirect('dashboard_syn')

    if request.method == "POST":
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            (username, password) = (
                form.cleaned_data["username"], form.cleaned_data["password"])
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard_syn')
            else:
                messages.warning(request, 'Invalid login credentials')

    # render the page
    context = {}
    context["form"] = forms.LoginForm()

    return render(request, 'login_syn.html', context)
 

@login_required
def DashboardView(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user.username, belegger__naam='Syntrus'):
        projects = Project.objects.filter(belegger__naam='Syntrus').filter(permitted__username__contains=request.user.username).distinct()
        context["projects"] = projects
    
    if PVEItemAnnotation.objects.filter(gebruiker=request.user):
        opmerkingen = PVEItemAnnotation.objects.filter(gebruiker=request.user, project__belegger__naam='Syntrus')
        context["opmerkingen"] = opmerkingen

    if request.user.type_user == 'B':
        return render(request, 'dashboardBeheerder_syn.html', context)
    if request.user.type_user == 'SB':
        return render(request, 'dashboardBeheerder_syn.html', context)
    if request.user.type_user == "SOG":
        return render(request, 'dashboardOpdrachtgever_syn.html', context)
    if request.user.type_user == "SD":
        return render(request, 'dashboardDerde_syn.html', context)

@login_required(login_url='login_syn')
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
    return render(request, 'FAQ_syn.html', context)

@login_required(login_url='login_syn')
def LogoutView(request):
    logout(request)
    return redirect('login_syn')

@login_required(login_url='login_syn')
def ManageOrganisaties(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    context = {}
    context["organisaties"] = Organisatie.objects.all()
    return render(request, 'organisatieManager.html', context)

@login_required(login_url='login_syn')
def AddOrganisatie(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    if request.method == "POST":
        form = forms.AddOrganisatieForm(request.POST)

        if form.is_valid():
            new_organisatie = Organisatie()
            new_organisatie.naam = form.cleaned_data["naam"]
            new_organisatie.save()
            return redirect("manageorganisaties_syn")

    context = {}
    context["organisaties"] = Organisatie.objects.all()
    context["form"] = AddOrganisatieForm()
    return render(request, 'organisatieAdd.html', context)

@login_required(login_url='login_syn')
def DeleteOrganisatie(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    if not Organisatie.objects.filter(id=pk):
        return render(request, '404_syn.html')

    organisatie = Organisatie.objects.filter(id=pk).first()

    if request.method == "POST":
        organisatie.delete()
        return redirect("manageorganisaties_syn")

    context = {}
    context["organisatie"] = organisatie
    context["organisaties"] = Organisatie.objects.all()
    return render(request, 'organisatieDelete.html', context)

@login_required(login_url='login_syn')
def ManageProjects(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    context = {}
    context["projecten"] = Project.objects.all().order_by('-datum_recent_verandering')
    return render(request, 'beheerProjecten_syn.html', context)

@login_required(login_url='login_syn')
def AddProjectManager(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    if not Project.objects.filter(id=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

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
                'admin@pvegenerator.net',
                [f'{form.cleaned_data["projectmanager"].email}'],
                fail_silently=False,
            )
            return redirect("manageprojecten_syn")

    context = {}
    context["projecten"] = Project.objects.all().order_by('-datum_recent_verandering')
    context["project"] = Project.objects.filter(id=pk).first()
    context["form"] = forms.AddProjectmanagerToProjectForm()
    return render(request, 'beheerAddProjmanager.html', context)

@login_required(login_url='login_syn')
def AddOrganisatieToProject(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    if not Project.objects.filter(id=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

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
                    'admin@pvegenerator.net',
                    [f'{werknemer.email}'],
                    fail_silently=False,
                )

            return redirect("manageprojecten_syn")

    context = {}
    context["projecten"] = Project.objects.all().order_by('-datum_recent_verandering')
    context["project"] = Project.objects.filter(id=pk).first()
    context["form"] = forms.AddOrganisatieToProjectForm()
    return render(request, 'beheerAddOrganisatieToProject.html', context)


@login_required(login_url='login_syn')
def ManageWerknemers(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    
    context = {}
    context["werknemers"] = CustomUser.objects.filter(Q(type_user="SD") | Q(type_user="SOG")).order_by('-last_visit')
    return render(request, 'beheerWerknemers_syn.html', context)


# Create your views here.
@login_required(login_url='login_syn')
def GeneratePVEView(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    if request.method == "POST":
        # get user entered form
        form = forms.PVEParameterForm(request.POST)
        # check validity
        if form.is_valid():
            # get parameters, find all pveitems with that
            (Bouwsoort1, TypeObject1, Doelgroep1, Bouwsoort2, TypeObject2, Doelgroep2, Bouwsoort3, TypeObject3, Doelgroep3, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort1"], form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"], form.cleaned_data["Bouwsoort2"], form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"], form.cleaned_data["Bouwsoort3"], form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )
            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(basisregel=True)
            basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort1))

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort2))
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort3))
            if TypeObject1:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(TypeObject__parameter__contains=TypeObject1))
            if TypeObject2:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(TypeObject__parameter__contains=TypeObject2))
            if TypeObject3:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(TypeObject__parameter__contains=TypeObject3))
            if Doelgroep1:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Doelgroep__parameter__contains=Doelgroep1))
            if Doelgroep2:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Doelgroep__parameter__contains=Doelgroep2))
            if Doelgroep3:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Doelgroep__parameter__contains=Doelgroep3))
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(AED=True)))
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Smarthome=True)))
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(EntreeUpgrade=True)))
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Pakketdient=True)))
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(JamesConcept=True)))

            basic_PVE = basic_PVE.order_by('id')
            # make pdf
            parameters = []
            if Bouwsoort1:
                parameters += f"{Bouwsoort1.parameter} (Hoofd)",
            if Bouwsoort2:
                parameters += f"{Bouwsoort2.parameter} (Sub)",
            if Bouwsoort3:
                parameters += f"{Bouwsoort3.parameter} (Sub)",
            if TypeObject1:
                parameters += f"{TypeObject1.parameter} (Hoofd)",
            if TypeObject2:
                parameters += f"{TypeObject2.parameter} (Sub)",
            if TypeObject3:
                parameters += f"{TypeObject3.parameter} (Sub)",
            if Doelgroep1:
                parameters += f"{Doelgroep1.parameter} (Hoofd)",
            if Doelgroep2:
                parameters += f"{Doelgroep2.parameter} (Sub)",
            if Doelgroep3:
                parameters += f"{Doelgroep3.parameter} (Sub)",
            date = datetime.datetime.now()
            fileExt = "%s%s%s%s%s%s" % (
                date.strftime("%H"),
                date.strftime("%M"),
                date.strftime("%S"),
                date.strftime("%d"),
                date.strftime("%m"),
                date.strftime("%Y")
            )
            filename = f"PvE-{fileExt}"
            zipFilename = f"PvE_Compleet-{fileExt}"
            pdfmaker = writePdf.PDFMaker()
            opmerkingen = {}
            bijlagen = {}

            pdfmaker.makepdf(filename, basic_PVE, opmerkingen, bijlagen, parameters)
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
            return render(request, 'PVEResult_syn.html', context)
        else:
            messages.warning(request, "Vul de verplichte keuzes in.")

    # if get method, just render the empty form
    context = {}
    context["form"] = forms.PVEParameterForm()
    return render(request, 'GeneratePVE_syn.html', context)

@login_required
def download_pve_overview(request):    
    projects = Project.objects.filter(permitted__username__contains=request.user.username)

    context = {}
    context["projects"] = projects
    return render(request, 'downloadPveOverview_syn.html', context)
    
@login_required
def download_pve(request, pk):
    if not Project.objects.filter(id=pk):
        raise Http404('404')
    
    if request.user.type_user != 'B':
        if not Project.objects.filter(id=pk, permitted__username__contains=request.user.username):
            raise Http404('404')

    project = Project.objects.filter(id=pk).first()
    basic_PVE = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").filter(projects__id__contains=pk).order_by('id')

    # make pdf
    parameters = []

    parameters += f"Project: {project.naam}",

    date = datetime.datetime.now()

    fileExt = "%s%s%s%s%s%s" % (
        date.strftime("%H"),
        date.strftime("%M"),
        date.strftime("%S"),
        date.strftime("%d"),
        date.strftime("%m"),
        date.strftime("%Y")
    )

    filename = f"PvE-{fileExt}"
    zipFilename = f"PvE_Compleet-{fileExt}"

    # Opmerkingen in kleur naast de regels
    opmerkingen = {}
    bijlagen = {}
    kostenverschil = 0

    if PVEItemAnnotation.objects.filter(project=project):
        for opmerking in PVEItemAnnotation.objects.select_related("item").filter(project=project):
            opmerkingen[opmerking.item.id] = opmerking
            if opmerking.kostenConsequenties:
                kostenverschil += opmerking.kostenConsequenties
            if BijlageToAnnotation.objects.filter(ann=opmerking).exists():
                bijlage = BijlageToAnnotation.objects.get(ann=opmerking)
                bijlagen[opmerking.item.id] = bijlage

    pdfmaker = writePdf.PDFMaker()
    pdfmaker.kostenverschil = kostenverschil
    pdfmaker.makepdf(filename, basic_PVE, opmerkingen, bijlagen, parameters)

    # get bijlagen
    bijlagen = [item for item in basic_PVE if item.bijlage]

    if BijlageToAnnotation.objects.filter(ann__project=project).exists():
        bijlagen = BijlageToAnnotation.objects.filter(ann__project=project)
        for item in bijlagen:
            bijlagen.append(item)
            
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
    return render(request, 'PVEResult_syn.html', context)

@login_required(login_url='login_syn')
def ViewProjectOverview(request):
    projects = Project.objects.filter(belegger__naam='Syntrus', permitted__username__contains=request.user.username)

    context = {}
    context["projects"]=projects
    return render(request, 'MyProjecten_syn.html', context)

@login_required(login_url='login_syn')
def ViewProject(request, pk):
    if not Project.objects.filter(id=pk, belegger__naam='Syntrus'):
        return render(request, '404_syn.html')

    if not Project.objects.filter(id=pk, belegger__naam='Syntrus', permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk, belegger__naam='Syntrus').first()

    if Room.objects.filter(project=project):
        chatroom = Room.objects.get(project=project)
    else:
        chatroom = Room()
        chatroom.description = f"Chat van {project.naam}"
        chatroom.project = project
        chatroom.save()

    medewerkers = [medewerker.username for medewerker in project.permitted.all()]

    # check of er frozencomments zijn als het project bevroren is, check het hoogste niveau om te kijken of het deelbaar door 2 is (of projmanager of checker kan het bekijken)
    if FrozenComments.objects.filter(project__id=project.id):
        frozencomments = FrozenComments.objects.filter(project__id=project.id).order_by('-level').first()
        highest_frozen_level = frozencomments.level
    else:
        # anders niet frozen
        highest_frozen_level = 0

    context = {}

    if project.frozenLevel == 0:
        pve_item_count = models.PVEItem.objects.filter(projects__id__contains=pk).count()
        comment_count = PVEItemAnnotation.objects.filter(project__id=pk).count()
        context["pve_item_count"] = pve_item_count
        context["comment_count"] = comment_count
        if project.pveconnected:
            context["done_percentage"] = int(100 * (comment_count) / pve_item_count)
        else:
            context["done_percentage"] = 0
            
    if project.frozenLevel >= 1:
        frozencomments_todo_now = FrozenComments.objects.filter(project__id=project.id).order_by('-level').first().comments.count()
        frozencomments_todo_first = FrozenComments.objects.filter(project__id=project.id).order_by('level').first().comments.count()
        context["frozencomments_todo_now"] = frozencomments_todo_now
        context["frozencomments_todo_first"] = frozencomments_todo_first
        context["frozencomments_done"] = frozencomments_todo_first - frozencomments_todo_now
        context["frozencomments_percentage"] = int(100 * (frozencomments_todo_first - frozencomments_todo_now) / frozencomments_todo_first)
    
    context["project"] = project
    context["chatroom"] = chatroom
    context["medewerkers"] = medewerkers
    context["highest_frozen_level"] = highest_frozen_level
    return render(request, 'ProjectPagina_syn.html', context)    

@login_required(login_url='login_syn')
def AddCommentOverview(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user):
        projects = Project.objects.filter(permitted__username__contains=request.user)
        context["projects"] = projects

    return render(request, 'plusOpmerkingOverview_syn.html', context)

@login_required(login_url='login_syn')
def MyComments(request, pk):
    context = {}

    if not Project.objects.filter(pk=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(pk=pk).first()

    if project.frozenLevel > 0:
        return render(request, '404_syn.html')
    
    if request.user != project.projectmanager:
        return render(request, '404_syn.html')

        # multiple forms
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("item_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(dict(item_id=item_id, annotation=opmrk, status=status, kostenConsequenties=kosten))
            for item_id, opmrk, status, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()]
        for form in ann_forms:
            # true comment if either comment or voldoet
            if form.cleaned_data["status"]:
                ann = PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()).first()
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()
                if form.cleaned_data["annotation"]:
                    ann.annotation = form.cleaned_data["annotation"]
                ann.status = form.cleaned_data["status"]
                #bijlage uit cleaned data halen en opslaan!
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                ann.save()

        return redirect('mijnopmerkingen_syn', pk=project.id)

    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(ann__project=project, ann__gebruiker=request.user):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    comments = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).order_by('-datum')
    for comment in comments:
        ann_forms.append(forms.PVEItemAnnotationForm(initial={
            'item_id':comment.item.id,
            'annotation':comment.annotation,
            'status':comment.status,
            'kostenConsequenties':comment.kostenConsequenties,
            }))
        
        form_item_ids.append(comment.item.id)

    aantal_opmerkingen_gedaan = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).count()
    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = comments
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    return render(request, 'MyComments.html', context)

@login_required(login_url='login_syn')
def MyCommentsDelete(request, pk):
    if not Project.objects.filter(pk=pk):
        return render(request, '404_syn.html')

    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    project = Project.objects.filter(pk=pk).first()

    if project.frozenLevel > 0:
        return render(request, '404_syn.html')

    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(ann__project=project, ann__gebruiker=request.user):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    aantal_opmerkingen_gedaan = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).count()

    context = {}
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).order_by('id')
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    return render(request, 'MyCommentsDelete.html', context)

@login_required(login_url='login_syn')
def deleteAnnotationPve(request, project_id, ann_id):
    # check if project exists
    if not Project.objects.filter(id=project_id):
        raise Http404("404")
    
    project = Project.objects.filter(id=project_id).first()

    if project.frozenLevel > 0:
        return render(request, '404_syn.html')

    # check if user is authorized to project
    if request.user.type_user != 'B':
        if not Project.objects.filter(id=project_id, permitted__username__contains=request.user.username):
            raise Http404('404')
    
    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(id=ann_id, gebruiker=request.user):
        raise Http404("404")


    comment = PVEItemAnnotation.objects.filter(id=ann_id).first()

    if request.method == "POST":
        messages.warning(request, f'Opmerking van {comment.project} verwijderd.')
        comment.delete()
        return HttpResponseRedirect(reverse('mijnopmerkingendelete_syn', args=(project.id,)))


    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []
    
    for bijlage in BijlageToAnnotation.objects.filter(ann__project=project, ann__gebruiker=request.user):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["comment"] = comment
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).order_by('id')
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten

    return render(request, 'deleteAnnotationModal_syn.html', context)

@login_required(login_url='login_syn')
def AddAnnotationAttachment(request, projid, annid):
    if not Project.objects.filter(pk=projid):
        return render(request, '404_syn.html')

    project = Project.objects.filter(pk=projid).first()

    if project.frozenLevel > 0:
        return render(request, '404_syn.html')


    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    annotation = PVEItemAnnotation.objects.filter(project=project, pk=annid).first()
    comments = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).order_by('id')

    if annotation.gebruiker != request.user:
        return render(request, '404_syn.html')

    if request.method == "POST":
        form = forms.BijlageToAnnotationForm(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["bijlage"]:
                form.save()
                annotation.bijlage = True
                annotation.save()
                return redirect('mijnopmerkingen_syn', pk=project.id)
    
    context = {}
    form = BijlageToAnnotationForm(initial={'ann':annotation})
    context["annotation"] = annotation
    context["form"] = form
    context["project"] = project
    context["comments"] = comments
    return render(request, 'addBijlagetoAnnotation_syn.html', context)


@login_required(login_url='login_syn')
def VerwijderAnnotationAttachment(request, projid, annid):
    
    # check if project exists
    if not Project.objects.filter(id=projid):
        raise Http404("404")
    
    project = Project.objects.filter(id=projid).first()

    if project.frozenLevel > 0:
        return render(request, '404_syn.html')

    # check if user is authorized to project
    if request.user.type_user != 'B':
        if not Project.objects.filter(id=projid, permitted__username__contains=request.user.username):
            raise Http404('404')
    
    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(id=annid, gebruiker=request.user):
        raise Http404("404")

    comment = PVEItemAnnotation.objects.filter(id=annid).first()
    attachment = BijlageToAnnotation.objects.filter(ann_id=annid).first()

    if request.method == "POST":
        messages.warning(request, f'Bijlage van {attachment.ann} verwijderd.')
        comment.bijlage = False
        comment.save()
        attachment.delete()
        return HttpResponseRedirect(reverse('mijnopmerkingendelete_syn', args=(project.id,)))

    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []
    
    for bijlage in BijlageToAnnotation.objects.filter(ann__project=project, ann__gebruiker=request.user):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["comment"] = comment
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user).order_by('id')
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten

    return render(request, 'deleteAttachmentAnnotation_syn.html', context)


@login_required(login_url='login_syn')
def DownloadAnnotationAttachment(request, projid, annid):
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    item = BijlageToAnnotation.objects.filter(ann__project__id=projid, ann__id=annid).first()
    expiration = 10000
    s3_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=settings.AWS_S3_REGION_NAME, config=botocore.client.Config(signature_version=settings.AWS_S3_SIGNATURE_VERSION))
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': str(item.bijlage)},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)

@login_required(login_url='login_syn')
def AllComments(request, pk):
    context = {}

    if not Project.objects.filter(pk=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(pk=pk).first()

    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')
    
    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    if PVEItemAnnotation.objects.filter(project=project):
        gebruiker = PVEItemAnnotation.objects.filter(project=project).first()
        auteur = gebruiker.gebruiker
        context["gebruiker"] = gebruiker
        context["comments"] = PVEItemAnnotation.objects.filter(project=project).order_by('-datum')

    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id).order_by('id')
    context["project"] = project
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = PVEItemAnnotation.objects.filter(project=project).count()
    return render(request, 'AllCommentsOfProject_syn.html', context)

@login_required(login_url='login_syn')
def AddComment(request, pk):
    context = {}

    if not Project.objects.filter(id=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

    if request.user != project.projectmanager:
        return render(request, '404_syn.html')

    if project.frozenLevel > 0:
        return render(request, '404_syn.html')

    if not models.PVEItem.objects.filter(projects__id__contains=pk).exists():
        return render(request, '404_syn.html')

    # multiple forms
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("item_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(dict(item_id=item_id, annotation=opmrk, status=status, kostenConsequenties=kosten))
            for item_id, opmrk, status, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()]

        for form in ann_forms:
            # true comment if either status or voldoet
            if form.cleaned_data["status"]:
                if PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()):
                    ann = PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()).first()
                else:
                    ann = PVEItemAnnotation()
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()
                if form.cleaned_data["annotation"]:
                    ann.annotation = form.cleaned_data["annotation"]
                ann.status = form.cleaned_data["status"]
                #bijlage uit cleaned data halen en opslaan!
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                ann.save()

        # remove duplicate entries
        return redirect('mijnopmerkingen_syn', pk=project.id)

    items = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").filter(projects__id__contains=pk).order_by('id')
    annotations = {}

    for annotation in PVEItemAnnotation.objects.select_related("item").select_related("status").filter(Q(project=project) & Q(gebruiker=request.user)):
        annotations[annotation.item] = annotation

    ann_forms = []
    hoofdstuk_ordered_items = {}

    for item in items:
        opmerking = None

        # create forms
        if item not in annotations.keys():
            ann_forms.append(forms.PVEItemAnnotationForm(initial={'item_id':item.id}))
        else:
            opmerking = annotations[item]
            ann_forms.append(forms.PVEItemAnnotationForm(initial={
                'item_id':opmerking.item.id,
                'annotation':opmerking.annotation,
                'status':opmerking.status,
                'kostenConsequenties':opmerking.kostenConsequenties,
                }))

        # create ordered items
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                    hoofdstuk_ordered_items[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk]:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append([item, item.id, opmerking.status])
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append([item, item.id, None])
            else:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [[item, item.id, opmerking.status]]
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [[item, item.id, None]]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk].append([item, item.id, opmerking.status])
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk].append([item, item.id, None])
            else:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [[item, item.id, opmerking.status]]
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [[item, item.id, None]]

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
    return render(request, 'plusOpmerking_syn.html', context)


@login_required(login_url='login_syn')
def AddProject(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    if request.method == "POST":
        form = forms.StartProjectForm(request.POST)

        if form.is_valid():
            form.save()

            project = Project.objects.all().order_by("-id")[0]
            project.permitted.add(request.user)
            project.belegger = Beleggers.objects.filter(naam="Syntrus").first()

            geolocator = Nominatim(user_agent="tamesbpvegenerator")
            if 'city' in geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address'].keys():
                project.plaatsnamen = geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address']['city']
            else:
                project.plaatsnamen = geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address']['town']

            project.save()
            return redirect('connectpve_syn', pk=project.id)

    context = {}
    context["form"] = StartProjectForm()
    return render(request, 'plusProject_syn.html', context)

@login_required(login_url='login_syn')
def InviteUsersToProject(request, pk):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

    if request.method == 'POST':
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
                        'admin@pvegenerator.net',
                        [f'{gebruiker.email}'],
                        fail_silently=False,
                    )

            if projectmanager:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {project}",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor het project { project } van Syntrus.
                    
                    U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/project/{project.id}""",
                    'admin@pvegenerator.net',
                    [f'{projectmanager.email}'],
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
                        'admin@pvegenerator.net',
                        [f'{gebruiker.email}'],
                        fail_silently=False,
                    )


            return redirect('connectpve_syn', pk=project.id)

    # form
    form = forms.InviteProjectStartForm()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, 'InviteUsersToProject_syn.html', context)


@login_required(login_url='login_syn')
def ConnectPVE(request, pk):
    allowed_users = ["B", "SB", "SOG"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

    if project.pveconnected:
        return render(request, '404_syn.html')

    if request.method == 'POST':
        form = forms.PVEParameterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # get parameters, find all pveitems with that
            (Bouwsoort1, TypeObject1, Doelgroep1, Bouwsoort2, TypeObject2, Doelgroep2, Bouwsoort3, TypeObject3, Doelgroep3, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort1"], form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"], form.cleaned_data["Bouwsoort2"], form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"], form.cleaned_data["Bouwsoort3"], form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )
            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(basisregel=True)
            basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort1))
            project.bouwsoort1 = models.Bouwsoort.objects.filter(parameter=Bouwsoort1).first()

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Bouwsoort__parameter__contains=Bouwsoort2))
                project.bouwsoort2 = models.Bouwsoort.objects.filter(parameter=Bouwsoort2).first()

            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                   models.PVEItem.objects.filter(
                        Bouwsoort__parameter__contains=Bouwsoort3))
                project.bouwsoort2 = models.Bouwsoort.objects.filter(parameter=Bouwsoort3).first()

            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject1))
                project.typeObject1 = models.TypeObject.objects.filter(parameter=TypeObject1).first()

            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject2))
                project.typeObject2 = models.TypeObject.objects.filter(parameter=TypeObject2).first()

            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject3))
                project.typeObject2 = models.TypeObject.objects.filter(parameter=TypeObject3).first()

            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep1))
                project.doelgroep1 = models.Doelgroep.objects.filter(parameter=Doelgroep1).first()

            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep2))
                project.doelgroep2 = models.Doelgroep.objects.filter(parameter=Doelgroep2).first()
            
            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep3))
                project.doelgroep2 = models.Doelgroep.objects.filter(parameter=Doelgroep3).first()
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(AED=True)))
                project.AED = True

            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Smarthome=True)))
                # add the parameter to the project
                project.Smarthome = True

            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(EntreeUpgrade=True)))
                project.EntreeUpgrade = True

            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Pakketdient=True)))
                project.Pakketdient = True

            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(JamesConcept=True)))
                project.JamesConcept = True

            # add the project to all the pve items
            for item in basic_PVE:
                item.projects.add(project)

            # succesfully connected, save the project
            project.pveconnected = True
            project.save()
            return redirect('projectenaddprojmanager_syn', pk=project.id)

    # form
    form = forms.PVEParameterForm()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, 'ConnectPVE_syn.html', context)


@login_required(login_url='login_syn')
def AddAccount(request):
    allowed_users = ["B", "SB", "SOG"]
    staff_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

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
                if form.cleaned_data["rang"] == 'SOG':
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
                    'admin@pvegenerator.net',
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
                    'admin@pvegenerator.net',
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )

            messages.warning(request, f"Uitnodiging verstuurd naar { form.cleaned_data['invitee'] }. De uitnodiging zal verlopen in { expiry_length } dagen.)")
            return redirect("managewerknemers_syn")

    projecten = Project.objects.filter(permitted__username__contains=request.user.username)

    if request.user.type_user in staff_users:
        form = forms.PlusAccountForm()
    else:
        form = forms.KoppelDerdeUserForm()

    # set projects to own
    form.fields["project"].queryset = projecten
    context = {}
    context["form"] = form

    if request.user.type_user in staff_users:
        return render(request, 'plusAccount_syn.html', context)
    else:
        return render(request, 'plusDerde_syn.html', context)

@login_required(login_url='login_syn')
def AddUserOrganisatie(request, pk):
    allowed_users = ["B", "SB"]
    staff_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')
    if not Organisatie.objects.filter(id=pk):
        return render(request, '404_syn.html')
    
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
                'admin@pvegenerator.net',
                [f'{werknemer.email}'],
                fail_silently=False,
            )
            return redirect("manageorganisaties_syn")


    form = forms.AddUserToOrganisatieForm()

    context = {}
    context["form"] = form
    context["pk"] = pk
    context["organisatie"] = organisatie
    context["organisaties"] = organisaties
    return render(request, 'organisatieAddUser.html', context)


def AcceptInvite(request, key):
    if not key or not Invitation.objects.filter(key=key):
        return render(request, '404_syn.html')
    
    invitation = Invitation.objects.filter(key=key).first()

    if utc.localize(datetime.datetime.now()) > invitation.expires:
        return render(request, '404verlopen_syn.html')

    if request.method == "POST":
        form = AcceptInvitationForm(request.POST)

        if form.is_valid():
            # strip the email by its first part to automatically create a username
            sep = "@"
            username = invitation.invitee.split(sep, 1)[0]
            user = CustomUser.objects.create_user(username, password=form.cleaned_data["password1"])
            user.email = invitation.invitee
            if invitation.organisatie:
                user.organisatie = invitation.organisatie
            user.save()
            
            user = authenticate(request, username=username, password=form.cleaned_data["password1"])

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
                'admin@pvegenerator.net',
                [f'{invitation.invitee}'],
                fail_silently=False,
            )
            if user is not None:
                login(request, user)
                return redirect('viewprojectoverview_syn')

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    return render(request, 'acceptInvitation_syn.html', context)


@login_required(login_url='login_syn')
def FirstFreeze(request, pk):
    if not Project.objects.filter(id=pk):
        raise Http404('404')

    project = Project.objects.filter(id=pk).first()

    if request.user !=  project.projectmanager:
        return render(request, '404_syn.html')

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
                comments = PVEItemAnnotation.objects.filter(project=project).all()
                
                # add all comments to it
                for comment in comments:
                    frozencomments.comments.add(comment)

                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()

                allprojectusers = project.permitted.all()
                filteredDerden = [user.email for user in allprojectusers if user.type_user == "SD"]
                send_mail(
                    f"Syntrus Projecten - Uitnodiging opmerkingscheck voor project {project}",
                    f"""{ request.user } heeft de initiele statussen van de PvE-regels ingevuld en nodigt u uit deze te checken voor het project { project } van Syntrus.
                    
                    Klik op de link om rechtstreeks de statussen langs te gaan.
                    Link: https://pvegenerator.net/syntrus/project/{project.id}/check
                    """,
                    'admin@pvegenerator.net',
                    [f'{filteredDerden}'],
                    fail_silently=False,
                )

                messages.warning(request, f"Uitnodiging voor opmerkingen checken verstuurd naar { form.cleaned_data['invitee'] }. De uitnodiging zal verlopen in { expiry_length } dagen.)")
                return redirect('viewproject_syn', pk=project.id)

    context = {}
    context["form"] = FirstFreezeForm(request.POST)
    context["pk"] = pk
    return render(request, 'FirstFreeze.html', context)

@login_required(login_url='login_syn')
def CheckComments(request, proj_id):
    context = {}

    # get the project
    if not Project.objects.filter(id=proj_id):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=proj_id).first()

    # check first if user is permitted to the project
    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    # get the frozencomments and the level
    if not FrozenComments.objects.filter(project__id=proj_id):
        return render(request, '404_syn.html')

    # get the highest ID of the frozencomments phases; the current phase
    frozencomments = FrozenComments.objects.filter(project__id=proj_id).order_by('-level').first()

    # uneven level = turn of SD, even level = turn of SOG
    if (frozencomments.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user != "SD":
            return render(request, '404_syn.html')
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != "SOG":
            return render(request, '404_syn.html')

    # the POST method
    if request.method == "POST":
        comment_id_list = [number for number in request.POST.getlist("comment_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.CommentReplyForm(dict(comment_id=comment_id, annotation=opmrk, status=status))
            for comment_id, opmrk, status in zip(
                request.POST.getlist("comment_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
            )
        ]

        # only use valid forms
        ann_forms = [ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()]

        # initiate the non-accepted comments check
        non_accepted_comments_ids = []

        for form in ann_forms:
            # Not accepted if annotation is filled out. Add a CommentReply per form
            if form.cleaned_data["annotation"]:
                
                # get the original comment it was on
                originalComment = PVEItemAnnotation.objects.filter(id=form.cleaned_data["comment_id"]).first()

                if form.cleaned_data["status"] != originalComment.status:
                    originalComment.status = form.cleaned_data["status"]
                    originalComment.save()

                ann = CommentReply()

                ann.commentphase = frozencomments
                ann.onComment = originalComment
                ann.comment = form.cleaned_data["annotation"]
                ann.save()

                # add the non_accepted id to list for further saving
                non_accepted_comments_ids.append(form.cleaned_data["comment_id"])

        # create a new phase with 1 higher level
        new_phase = FrozenComments()
        new_phase.level = frozencomments.level + 1
        new_phase.project = project
        new_phase.save()

        # add all the non accepted comments
        for comment_id in non_accepted_comments_ids:
            todo_comment = PVEItemAnnotation.objects.filter(id=comment_id).first()
            new_phase.comments.add(todo_comment)
            new_phase.save()

        # redirect to dashboard after posting replies for now
        return redirect('dashboard_syn')

    # the GET method
    comments = frozencomments.comments.order_by('id').all()

    # create the forms
    ann_forms = []
    for comment in comments:
        # look if the persons reply already exists, for later saving
        if not CommentReply.objects.filter(Q(commentphase=frozencomments) & Q(onComment=comment)):
            ann_forms.append(forms.CommentReplyForm(initial={'comment_id':comment.id, 'status':comment.status}))
        else:
            reply = CommentReply.objects.filter(Q(commentphase=frozencomments) & Q(onComment=comment)).first()
            ann_forms.append(forms.CommentReplyForm(initial={
                'comment_id':comment.id,
                'annotation':reply.comment,
                }))

    # loop for reply ordering for the pagedesign
    hoofdstuk_ordered_items = {}
    temp_commentbulk_list = {}
    form_item_ids = []

    for comment in comments:

        # set the PVEItem from the comment
        item = comment.item

        # save id to list for connecting modal to the item
        form_item_ids.append(item.id)

        # sort
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                    hoofdstuk_ordered_items[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk]:
                hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(item)
            else:
                hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [item]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items:
                hoofdstuk_ordered_items[item.hoofdstuk].append(item)
            else:
                hoofdstuk_ordered_items[item.hoofdstuk] = [item]

        # to put comments in a dict where they are organized
        if item not in temp_commentbulk_list.keys():
            temp_commentbulk_list[item] = [comment]
        else:
            temp_commentbulk_list[item].append(comment)

        # add all replies to this comment
        if CommentReply.objects.filter(Q(onComment=comment)):
            commentreplys = CommentReply.objects.filter(Q(onComment=comment)).all()

            for reply in commentreplys:
                temp_commentbulk_list[item].append(reply.comment)
        

    # arrange the comments in list so the comments are combined onto one item
    comment_inhoud_list = []

    for comments in temp_commentbulk_list.values():

        # ensures to put multiple comments in one string
        string = f"Huidige status: { comments[0].status }, Opmerkingen: "
        for comment in comments:
            string += f"'{ comment }', "

        # remove last comma and space from string
        string = string[:-2]
        comment_inhoud_list.append(string)

    context["forms"] = ann_forms
    context["comments"] = comments
    context["form_item_ids"] = form_item_ids
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id).order_by('id')
    context["project"] = project
    context["hoofdstuk_ordered_items"] = hoofdstuk_ordered_items
    context["comment_inhoud_list"] = comment_inhoud_list
    return render(request, 'CheckComments_syn.html', context)

@login_required
def FrozenProgressView(request, proj_id):
    context = {}

    # get the project
    if not Project.objects.filter(id=proj_id):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=proj_id).first()

    # check first if user is permitted to the project
    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    # get the frozencomments and the level
    if not FrozenComments.objects.filter(project__id=proj_id):
        return render(request, '404_syn.html')

    # get all the frozencomments, based on level
    frozencomments = FrozenComments.objects.filter(project__id=proj_id).order_by('level')
    first_frozen = frozencomments.first()

    # infos (list van gebruiker + datum), regels (die op de comments waren), comments (lijst van opeenvolgende comments bij de regel)
    infos = []
    regels = {}

    for frozencomment in frozencomments:
        infos.append(frozencomment.level)

        for comment in frozencomment.comments.all():

            if comment.item in regels:
                commentreplys = CommentReply.objects.filter(Q(onComment=comment)).order_by('id')
                
                for commentreply in commentreplys:
                    if commentreply not in regels[comment.item]:
                        regels[comment.item].append(commentreply)
            else:
                regels[comment.item] = [comment.status, comment]

    context["infos"] = infos
    context["regels"] = regels
    context["project"] = project
    return render(request, 'FrozenProgress_syn.html', context)
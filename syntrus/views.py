from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from syntrus import forms
from project.models import Project, PVEItemAnnotation
from users.models import Invitation, CustomUser
from syntrus.forms import KoppelDerdeUserForm
from users.forms import AcceptInvitationForm
from app import models
import datetime
from geopy.geocoders import Nominatim
from django.db.models import Q
from utils import writePdf
from utils import createBijlageZip
from utils.writePdf import PDFMaker
from utils.createBijlageZip import ZipMaker
import secrets
from django.core.mail import send_mail
import pytz

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
        print(projects)
        #geolocator = Nominatim(user_agent="pvegenerator")
        #locations = {}
        #for project in projects:
        #    if 'city' in geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address'].keys():
        #        locations[project] = geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address']['city']
        #    else:
        #        locations[project] = geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address']['town']
        #context["locations"] = locations
    
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
def LogoutView(request):
    logout(request)
    return redirect('login_syn')

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
            pdfmaker.makepdf(filename, basic_PVE, parameters)
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
    basic_PVE = models.PVEItem.objects.filter(projects__id__contains=pk)

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

    filename = f"PvE-{fileExt}"
    zipFilename = f"PvE_Compleet-{fileExt}"

    pdfmaker = writePdf.PDFMaker()
    pdfmaker.makepdf(filename, basic_PVE, parameters)

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

@login_required(login_url='login_syn')
def ViewProject(request, pk):
    if not Project.objects.filter(id=pk, belegger__naam='Syntrus'):
        return render(request, '404_syn.html')

    project = Project.object.filter(id=pk, belegger__naam='Syntrus')

    if not project.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    context = {}
    context["project"] = project
    return render(request, 'projectView_syn.html', context)

@login_required(login_url='login_syn')
def AddCommentOverview(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user):
        projects = Project.objects.filter(permitted__username__contains=request.user)
        context["projects"] = projects

    return render(request, 'plusOpmerkingOverview_syn.html', context)

@login_required(login_url='login_syn')
def AddComment(request, pk):
    context = {}

    if not Project.objects.filter(id=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

    if request.user not in project.permitted.all():
        return render(request, '404_syn.html')

    # multiple forms!
    if request.method == "POST":
        ann_forms = [
            forms.PVEItemAnnotationForm(dict(item_id=item_id, annotation=opmrk, kostenConsequenties=kosten, annbijlage=annbijlage))
            for item_id, opmrk, kosten, annbijlage in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("kostenConsequenties"),
                request.FILES.getlist("annbijlage"),
            )
        ]

        # only use valid forms
        ann_forms = [ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()]

        # second check, save in annotations
        if all(ann_forms[i].is_valid() for i in range(len(ann_forms))):                
            for form in ann_forms:
                if form.cleaned_data["annotation"]:
                    annotation = PVEItemAnnotation()
                    annotation.project = project
                    annotation.item = models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()
                    annotation.annotation = form.cleaned_data["annotation"]
                    annotation.gebruiker = request.user
                    if form.cleaned_data["kostenConsequenties"]:
                        annotation.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                    if form.cleaned_data["annbijlage"]:
                        annotation.annbijlage = form.cleaned_data["annbijlage"]
                    annotation.save()

            messages.warning(request, f"{range(len(ann_forms))} opmerkingen toegevoegd.")
            return redirect('dashboard_syn')

    if models.PVEItem.objects.filter(projects__id__contains=pk):
        items = models.PVEItem.objects.filter(projects__id__contains=pk).order_by('id')
        ann_forms = [forms.PVEItemAnnotationForm(initial={'item_id':item.id}) for item in items]

        hoofdstuk_ordered_items = {}

        for item in items:
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

        # easy entrance to item ids
        form_item_ids = [item.id for item in items]

        context["forms"] = ann_forms
        context["items"] = items
        context["form_item_ids"] = form_item_ids
        context["hoofdstuk_ordered_items"] = hoofdstuk_ordered_items

    context["project"] = project
    return render(request, 'plusOpmerking_syn.html', context)


@login_required(login_url='login_syn')
def AddProject(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    context = {}
    return render(request, 'plusProject_syn.html', context)

@login_required(login_url='login_syn')
def AddAccount(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    context = {}
    return render(request, 'plusAccount_syn.html', context)

@login_required(login_url='login_syn')
def AddDerde(request):
    allowed_users = ["B", "SB", "SOG", "SD"]
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
            invitation.project = form.cleaned_data["project"]
            invitation.user_functie = form.cleaned_data["user_functie"]
            invitation.user_afdeling = form.cleaned_data["user_afdeling"]
            
            # Als syntrus beheerder invitatie doet kan hij ook rang geven (projectmanager/derde)
            manager = False

            if request.user.type_user in staff_users:
                invitation.rang = form.cleaned_data["rang"]

                if form.cleaned_data["rang"] == 'SOG':
                    manager = True

            expiry_length = 10
            expire_date = datetime.datetime.now() + datetime.timedelta(expiry_length)
            invitation.expires = expire_date
            invitation.key = secrets.token_urlsafe(30)
            invitation.save()

            if manager:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {form.cleaned_data['project']}",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor het project { form.cleaned_data['project'] } van Syntrus.
                    
                    Klik op de uitnodigingslink om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    'admin@pvegenerator.net',
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )
            else:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {form.cleaned_data['project']}",
                    f"""{ request.user } nodigt u uit voor het commentaar leveren en het checken van het Programma van Eisen voor het project { form.cleaned_data['project'] } van Syntrus.
                    
                    Klik op de uitnodigingslink om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    'admin@pvegenerator.net',
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )

            messages.warning(request, f"Uitnodiging verstuurd naar { form.cleaned_data['invitee'] } voor project { form.cleaned_data['project'] }. De uitnodiging zal verlopen in { expiry_length } dagen.)")
            return redirect("dashboard_syn")

    projecten = Project.objects.filter(permitted__username__contains=request.user.username, belegger__naam='Syntrus')

    if request.user.type_user in staff_users:
        form = forms.PlusAccountForm(initial={'project': projecten})
    else:
        form = forms.KoppelDerdeUserForm(initial={'project': projecten})

    context = {}
    context["form"] = form

    if request.user.type_user in staff_users:
        return render(request, 'plusAccount_syn.html', context)
    else:
        return render(request, 'plusDerde_syn.html', context)

def AcceptInvite(request, key):
    if not key or not Invitation.objects.filter(key=key):
        return render(request, '404_syn.html')
    
    invitation = Invitation.objects.filter(key=key).first()

    if utc.localize(datetime.datetime.now()) > invitation.expires:
        return render(request, '404verlopen_syn.html')

    if request.method == "POST":
        form = AcceptInvitationForm(request.POST)

        if form.is_valid():
            form.email = invitation.invitee
            form.functie = invitation.user_functie
            form.afdeling = invitation.user_afdeling

            if invitation.rang:
                form.type_user = invitation.rang

            form.save()

            user = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password1"])
            project = invitation.project
            project.permitted.add(user)

            if invitation.rang:
                if invitation.rang == "SOG":
                    project.projectmanager = user

            invitation.delete()

            if user is not None:
                login(request, user)
                return redirect('dashboard_syn')

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    return render(request, 'acceptInvitation_syn.html', context)

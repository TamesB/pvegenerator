from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from syntrus import forms
from project.models import Project
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
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    if request.method == "POST":
        # get user entered form
        form = forms.KoppelDerdeUserForm(request.POST)
        # check validity
        if form.is_valid():
            invitation = Invitation()
            invitation.inviter = request.user
            invitation.invitee = form.cleaned_data["invitee"]
            invitation.project = form.cleaned_data["project"]
            invitation.user_functie = form.cleaned_data["user_functie"]
            invitation.user_afdeling = form.cleaned_data["user_afdeling"]

            expiry_length = 10
            expire_date = datetime.datetime.now() + datetime.timedelta(expiry_length)
            invitation.expires = expire_date
            invitation.key = secrets.token_urlsafe(30)
            invitation.save()

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
    form = KoppelDerdeUserForm(initial={'project': projecten})
    context = {}
    context["form"] = form
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
            form.save()

            user = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password1"])
            project = invitation.project
            project.permitted.add(user)

            invitation.delete()

            if user is not None:
                login(request, user)
                return redirect('dashboard_syn')

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    return render(request, 'acceptInvitation_syn.html', context)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from project.models import Beleggers, Project
from users.models import CustomUser
from pvetool import forms
from pvetool.forms import StartProjectForm
from pvetool.views.utils import GetAWSURL
from users.models import CustomUser, Organisatie
from django.urls import reverse_lazy
from django.http import Http404, HttpResponse, HttpResponseRedirect


# SSL geocoder
import certifi
import ssl
import geopy.geocoders
from geopy.geocoders import Nominatim
ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx


# minimal gatekeeping for partial templates.
def GateKeepingMinimal(request, client_pk):
    # Belegger is the client, checks if this subwebsite exists.
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return False

    # this viewset requires the user to be of the client, and a form of admin (either total admin B or subwebsite admin SB)
    if (
        request.user.client.id != client_pk
        and request.user.type_user != "B"
        and request.user.type_user != "SB"
    ):
        return False
    
    return True


# initial account-type gatekeeping the pages. Also returns the logo_url and client object, for full pages
def GateKeepingVerbose(request, client_pk):
    # check if the client exists
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return False, None, None

    # get the logo from the client object
    client = Beleggers.objects.filter(pk=client_pk).first()

    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    # here the admin is allowed to enter any client website
    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return False, None, None
    else:
        return False, None, None
    
    return True, logo_url, client

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def ManageProjects(request, client_pk):
    # Gatekeep users
    user_allowed, logo_url, client = GateKeepingVerbose(request, client_pk)
    
    if not user_allowed:
        return redirect("logout_syn", client_pk=client_pk)
    
    # get all projects from this client
    projecten = client.project.all().order_by("-date_recent_verandering")

    new_projecten = []
    old_projecten = []

    # filter projects that have initial projectmanagers/3rd parties added, and ones that don't
    for project in projecten:
        stakeholders = project.organisaties.all()
        if (
            not project.pveconnected
            or not project.projectmanager
            or len(stakeholders) == 0
        ):
            new_projecten.append(project)
        else:
            old_projecten.append(project)

    context = {}
    context["new_projecten"] = new_projecten
    context["old_projecten"] = old_projecten
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "beheerProjecten_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddProject(request, client_pk):
    # Gatekeep users
    user_allowed, logo_url, client = GateKeepingVerbose(request, client_pk)
    
    if not user_allowed:
        return redirect("logout_syn", client_pk=client_pk)

    if request.method == "POST":
        form = forms.StartProjectForm(request.POST)

        if form.is_valid():
            # save the initial data
            form.save()

            # find this project and add the user to the permitted user list
            project = Project.objects.all().order_by("-id")[0]
            project.permitted.add(request.user)
            project.client = client
            project.first_annotate = form.cleaned_data["first_annotate"]
            
            # Reverse coordinates to city/town name. Package is always very buggy with every version change.
            # Input coordinates should return
            # raw = {
            #    "address": {
            #      "city": city,
            #      "town": town,
            #        ...
            #    }, ...
            # }
            
            # They frequently change the payload keys, watch out!
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
            messages.warning(request, f"Project {project.name} aangemaakt.")
            return redirect("manageprojecten_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = StartProjectForm()
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusProject_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetProjectManagerOfProject(request, client_pk, pk):
    
    # gatekeep user from using this view
    user_allowed = GateKeepingMinimal(request, client_pk)
    if not user_allowed:
        return render(request, "partials/tests_error.html")
    
    # check if this project belongs to the client
    project = get_object_or_404(Project, id=pk)
    if project.client.id != client_pk:
        return render(request, "partials/tests_error.html")

    context = {}
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/projectmanager_detail.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,},))
def DeleteProject(request, client_pk, pk):
    # gatekeep user
    user_allowed = GateKeepingMinimal(request, client_pk)
    if not user_allowed:
        return render(request, "partials/tests_error.html")

    # check if project belongs to the client
    project = get_object_or_404(Project, id=pk)
    if project.client.id != client_pk:
        return render(request, "partials/tests_error.html")

    if request.headers["HX-Prompt"] == "VERWIJDEREN":
        project.delete()
        messages.warning(request, f"Project: {project.name} succesvol verwijderd!")
        return render(request, "partials/messages.html")
    else:
        messages.warning(request, f"Onjuiste invulling. Probeer het opnieuw.")
        return render(request, "partials/messages.html")

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddProjectManagerToProject(request, client_pk, pk):
    
    # partial template gatekeeping
    user_allowed = GateKeepingMinimal(request, client_pk)
    if not user_allowed:
        return render(request, "partials/tests_error.html")

    client = Beleggers.objects.get(id=client_pk)

    project = Project.objects.get(id=pk)
    
    # initiate the projectmanager form
    form = forms.AddProjectmanagerToProjectForm(request.POST or None)
    form.fields["projectmanager"].queryset = CustomUser.objects.filter(
        type_user="SOG", client=client
    )
    form.fields["projectmanager"].initial = project.projectmanager

    # create template context
    context = {}
    context["client_pk"] = client_pk
    context["project"] = project
    context["projectmanager"] = project.projectmanager

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            # if the form is valid, check if projectmanager belongs to the client
            if form.cleaned_data["projectmanager"].client != client:
                return render(request, "partials/tests_error.html")

            # if same projectmanager already, skip sending mails
            if project.projectmanager == form.cleaned_data["projectmanager"]:
                return render(request, "partials/projectmanager_detail.html", context)

            project.projectmanager = form.cleaned_data["projectmanager"]

            # add projectmanager to the permitted list of the project
            if form.cleaned_data["projectmanager"] not in project.permitted.all():
                project.permitted.add(form.cleaned_data["projectmanager"])
            project.save()

            # send the invitation for the project manager by mail
            send_mail(
                f"{ client.name } Projecten - Uitnodiging voor project {project}",
                f"""{ request.user } heeft u uitgenodigd projectmanager te zijn van het project { project } van { client.name }.
                
                U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan en de eerste PvE check uit te voeren.
                Link: https://pvegenerator.net/pvetool/{ client_pk }/project/{project.id}""",
                "admin@pvegenerator.net",
                [f'{form.cleaned_data["projectmanager"].email}'],
                fail_silently=False,
            )
            messages.warning(
                request,
                f"""De projectmanager van Project: {project.name} is nu {form.cleaned_data["projectmanager"]}.""",
            )
            return render(request, "partials/projectmanager_detail.html", context)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context["form"] = form
    return render(request, "partials/projectmanager_form.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetOrganisatieToProject(request, client_pk, pk):
    # Gatekeep users
    user_allowed, logo_url, client = GateKeepingVerbose(request, client_pk)
    
    if not user_allowed:
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, id=pk)
    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    context = {}
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "partials/projectpartijen_detail.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddOrganisatieToProject(request, client_pk, pk):
    # Gatekeep users
    user_allowed, logo_url, client = GateKeepingVerbose(request, client_pk)
    
    if not user_allowed:
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, id=pk)
    
    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)
    
    # initiate form
    form = forms.AddOrganisatieToProjectForm(request.POST or None)
    form.fields["stakeholder"].queryset = Organisatie.objects.filter(
        Q(client=client) & ~Q(projecten=project)
    )

    if request.method == "POST":
        if form.is_valid():
            # voeg project toe aan stakeholder
            stakeholder = form.cleaned_data["stakeholder"]
            if stakeholder.client != client:
                return redirect("logout_syn", client_pk=client_pk)

            # add project to the stakeholder
            stakeholder.projecten.add(project)

            # add stakeholder to the project (still needed?)
            project.organisaties.add(stakeholder)

            # add all employees to the project
            werknemers = stakeholder.users.all()

            for employee in werknemers:
                if employee.client != client:
                    return redirect("logout_syn", client_pk=client_pk)

                project.permitted.add(employee)
                
                # send invitation mails to each employee
                send_mail(
                    f"{ client.name } Projecten - Uitnodiging voor project {project}",
                    f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van { client.name }.
                    
                    U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/pvetool/{ client_pk }/project/{project.id}""",
                    "admin@pvegenerator.net",
                    [f"{employee.email}"],
                    fail_silently=False,
                )

            return redirect("getprojectpartijen", client_pk=client_pk, pk=pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["project"] = project
    context["form"] = form
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "partials/projectpartijen_form.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def SOGAddDerdenToProj(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    allowed_users = ["SOG"]

    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)

    if not client.project.filter(id=pk):
        return redirect("logout_syn", client_pk=client_pk)

    project = client.project.filter(id=pk).first()

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    if request.method == "POST":
        form = forms.SOGAddDerdenForm(request.POST)
        form.fields["stakeholder"].queryset = Organisatie.objects.filter(
            client=client
        ).all()
 
        # check whether it's valid:
        if form.is_valid():
            stakeholders = form.cleaned_data["stakeholder"]
            
            # add stakeholder to the project
            project.organisaties.add(*stakeholders)

            # and vice versa
            for stakeholder in stakeholders:
                stakeholder.projecten.add(project)

            # grab all users from the stakeholder and send invitation email to the project
            if stakeholders:
                stakeholder_users = [stakeholder.users.all() for stakeholder in stakeholders]

                for user_list in stakeholder_users:
                    project.permitted.add(*user_list)
                    
                    for user in user_list:
                        send_mail(
                            f"{ client.name } Projecten - Uitnodiging voor project {project}",
                            f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van { client.name }.
                            
                            U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                            Link: https://pvegenerator.net/pvetool/{ client_pk }/project/{project.id}""",
                            "admin@pvegenerator.net",
                            [f"{user.email}"],
                            fail_silently=False,
                        )

            return redirect("dashboard_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
    form = forms.SOGAddDerdenForm()
    form.fields["stakeholder"].queryset = Organisatie.objects.filter(
        client=client
    ).all()

    context = {}
    context["form"] = form
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "SOGAddDerde.html", context)

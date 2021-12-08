from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from geopy.geocoders import Nominatim
from django.db.models import Q
from project.models import Beleggers, Project
from users.models import CustomUser
from pvetool import forms
from pvetool.forms import StartProjectForm
from pvetool.views.utils import GetAWSURL
from users.models import CustomUser, Organisatie
from django.urls import reverse_lazy
from django.http import Http404, HttpResponse, HttpResponseRedirect


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def ManageProjects(request, client_pk):
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

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)
    projecten = client.project.all().order_by("-date_recent_verandering")

    new_projecten = []
    old_projecten = []

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

    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)

    if request.method == "POST":
        form = forms.StartProjectForm(request.POST)

        if form.is_valid():
            form.save()

            project = Project.objects.all().order_by("-id")[0]
            project.permitted.add(request.user)
            project.client = client
            project.first_annotate = form.cleaned_data["first_annotate"]

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
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "partials/tests_error.html")

    client = Beleggers.objects.filter(pk=client_pk).first()

    if (
        request.user.client.id != client.id
        and request.user.type_user != "B"
    ):
        return render(request, "partials/tests_error.html")

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "partials/tests_error.html")

    project = get_object_or_404(Project, id=pk)
    if project.client != client:
        return render(request, "partials/tests_error.html")

    context = {}
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/projectmanager_detail.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,},))
def DeleteProject(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "partials/tests_error.html")

    client = Beleggers.objects.filter(pk=client_pk).first()

    if (
        request.user.client.id != client.id
        and request.user.type_user != "B"
    ):
        return render(request, "partials/tests_error.html")

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "partials/tests_error.html")

    project = get_object_or_404(Project, id=pk)
    if project.client != client:
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
    client = Beleggers.objects.get(id=client_pk)
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)
    project = Project.objects.get(id=pk)
    form = forms.AddProjectmanagerToProjectForm(request.POST or None)
    form.fields["projectmanager"].queryset = CustomUser.objects.filter(
        type_user="SOG", client=client
    )
    form.fields["projectmanager"].initial = project.projectmanager

    context = {}
    context["client_pk"] = client_pk
    context["project"] = project
    context["projectmanager"] = project.projectmanager

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if form.cleaned_data["projectmanager"].client != client:
                return render(request, "partials/tests_error.html")

            if project.projectmanager == form.cleaned_data["projectmanager"]:
                return render(request, "partials/projectmanager_detail.html", context)

            project.projectmanager = form.cleaned_data["projectmanager"]

            if form.cleaned_data["projectmanager"] not in project.permitted.all():
                project.permitted.add(form.cleaned_data["projectmanager"])
            project.save()

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

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
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

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, id=pk)
    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)
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

            stakeholder.projecten.add(project)

            # voeg stakeholder toe aan project
            project.organisaties.add(stakeholder)

            # geef alle werknemers toegang aan het project
            werknemers = stakeholder.users.all()

            for employee in werknemers:
                if employee.client != client:
                    return redirect("logout_syn", client_pk=client_pk)

                project.permitted.add(employee)

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
        # check whether it's valid:
        if form.is_valid():
            permitted = form.cleaned_data["permitted"]
            project.permitted.add(*permitted)

            if permitted:
                users = [user for user in permitted]

                for user in users:
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
    form.fields["permitted"].queryset = CustomUser.objects.filter(
        type_user="SD", client=client
    ).all()

    context = {}
    context["form"] = form
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "SOGAddDerde.html", context)

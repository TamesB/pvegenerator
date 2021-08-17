from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from geopy.geocoders import Nominatim

from project.models import Beleggers, Project
from users.models import CustomUser
from syntrus import forms
from syntrus.forms import StartProjectForm


@login_required(login_url="login_syn")
def ManageProjects(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    context = {}
    context["projecten"] = Project.objects.all().order_by("-datum_recent_verandering")
    return render(request, "beheerProjecten_syn.html", context)


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
            return redirect("connectpve_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = StartProjectForm()
    return render(request, "plusProject_syn.html", context)


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
def SOGAddDerdenToProj(request, pk):
    allowed_users = ["SOG"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    project = Project.objects.filter(id=pk).first()

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.SOGAddDerdenForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            permitted = form.cleaned_data["permitted"]

            for permit in permitted:
                project.permitted.add(permit)

            project.save()

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

            return redirect("dashboard_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
    form = forms.SOGAddDerdenForm()
    form.fields["permitted"].queryset = CustomUser.objects.filter(
        type_user="SD"
    ).all()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, "SOGAddDerde.html", context)

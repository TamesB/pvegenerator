from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.http.response import HttpResponse
from pvetool import forms
from pvetool.forms import AddOrganisatieForm
from users.models import Organisatie
from project.models import Beleggers
from pvetool.views.utils import GetAWSURL
from users.models import CustomUser
from django.db.models import Q
from django.urls import reverse_lazy
from project.models import Project

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def ManageOrganisaties(request, client_pk):
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

    context = {}
    context["organisaties"] = Organisatie.objects.filter(client=client)
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "organisatieManager.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddOrganisatie(request, client_pk):
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
        form = forms.AddOrganisatieForm(request.POST)

        if form.is_valid():
            new_organisatie = Organisatie()
            new_organisatie.name = form.cleaned_data["name"]
            new_organisatie.client = client
            new_organisatie.save()
            messages.warning(
                request, f"Organisatie {form.cleaned_data['name']} aangemaakt."
            )
            return redirect("manageorganisaties_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["organisaties"] = Organisatie.objects.filter(client=client)
    context["form"] = AddOrganisatieForm()
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "organisatieAdd.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteOrganisatie(request, client_pk, pk):
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

    stakeholder = get_object_or_404(Organisatie, id=pk)
    if stakeholder.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    if request.method == "POST":
        name = stakeholder.name
        stakeholder.delete()
        messages.warning(request, f"Organisatie {name} verwijderd.")
        return HttpResponse("")

    return redirect("manageorganisaties_syn", client_pk=client_pk)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddUserOrganisatie(request, client_pk, pk):
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
    if not Organisatie.objects.filter(id=pk):
        return redirect("logout_syn", client_pk=client_pk)

    stakeholder = Organisatie.objects.filter(id=pk, client=client).first()
    organisaties = Organisatie.objects.filter(client=client)
    form = forms.AddUserToOrganisatieForm(request.POST or None)
    form.fields["employee"].queryset = CustomUser.objects.filter(
        ~Q(stakeholder=stakeholder) & Q(type_user="SD") & Q(client=client)
    )

    if request.method == "POST":
        # get user entered form

        # check validity
        if form.is_valid():
            employee = form.cleaned_data["employee"]
            if employee.client != client:
                return redirect("logout_syn", client_pk=client_pk)

            stakeholder.users.add(employee)

            # add new user to all projects the organisation works with
            projects = stakeholder.projecten.all()

            for project in projects:
                if (
                    employee not in project.permitted.all()
                    and project.client == client
                ):
                    project.permitted.add(employee)
                    project.save()

            stakeholder.save()

            send_mail(
                f"{ client.name } Projecten - Toegevoegd aan stakeholder {stakeholder.name}",
                f"""{ request.user } heeft u toegevoegd aan de stakeholder {stakeholder.name}.
                
                Een stakeholder kan toegevoegd worden aan projecten en werknemers krijgen dan automatisch toegang tot deze projecten.
                U kunt uw huidige projecten bekijken bij https://pvegenerator.net/pvetool/{client.id}/projects""",
                "admin@pvegenerator.net",
                [f"{employee.email}"],
                fail_silently=False,
            )
            messages.warning(
                request,
                f"{employee.username} toegevoegd aan stakeholder {stakeholder.name}. Een notificatie is gemaild naar deze persoon.",
            )
            return redirect(
                "getusersorganisatie", client_pk=client_pk, pk=stakeholder.id
            )
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = form
    context["pk"] = pk
    context["stakeholder"] = stakeholder
    context["organisaties"] = organisaties
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "partials/organisatieadduser_form.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetUsersInOrganisatie(request, client_pk, pk):
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
    if not Organisatie.objects.filter(id=pk):
        return redirect("logout_syn", client_pk=client_pk)

    stakeholder = Organisatie.objects.filter(id=pk, client=client).first()
    organisaties = Organisatie.objects.filter(client=client)

    context = {}
    context["pk"] = pk
    context["stakeholder"] = stakeholder
    context["organisaties"] = organisaties
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "partials/organisatie_detail.html", context)

def OrganisatieRemoveFromProject(request, client_pk, organisatie_pk, project_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()

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
    if not Organisatie.objects.filter(id=organisatie_pk):
        return redirect("logout_syn", client_pk=client_pk)

    stakeholder = Organisatie.objects.get(id=organisatie_pk)
    project = Project.objects.get(id=project_pk)

    if project in stakeholder.projecten.all():
        stakeholder.projecten.remove(project)

    if stakeholder in project.organisaties.all():
        project.organisaties.remove(stakeholder)
        
    for user in stakeholder.users.all():
        if user in project.permitted.all():
            project.permitted.remove(user)

    messages.warning(request, f"Project { project.name } verwijderd uit stakeholder { stakeholder.name }")
    return HttpResponse("")

def GebruikerRemoveFromOrganisatie(request, client_pk, organisatie_pk, user_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()

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
    if not CustomUser.objects.filter(id=user_pk):
        return redirect("logout_syn", client_pk=client_pk)

    stakeholder = Organisatie.objects.get(id=organisatie_pk)
    user = CustomUser.objects.get(id=user_pk)

    if user.client.id != client.id:
        return redirect("logout_syn", client_pk=client_pk)

    if user in stakeholder.users.all():
        stakeholder.users.remove(user)
        
    for project in stakeholder.projecten.all():
        if project in user.projectspermitted.all():
            user.projectspermitted.remove(project)

    if stakeholder == user.stakeholder:
        user.stakeholder = None
        user.save()

    messages.warning(request, f"Gebruiker { user.username } verwijderd uit stakeholder { stakeholder.name }")
    return HttpResponse("")
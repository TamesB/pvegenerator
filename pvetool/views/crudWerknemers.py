import datetime
import secrets

import pytz
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse_lazy

from project.models import Project, Beleggers
from pvetool import forms
from users.forms import AcceptInvitationForm
from users.models import CustomUser, Invitation
from pvetool.views.utils import GetAWSURL
from users.models import Organisatie

utc = pytz.UTC


@login_required(
    login_url=reverse_lazy(
        "login_syn",
        args={
            1,
        },
    )
)
def ManageWerknemers(request, client_pk):
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
    context["werknemers"] = (
        client.employee.all()
        .filter(Q(type_user="SD") | Q(type_user="SOG"))
        .order_by("-last_visit")
    )
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "beheerWerknemers_syn.html", context)


@login_required(
    login_url=reverse_lazy(
        "login_syn",
        args={
            1,
        },
    )
)
def AddAccount(request, client_pk):
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

    allowed_users = ["B", "SB", "SOG"]
    staff_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)

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
            invitation.client = client

            if form.cleaned_data["project"]:
                invitation.project = form.cleaned_data["project"]
            if form.cleaned_data["stakeholder"]:
                invitation.stakeholder = form.cleaned_data["stakeholder"]

            # Als pvetool beheerder invitatie doet kan hij ook rang geven (projectmanager/derde)
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
                    f"{ client.name } Projecten - Uitnodiging voor de PvE tool",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor een of meerdere projecten van { client.name }.
                    
                    Klik op de uitnodigingslink om rechtstreeks de tool in te gaan.
                    Link: https://pvegenerator.net/pvetool/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    "admin@pvegenerator.net",
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )
            else:
                send_mail(
                    f"{ client.name } Projecten - Uitnodiging voor de PvE tool",
                    f"""{ request.user } nodigt u uit voor het commentaar leveren en het checken van het Programma van Eisen voor een of meerdere projecten van { client.name }.
                    
                    Uw stappenplan:
                    1. Volg de link hieronder en maak een wachtwoord aan. Uw usersname wordt naar u gemaild.
                    2. Check uw projecten op de dashboard of bij "Mijn Projecten" in het uitschuifmenu links.
                    3. Check de projectpagina's en volg de To Do stappen om commentaar te leveren op de regels.

                    Klik op de uitnodigingslink om rechtstreeks de tool in te gaan.
                    Link: https://pvegenerator.net/pvetool/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    "admin@pvegenerator.net",
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )

            messages.warning(
                request,
                f"Uitnodiging verstuurd naar { form.cleaned_data['invitee'] }. De uitnodiging zal verlopen in { expiry_length } dagen.)",
            )
            return redirect("dashboard_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    projecten = Project.objects.filter(
        permitted__username__iregex=r"\y{0}\y".format(request.user.username)
    )

    if request.user.type_user in staff_users:
        form = forms.PlusAccountForm()
    else:
        form = forms.KoppelDerdeUserForm()

    form.fields["project"].queryset = Project.objects.filter(client=client)
    form.fields["stakeholder"].queryset = Organisatie.objects.filter(
        client=client
    )

    context = {}
    context["form"] = form

    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url

    if request.user.type_user in staff_users:
        return render(request, "plusAccount_syn.html", context)
    else:
        return render(request, "plusDerde_syn.html", context)


def AcceptInvite(request, client_pk, key):
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

    if not key or not Invitation.objects.filter(key=key):
        return redirect("logout_syn", client_pk=client_pk)

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
            if invitation.stakeholder:
                user.stakeholder = invitation.stakeholder
            if invitation.client:
                user.client = invitation.clienteorganisatie

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

            if invitation.stakeholder:
                stakeholder = invitation.stakeholder
                stakeholder.users.add(user)
                stakeholder.save()

            invitation.delete()

            send_mail(
                f"{ client.name } Projecten - Uw Logingegevens",
                f"""Reeds heeft u zich aangemeld bij de PvE tool.
                Voor het vervolgens inloggen op de tool is uw usersname: {user.username}
                en het wachtwoord wat u heeft aangegeven bij het aanmelden.""",
                "admin@pvegenerator.net",
                [f"{invitation.invitee}"],
                fail_silently=False,
            )
            if user is not None:
                login(request, user)
                messages.warning(
                    request,
                    f"Account aangemaakt met usersname: {user.username}. Uw logingegevens zijn naar u gemaild.",
                )
                return redirect("viewprojectoverview_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "acceptInvitation_syn.html", context)


@login_required(
    login_url=reverse_lazy(
        "login_syn",
        args={
            1,
        },
    )
)
def InviteUsersToProject(request, client_pk, pk):
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

    project = Project.objects.filter(id=pk).first()

    if request.method == "POST":
        form = forms.InviteProjectStartForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            organisaties = form.cleaned_data["organisaties"]
            projectmanager = form.cleaned_data["projectmanager"]
            permitted = form.cleaned_data["permitted"]

            for user in permitted:
                if user.client != client:
                    return redirect("logout_syn", client_pk=client_pk)

            project.projectmanager = projectmanager
            project.organisaties.add(*organisaties)
            project.permitted.add(*permitted)
            project.save()

            if organisaties:
                organisaties = [stakeholder for stakeholder in organisaties]
                users = []

                for stakeholder in organisaties:
                    userSet = [user for user in stakeholder.users.all()]
                    users.append(userSet)
                    stakeholder.projecten.add(project)
                    stakeholder.save()

                for user in users:
                    send_mail(
                        f"{ client.name } Projecten - Uitnodiging voor project {project}",
                        f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van { client.name }.
                        
                        U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                        Link: https://pvegenerator.net/pvetool/project/{project.id}""",
                        "admin@pvegenerator.net",
                        [f"{user.email}"],
                        fail_silently=False,
                    )

            if projectmanager:
                send_mail(
                    f"{ client.name } Projecten - Uitnodiging voor project {project}",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor het project { project } van { client.name }.
                    
                    U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/pvetool/project/{project.id}""",
                    "admin@pvegenerator.net",
                    [f"{projectmanager.email}"],
                    fail_silently=False,
                )

            if permitted:
                users = [user for user in permitted]

                for user in users:
                    send_mail(
                        f"{ client.name } Projecten - Uitnodiging voor project {project}",
                        f"""{ request.user } heeft u uitgenodigd om mee te werken aan het project { project } van { client.name }.
                        
                        U heeft nu toegang tot dit project. Klik op de link om rechtstreeks het project in te gaan.
                        Link: https://pvegenerator.net/pvetool/project/{project.id}""",
                        "admin@pvegenerator.net",
                        [f"{user.email}"],
                        fail_silently=False,
                    )
            messages.warning(
                request,
                f"Personen zijn uitgenodigd en de uitnodigings E-Mails zijn succesvol verstuurd.",
            )
            return redirect("connectpve_syn", client_pk=client_pk, pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
    form = forms.InviteProjectStartForm()
    form.fields["organisaties"].queryset = Organisatie.objects.filter(
        client=client
    )

    context = {}
    context["form"] = form
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "InviteUsersToProject_syn.html", context)

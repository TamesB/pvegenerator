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

from project.models import Project
from syntrus import forms
from users.forms import AcceptInvitationForm
from users.models import CustomUser, Invitation

utc = pytz.UTC


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

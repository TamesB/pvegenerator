import secrets

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from project.models import Project, Beleggers
from syntrus.views.utils import GetAWSURL
from . import forms, models


# Create your views here.
@staff_member_required
def signup(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.get(pk=client_pk)
    logo_url = GetAWSURL(client)

    if request.method == "POST":
        form = forms.CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.warning(request, "Account aangemaakt.")
            return redirect("accoverview")
    else:
        form = forms.CustomUserCreationForm()
    context = {}
    context["form"] = form
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "createAccount.html", context)


@staff_member_required
def accountOverview(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.get(pk=client_pk)
    logo_url = GetAWSURL(client)

    users = models.CustomUser.objects.all()

    context = {}
    context["users"] = users
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "accountOverview.html", context)


@staff_member_required
def accountProfile(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.get(pk=client_pk)
    logo_url = GetAWSURL(client)

    if not models.CustomUser.objects.filter(id=pk):
        return Http404("404")

    user = models.CustomUser.objects.filter(id=pk).first()
    projects = user.projectspermitted.all()
    context = {}
    context["user"] = request.user
    context["projects"] = projects
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "accProfile.html", context)


def ForgotPassword(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.get(pk=client_pk)
    logo_url = GetAWSURL(client)

    if request.user.is_authenticated:
        raise Http404("404_syn.html")

    if request.method == "POST":
        # get user entered form
        form = forms.ForgotPassForm(request.POST)
        # check validity
        if form.is_valid():
            invitation = models.ForgotPassInvite()

            # filter either username or email from the input
            if "@" in form.cleaned_data["email"]:
                email = form.cleaned_data["email"]
                email = email.split("@")
                username = email[0]
                if not models.CustomUser.objects.filter(
                    username=username

                ):
                    return redirect("login_syn")
                else:
                    user = models.CustomUser.objects.get(
                        username=username
                    )
            else:
                if not models.CustomUser.objects.filter(
                    username=form.cleaned_data["email"]
                ):
                    return redirect("login_syn")
                else:
                    user = models.CustomUser.objects.get(
                        username=form.cleaned_data["email"]
                    )

            invitation.user = user
            expiry_length = 10
            expire_date = timezone.now() + timezone.timedelta(expiry_length)
            invitation.expires = expire_date
            invitation.key = secrets.token_urlsafe(30)
            invitation.save()

            send_mail(
                f"Syntrus Projecten - Wachtwoord Reset",
                f"""U heeft aangevraagd uw wachtwoord te resetten. Klik op de link om uw wachtwoord opnieuw in te stellen.
                
                Link: https://pvegenerator.net/beheer/users/passreset/{invitation.key}
                
                Deze link is 10 dagen geldig.""",
                "admin@pvegenerator.net",
                [f"{user.email}"],
                fail_silently=False,
            )

            messages.warning(
                request,
                f"Er is een E-mail verstuurd gekoppeld aan dit account om het wachtwoord te veranderen. De uitnodiging zal verlopen in { expiry_length } dagen.)",
            )
            return redirect("login_syn")

    context = {}
    context["form"] = forms.ForgotPassForm()
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "ForgotPassword.html", context)


def ResetPassword(request, client_pk, key):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.get(pk=client_pk)
    logo_url = GetAWSURL(client)

    if not models.ForgotPassInvite.objects.filter(key=key):
        raise Http404("404_syn.html")

    invitation = models.ForgotPassInvite.objects.get(key=key)
    if timezone.now() > invitation.expires:
        invitation.delete()
        raise Http404("404_syn.html")

    if request.method == "POST":
        form = forms.ResetPassForm(request.POST)

        if form.is_valid():
            user = invitation.user
            user.set_password(form.cleaned_data["password1"])
            user.save()
            invitation.delete()
            messages.warning(request, f"Wachtwoord veranderd, login met uw account.")

            return redirect("login_syn")

    context = {}
    context["form"] = forms.ResetPassForm()
    context["key"] = key
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "ResetPassword.html", context)
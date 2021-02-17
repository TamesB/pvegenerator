from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from . import models
from project.models import Project
from . import forms
from django.utils import timezone
import secrets
from django.core.mail import send_mail

# Create your views here.
@staff_member_required
def signup(request):
    if request.method == 'POST':
        form = forms.CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.warning(request, 'Account aangemaakt.')
            return redirect('accoverview')
    else:
        form = forms.CustomUserCreationForm()

    return render(request, 'createAccount.html', {'form': form})

@staff_member_required
def accountOverview(request):
    users = models.CustomUser.objects.all()

    context = {}
    context['users'] = users
    return render(request, 'accountOverview.html', context)

@staff_member_required
def accountProfile(request, pk):
    if not models.CustomUser.objects.filter(id=pk):
        return Http404('404')

    user = models.CustomUser.objects.filter(id=pk).first()
    projects = Project.objects.filter(permitted__username__contains=user.username)
    context = {}
    context['user'] = user
    context['projects'] = projects
    return render(request, 'accProfile.html', context)

def ForgotPassword(request):
    if request.user.is_authenticated:
        raise Http404('404_syn.html')

    if request.method == "POST":
        # get user entered form
        form = forms.ForgotPassForm(request.POST)
        # check validity
        if form.is_valid():
            invitation = models.ForgotPassInvite()

            # filter either username or email from the input
            if "@" in form.cleaned_data["email"]:
                if not models.CustomUser.objects.filter(email=form.cleaned_data["email"]):
                    return redirect("login_syn")
                else:
                    user = models.CustomUser.objects.get(email=form.cleaned_data["email"])
            else:
                if not models.CustomUser.objects.filter(username=form.cleaned_data["email"]):
                    return redirect("login_syn")
                else:
                    user = models.CustomUser.objects.get(username=form.cleaned_data["email"])

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
                'admin@pvegenerator.net',
                [f'{user.email}'],
                fail_silently=False,
            )

            messages.warning(request, f"Er is een E-mail verstuurd gekoppeld aan dit account om het wachtwoord te veranderen. De uitnodiging zal verlopen in { expiry_length } dagen.)")
            return redirect("login_syn")

    context = {}
    context["form"] = forms.ForgotPassForm()
    return render(request, 'ForgotPassword.html', context)

def ResetPassword(request, key):
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

            return redirect('login_syn')

    context = {}
    context["form"] = forms.ResetPassForm()
    context["key"] = key
    return render(request, 'ResetPassword.html', context)

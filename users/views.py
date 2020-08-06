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
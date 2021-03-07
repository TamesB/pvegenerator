from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from syntrus import forms
from syntrus.forms import AddOrganisatieForm
from users.models import Organisatie


@login_required(login_url="login_syn")
def ManageOrganisaties(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    context = {}
    context["organisaties"] = Organisatie.objects.all()
    return render(request, "organisatieManager.html", context)


@login_required(login_url="login_syn")
def AddOrganisatie(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.AddOrganisatieForm(request.POST)

        if form.is_valid():
            new_organisatie = Organisatie()
            new_organisatie.naam = form.cleaned_data["naam"]
            new_organisatie.save()
            return redirect("manageorganisaties_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["organisaties"] = Organisatie.objects.all()
    context["form"] = AddOrganisatieForm()
    return render(request, "organisatieAdd.html", context)


@login_required(login_url="login_syn")
def DeleteOrganisatie(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    organisatie = get_object_or_404(Organisatie, id=pk)

    if request.method == "POST":
        organisatie.delete()
        return redirect("manageorganisaties_syn")

    context = {}
    context["organisatie"] = organisatie
    context["organisaties"] = Organisatie.objects.all()
    return render(request, "organisatieDelete.html", context)


@login_required(login_url="login_syn")
def AddUserOrganisatie(request, pk):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")
    if not Organisatie.objects.filter(id=pk):
        return render(request, "404_syn.html")

    organisatie = Organisatie.objects.filter(id=pk).first()
    organisaties = Organisatie.objects.all()

    if request.method == "POST":
        # get user entered form
        form = forms.AddUserToOrganisatieForm(request.POST)

        # check validity
        if form.is_valid():
            werknemer = form.cleaned_data["werknemer"]
            organisatie.gebruikers.add(werknemer)

            # add new user to all projects the organisation works with
            projects = organisatie.projecten.all()

            for project in projects:
                if werknemer not in project.permitted.all():
                    project.permitted.add(werknemer)
                    project.save()

            organisatie.save()

            send_mail(
                f"Syntrus Projecten - Toegevoegd aan organisatie {organisatie.naam}",
                f"""{ request.user } heeft u toegevoegd aan de organisatie {organisatie.naam}.
                
                Een organisatie kan toegevoegd worden aan projecten en werknemers krijgen dan automatisch toegang tot deze projecten.
                U kunt uw huidige projecten bekijken bij https://pvegenerator.net/syntrus/projects""",
                "admin@pvegenerator.net",
                [f"{werknemer.email}"],
                fail_silently=False,
            )
            return redirect("manageorganisaties_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    form = forms.AddUserToOrganisatieForm()

    context = {}
    context["form"] = form
    context["pk"] = pk
    context["organisatie"] = organisatie
    context["organisaties"] = organisaties
    return render(request, "organisatieAddUser.html", context)

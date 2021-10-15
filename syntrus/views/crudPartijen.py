from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from syntrus import forms
from syntrus.forms import AddOrganisatieForm
from users.models import Organisatie
from project.models import Beleggers
from syntrus.views.utils import GetAWSURL
from users.models import CustomUser

@login_required(login_url="login_syn")
def ManageOrganisaties(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    context = {}
    context["organisaties"] = Organisatie.objects.filter(klantenorganisatie=client)
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "organisatieManager.html", context)


@login_required(login_url="login_syn")
def AddOrganisatie(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.AddOrganisatieForm(request.POST)

        if form.is_valid():
            new_organisatie = Organisatie()
            new_organisatie.naam = form.cleaned_data["naam"]
            new_organisatie.klantenorganisatie = client
            new_organisatie.save()
            messages.warning(
                request, f"Organisatie {form.cleaned_data['naam']} aangemaakt."
            )
            return redirect("manageorganisaties_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["organisaties"] = Organisatie.objects.filter(klantenorganisatie=client)
    context["form"] = AddOrganisatieForm()
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "organisatieAdd.html", context)


@login_required(login_url="login_syn")
def DeleteOrganisatie(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    organisatie = get_object_or_404(Organisatie, id=pk)
    if organisatie.klantenorganisatie != client:
        return render(request, "404_syn.html")

    if request.method == "POST":
        naam = organisatie.naam
        organisatie.delete()
        messages.warning(
            request, f"Organisatie {naam} verwijderd."
        )
        return redirect("manageorganisaties_syn", client_pk=client_pk)

    context = {}
    context["organisatie"] = organisatie
    context["organisaties"] = Organisatie.objects.filter(klantenorganisatie=client)
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "organisatieDelete.html", context)


@login_required(login_url="login_syn")
def AddUserOrganisatie(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")
    if not Organisatie.objects.filter(id=pk):
        return render(request, "404_syn.html")

    organisatie = Organisatie.objects.filter(id=pk, klantenorganisatie=client).first()
    organisaties = Organisatie.objects.filter(klantenorganisatie=client)

    if request.method == "POST":
        # get user entered form
        form = forms.AddUserToOrganisatieForm(request.POST)

        # check validity
        if form.is_valid():
            werknemer = form.cleaned_data["werknemer"]
            if werknemer.klantenorganisatie != client:
                return render(request, "404_syn.html")

            organisatie.gebruikers.add(werknemer)

            # add new user to all projects the organisation works with
            projects = organisatie.projecten.all()

            for project in projects:
                if werknemer not in project.permitted.all() and project.belegger == client:
                    project.permitted.add(werknemer)
                    project.save()

            organisatie.save()

            send_mail(
                f"Syntrus Projecten - Toegevoegd aan organisatie {organisatie.naam}",
                f"""{ request.user } heeft u toegevoegd aan de organisatie {organisatie.naam}.
                
                Een organisatie kan toegevoegd worden aan projecten en werknemers krijgen dan automatisch toegang tot deze projecten.
                U kunt uw huidige projecten bekijken bij https://pvegenerator.net/pvetool/projects""",
                "admin@pvegenerator.net",
                [f"{werknemer.email}"],
                fail_silently=False,
            )
            messages.warning(
                request, f"{werknemer.username} toegevoegd aan organisatie {organisatie.naam}. Een notificatie is gemaild naar deze persoon."
            )
            return redirect("manageorganisaties_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    form = forms.AddUserToOrganisatieForm()
    form.fields["werknemer"].queryset = CustomUser.objects.filter(klantenorganisatie=client)

    context = {}
    context["form"] = form
    context["pk"] = pk
    context["organisatie"] = organisatie
    context["organisaties"] = organisaties
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "organisatieAddUser.html", context)

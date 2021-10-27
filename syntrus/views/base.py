import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from app import models
from project.models import Project, PVEItemAnnotation, Beleggers, BeheerdersUitnodiging, BijlageToAnnotation
from syntrus import forms
from syntrus.models import FAQ
from utils import createBijlageZip, writePdf, pve_csv_extract
from syntrus.views.utils import GetAWSURL
from users.models import CustomUser
from users.forms import AcceptInvitationForm
from django.utils import timezone

def LoginView(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            return redirect("dashboard_syn", client_pk=client_pk)

    if request.method == "POST":
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            (username, password) = (
                form.cleaned_data["username"],
                form.cleaned_data["password"],
            )
            
            if "@" in username:
                email = username.split("@")
                email = email[0]

                user_check = CustomUser.objects.filter(username=email)

                if user_check.exists():
                    user_check = user_check.first()
                    user = authenticate(request, username=email, password=password)
                else:
                    messages.warning(request, "Invalid login credentials")
            else:
                user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.klantenorganisatie == client and user.type_user != "B":
                    login(request, user)
                    return redirect("dashboard_syn", client_pk=client_pk)

                messages.warning(request, "Invalid login credentials")
            else:
                messages.warning(request, "Invalid login credentials")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # render the page
    context = {}
    context["form"] = forms.LoginForm()
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "login_syn.html", context)

def BeheerdersAcceptUitnodiging(request, client_pk, key):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if not key or not BeheerdersUitnodiging.objects.filter(key=key):
        return redirect("logout_syn", client_pk=client_pk)

    invitation = BeheerdersUitnodiging.objects.filter(key=key).first()

    if timezone.now() > invitation.expires:
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
            if invitation.klantenorganisatie:
                user.klantenorganisatie = invitation.klanteorganisatie

            user.save()

            klant = invitation.klantenorganisatie
            klant.beheerder = user
            klant.save()

            user = authenticate(
                request, username=username, password=form.cleaned_data["password1"]
            )

            invitation.delete()

            send_mail(
                f"{klant.naam} PvE Tool - Uw Logingegevens",
                f"""Reeds heeft u zich aangemeld bij de PvE tool.
                Voor het vervolgens inloggen op de tool is uw gebruikersnaam: {user.username}
                en het wachtwoord wat u heeft aangegeven bij het aanmelden.""",
                "admin@pvegenerator.net",
                [f"{invitation.invitee}"],
                fail_silently=False,
            )
            if user is not None:
                login(request, user)
                messages.warning(request, f"Account aangemaakt met gebruikersnaam: {user.username}. Uw logingegevens zijn naar u gemaild.")
                return redirect("dashboard_syn")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "acceptBeheerderInvite.html", context)

def LogoutView(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    logout(request)
    return redirect("login_syn", client_pk=client_pk)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DashboardView(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)
    if request.user.klantenorganisatie:
        if request.user.klantenorganisatie.id != client.id and request.user.type_user != "B":
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    context = {}
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    
    if request.user.projectspermitted.all().filter(belegger__id=client_pk).exists():
        projects = request.user.projectspermitted.all().filter(belegger__id=client_pk)
        context["projects"] = projects


        if request.user.annotation.exists():
            opmerkingen = request.user.annotation.all()
            context["opmerkingen"] = opmerkingen

        medewerkers = [proj.permitted.all() for proj in projects]

        derden_toegevoegd = []
        for medewerker_list in medewerkers:
            derdes = False
            for medewerker in medewerker_list:
                if medewerker.type_user == "SD":
                    derdes = True
            derden_toegevoegd.append(derdes)
            
        context["derden_toegevoegd"] = derden_toegevoegd
        context["first_annotate"] = [project.first_annotate for project in projects]
    else:
        context["projects"] = None
        context["opmerkingen"] = None
        context["derden_toegevoegd"] = None
        context["first_annotate"] = None

    if request.user.type_user == "B":
        return render(request, "dashboardBeheerder_syn.html", context)
    if request.user.type_user == "SB":
        return render(request, "dashboardBeheerder_syn.html", context)
    if request.user.type_user == "SOG":
        return render(request, "dashboardOpdrachtgever_syn.html", context)
    if request.user.type_user == "SD":
        return render(request, "dashboardDerde_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def FAQView(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)
    if request.user.klantenorganisatie:
        if request.user.klantenorganisatie.id != client.id and request.user.type_user != "B":
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    faqquery = FAQ.objects.all()
    if request.user.type_user == "SB":
        faqquery = FAQ.objects.filter(gebruikersrang="SB")
    if request.user.type_user == "SOG":
        faqquery = FAQ.objects.filter(gebruikersrang="SOG")
    if request.user.type_user == "SD":
        faqquery = FAQ.objects.filter(gebruikersrang="SD")

    context = {}
    context["faqquery"] = faqquery
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url    
    return render(request, "FAQ_syn.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def KiesPVEGenerate(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.klantenorganisatie:
        if request.user.klantenorganisatie.id != client.id and request.user.type_user != "B":
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.id is not client.beheerder.id and request.user.type_user != "B":
        return redirect("logout_syn", client_pk=client_pk)

    form = forms.PVEVersieKeuzeForm(request.POST or None)
    form.fields["pve_versie"].queryset = models.PVEVersie.objects.filter(belegger=client, public=True)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            return redirect("generate_syn", client_pk=client_pk, versie_pk=form.cleaned_data["pve_versie"].id)

    context = {}
    context["form"] = form
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "kiespvegenereer.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def GeneratePVEView(request, client_pk, versie_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()

    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.klantenorganisatie:
        if request.user.klantenorganisatie.id != client.id and request.user.type_user != "B":
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)
        
    if request.user.id is not client.beheerder.id and request.user.type_user != "B":
        return redirect("logout_syn", client_pk=client_pk)

    if not models.PVEVersie.objects.filter(pk=versie_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)
    else:
        versie = models.PVEVersie.objects.filter(pk=versie_pk).first()

    if request.method == "POST":
        # get user entered form
        form = forms.PVEParameterForm(request.POST)

        bouwsoort = versie.bouwsoort.all()
        form.fields["Bouwsoort1"].queryset = bouwsoort
        form.fields["Bouwsoort2"].queryset = bouwsoort
        form.fields["Bouwsoort3"].queryset = bouwsoort

        typeObject = versie.typeobject.all()
        form.fields["TypeObject1"].queryset = typeObject
        form.fields["TypeObject2"].queryset = typeObject
        form.fields["TypeObject3"].queryset = typeObject

        doelgroep = versie.doelgroep.all()
        form.fields["Doelgroep1"].queryset = doelgroep
        form.fields["Doelgroep2"].queryset = doelgroep
        form.fields["Doelgroep3"].queryset = doelgroep

        # check validity
        if form.is_valid():
            # get parameters, find all pveitems with that
            (
                Bouwsoort1,
                TypeObject1,
                Doelgroep1,
                Bouwsoort2,
                TypeObject2,
                Doelgroep2,
                Bouwsoort3,
                TypeObject3,
                Doelgroep3,
                Smarthome,
                AED,
                EntreeUpgrade,
                Pakketdient,
                JamesConcept,
            ) = (
                form.cleaned_data["Bouwsoort1"],
                form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"],
                form.cleaned_data["Bouwsoort2"],
                form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"],
                form.cleaned_data["Bouwsoort3"],
                form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"],
                form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"],
                form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"],
                form.cleaned_data["JamesConcept"],
            )

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = versie.item.select_related("paragraaf").select_related("hoofdstuk").filter(basisregel=True)

            basic_PVE = basic_PVE.union(Bouwsoort1.item.select_related("hoofdstuk").select_related("paragraaf").all())

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(Bouwsoort2.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(Bouwsoort3.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if TypeObject1:
                basic_PVE = basic_PVE.union(TypeObject1.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if TypeObject2:
                basic_PVE = basic_PVE.union(TypeObject2.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if TypeObject3:
                basic_PVE = basic_PVE.union(TypeObject3.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if Doelgroep1:
                basic_PVE = basic_PVE.union(Doelgroep1.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if Doelgroep2:
                basic_PVE = basic_PVE.union(Doelgroep2.item.select_related("hoofdstuk").select_related("paragraaf").all())
            if Doelgroep3:
                basic_PVE = basic_PVE.union(Doelgroep3.item.select_related("hoofdstuk").select_related("paragraaf").all())

            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(versie.item.select_related("paragraaf").select_related("hoofdstuk").filter(AED=True))
            if Smarthome:
                basic_PVE = basic_PVE.union(versie.item.select_related("paragraaf").select_related("hoofdstuk").filter(Smarthome=True))
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(versie.item.select_related("paragraaf").select_related("hoofdstuk").filter(EntreeUpgrade=True))
            if Pakketdient:
                basic_PVE = basic_PVE.union(versie.item.select_related("paragraaf").select_related("hoofdstuk").filter(Pakketdient=True))
            if JamesConcept:
                basic_PVE = basic_PVE.union(versie.item.select_related("paragraaf").select_related("hoofdstuk").filter(JamesConcept=True))

            basic_PVE = basic_PVE.order_by("id")

            # make pdf
            parameters = []
            if Bouwsoort1:
                parameters += (f"{Bouwsoort1.parameter} (Hoofd)",)
            if Bouwsoort2:
                parameters += (f"{Bouwsoort2.parameter} (Sub)",)
            if Bouwsoort3:
                parameters += (f"{Bouwsoort3.parameter} (Sub)",)
            if TypeObject1:
                parameters += (f"{TypeObject1.parameter} (Hoofd)",)
            if TypeObject2:
                parameters += (f"{TypeObject2.parameter} (Sub)",)
            if TypeObject3:
                parameters += (f"{TypeObject3.parameter} (Sub)",)
            if Doelgroep1:
                parameters += (f"{Doelgroep1.parameter} (Hoofd)",)
            if Doelgroep2:
                parameters += (f"{Doelgroep2.parameter} (Sub)",)
            if Doelgroep3:
                parameters += (f"{Doelgroep3.parameter} (Sub)",)

            date = datetime.datetime.now()
            fileExt = "%s%s%s%s%s%s" % (
                date.strftime("%H"),
                date.strftime("%M"),
                date.strftime("%S"),
                date.strftime("%d"),
                date.strftime("%m"),
                date.strftime("%Y"),
            )
            
            filename = f"PvE-{fileExt}"
            zipFilename = f"PvE_Compleet-{fileExt}"
            pdfmaker = writePdf.PDFMaker(versie.versie, logo_url)
            opmerkingen = {}
            bijlagen = {}
            reacties = {}
            reactiebijlagen = {}

            pdfmaker.makepdf(
                filename,
                basic_PVE,
                versie.id,
                opmerkingen,
                bijlagen,
                reacties,
                reactiebijlagen,
                parameters,
                [],
            )

            # get bijlagen
            bijlagen_models = models.ItemBijlages.objects.all()
            bijlagen = []

            for bijlage_model in bijlagen_models:
                for item in bijlage_model.items.all():
                    if item in basic_PVE:
                        bijlagen.append(bijlage_model)

            bijlagen = list(set(bijlagen))
            
            if bijlagen:
                zipmaker = createBijlageZip.ZipMaker()
                zipmaker.makeZip(zipFilename, filename, bijlagen)
            else:
                zipFilename = False

            # and render the result page
            context = {}
            context["itemsPVE"] = basic_PVE
            context["filename"] = filename
            context["zipFilename"] = zipFilename
            return render(request, "PVEResult_syn.html", context)
        else:
            messages.warning(request, "Vul de verplichte keuzes in.")

    form = forms.PVEParameterForm()
    bouwsoort = versie.bouwsoort.all()
    form.fields["Bouwsoort1"].queryset = bouwsoort
    form.fields["Bouwsoort2"].queryset = bouwsoort
    form.fields["Bouwsoort3"].queryset = bouwsoort

    typeObject = versie.typeobject.all()
    form.fields["TypeObject1"].queryset = typeObject
    form.fields["TypeObject2"].queryset = typeObject
    form.fields["TypeObject3"].queryset = typeObject

    doelgroep = versie.doelgroep.all()
    form.fields["Doelgroep1"].queryset = doelgroep
    form.fields["Doelgroep2"].queryset = doelgroep
    form.fields["Doelgroep3"].queryset = doelgroep

    # if get method, just render the empty form
    context = {}
    context["form"] = form
    context["versie"] = versie
    context["versie_pk"] = versie_pk
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url    
    return render(request, "GeneratePVE_syn.html", context)

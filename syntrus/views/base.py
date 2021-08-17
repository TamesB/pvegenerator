import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from app import models
from project.models import Project, PVEItemAnnotation
from syntrus import forms
from syntrus.models import FAQ
from utils import createBijlageZip, writePdf, pve_csv_extract


def LoginView(request):
    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            return redirect("dashboard_syn")

    if request.method == "POST":
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            if "@" in form.cleaned_data["username"]:
                (email, password) = (
                    form.cleaned_data["username"],
                    form.cleaned_data["password"],
                )
                user = authenticate(request, email=email, password=password)
            else:
                (username, password) = (
                    form.cleaned_data["username"],
                    form.cleaned_data["password"],
                )
                user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("dashboard_syn")
            else:
                messages.warning(request, "Invalid login credentials")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # render the page
    context = {}
    context["form"] = forms.LoginForm()

    return render(request, "login_syn.html", context)


@login_required(login_url="login_syn")
def LogoutView(request):
    logout(request)
    return redirect("login_syn")


@login_required
def DashboardView(request):
    context = {}

    if Project.objects.filter(
        permitted__username__contains=request.user.username, belegger__naam="Syntrus"
    ).exists():
        projects = (
            Project.objects.filter(        
                Q(belegger__naam="Syntrus") &
                Q(permitted__username__contains=request.user.username))
            .distinct()
        )
        context["projects"] = projects

    if PVEItemAnnotation.objects.filter(gebruiker=request.user).exists():
        opmerkingen = PVEItemAnnotation.objects.filter(
            gebruiker=request.user, project__belegger__naam="Syntrus"
        )
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
    
    if request.user.type_user == "B":
        return render(request, "dashboardBeheerder_syn.html", context)
    if request.user.type_user == "SB":
        return render(request, "dashboardBeheerder_syn.html", context)
    if request.user.type_user == "SOG":
        return render(request, "dashboardOpdrachtgever_syn.html", context)
    if request.user.type_user == "SD":
        return render(request, "dashboardDerde_syn.html", context)


@login_required(login_url="login_syn")
def FAQView(request):
    faqquery = FAQ.objects.all()
    if request.user.type_user == "SB":
        faqquery = FAQ.objects.filter(gebruikersrang="SB")
    if request.user.type_user == "SOG":
        faqquery = FAQ.objects.filter(gebruikersrang="SOG")
    if request.user.type_user == "SD":
        faqquery = FAQ.objects.filter(gebruikersrang="SD")

    context = {}
    context["faqquery"] = faqquery
    return render(request, "FAQ_syn.html", context)


@login_required(login_url="login_syn")
def GeneratePVEView(request):
    allowed_users = ["B", "SB"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    versie = models.ActieveVersie.objects.get(belegger__naam="Syntrus").versie

    if request.method == "POST":
        # get user entered form
        form = forms.PVEParameterForm(request.POST)
        form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()
        form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
            versie=versie
        ).all()

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

            versie = models.ActieveVersie.objects.get(belegger__naam="Syntrus").versie
            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = (
                models.PVEItem.objects.select_related("hoofdstuk")
                .select_related("paragraaf")
                .filter(Q(versie=versie) & Q(basisregel=True))
            )
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.select_related("hoofdstuk")
                .select_related("paragraaf")
                .filter(versie=versie, Bouwsoort__parameter__contains=Bouwsoort1)
            )

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Bouwsoort__parameter__contains=Bouwsoort2)
                )
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Bouwsoort__parameter__contains=Bouwsoort3)
                )
            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, TypeObject__parameter__contains=TypeObject1)
                )
            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, TypeObject__parameter__contains=TypeObject2)
                )
            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, TypeObject__parameter__contains=TypeObject3)
                )
            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Doelgroep__parameter__contains=Doelgroep1)
                )
            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Doelgroep__parameter__contains=Doelgroep2)
                )
            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(versie=versie, Doelgroep__parameter__contains=Doelgroep3)
                )
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(AED=True))
                )
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(Smarthome=True))
                )
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(EntreeUpgrade=True))
                )
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(Pakketdient=True))
                )
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk")
                    .select_related("paragraaf")
                    .filter(Q(versie=versie) & Q(JamesConcept=True))
                )

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
            pdfmaker = writePdf.PDFMaker(versie.versie)
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
    form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()
    form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
        versie=versie
    ).all()

    # if get method, just render the empty form
    context = {}
    context["form"] = form
    context["versie"] = versie
    return render(request, "GeneratePVE_syn.html", context)

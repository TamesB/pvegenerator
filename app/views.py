# Author: Tames Boon

import datetime
import logging

import boto3
import botocore
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from pvetool.views.utils import GetAWSURL
from project.models import Beleggers, Project, BeheerdersUitnodiging
from utils import writeExcel
from users.models import CustomUser
from . import forms, models
import secrets
from django.utils import timezone

def LoginPageView(request):
    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            return redirect("dashboard")

    form = forms.LoginForm(request.POST or None)

    if request.method == "POST":
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
                login(request, user)
                return redirect("dashboard")
            else:
                messages.warning(request, "Invalid login credentials")
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # render the page
    context = {}
    context["form"] = forms.LoginForm()

    return render(request, "login.html", context)


def LogoutView(request):
    logout(request)
    return redirect("login")

@staff_member_required(login_url=reverse_lazy("logout"))
def DashboardView(request):
        
    hour = datetime.datetime.utcnow().hour + 2  # UTC + 2 = CEST

    greeting = ""
    if hour > 3 and hour < 12:
        greeting = "Goedemorgen"
    if hour >= 12 and hour < 18:
        greeting = "Goedemiddag"
    if hour >= 18 and hour <= 24:
        greeting = "Goedenavond"
    if hour <= 3 and hour >= 0:
        greeting = "Goedenacht"

    if greeting == "":
        greeting = "Goedendag"

    context = {}
    context["greeting"] = greeting

    pve_activiteiten = models.Activity.objects.filter(activity_type="PvE")[0:5]
    project_activiteiten = models.Activity.objects.filter(activity_type="P")[0:5]
    klant_activiteiten = models.Activity.objects.filter(activity_type="K")[0:5]

    context["project_activiteiten"] = project_activiteiten
    context["klant_activiteiten"] = klant_activiteiten
    context["pve_activiteiten"] = pve_activiteiten

    if pve_activiteiten.count() > 5:
        context["pve_activiteiten"] = pve_activiteiten[0:4]
    if klant_activiteiten.count() > 5:
        context["klant_activiteiten"] = klant_activiteiten[0:4]
    if project_activiteiten.count() > 5:
        context["project_activiteiten"] = project_activiteiten[0:4]

    if Project.objects.filter(permitted__username__contains=request.user.username):
        projects = Project.objects.filter(
            permitted__username__contains=request.user.username
        )
        context["projects"] = projects

    if request.user.type_user == "B":
        return render(request, "adminDashboard.html", context)


    return render(request, "dashboard.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def KlantOverzicht(request):
    klanten = Beleggers.objects.all()

    context = {}
    context["klanten"] = klanten
    return render(request, 'klantenOverzicht.html', context)

@staff_member_required(login_url=reverse_lazy("logout"))
def KlantVerwijderen(request, client_pk):
    klant = Beleggers.objects.get(id=client_pk)
    naam = klant.naam

    if request.headers["HX-Prompt"] == "VERWIJDEREN":
        klant.delete()
        messages.warning(request, f"Klant: {naam} succesvol verwijderd!")
        return HttpResponse("")
    else:
        messages.warning(request, f"Onjuiste invulling. Probeer het opnieuw.")
        return HttpResponse("")

@staff_member_required(login_url=reverse_lazy("logout"))
def GetLogo(request, client_pk):
    klant = Beleggers.objects.get(id=client_pk)
        
    logo_url = None
    
    if klant.logo:
        logo_url = GetAWSURL(klant)

    context = {}
    context["klant"] = klant
    context["client_pk"] = client_pk
    context["logo_url"] = logo_url
    return render(request, "partials/getlogoklant.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def LogoKlantForm(request, client_pk):
    klant = Beleggers.objects.get(id=client_pk)

    logo_url = None
    
    if klant.logo:
        logo_url = GetAWSURL(klant)

    form = forms.LogoKlantForm(request.POST or None, request.FILES or None, instance=klant)
    if klant.logo:
        form.fields["logo"].initial = klant.logo

    context = {}
    context["client_pk"] = client_pk
    context["form"] = form
    context["klant"] = klant
    context["logo_url"] = logo_url

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            form.save()
            messages.warning(request, "Klantlogo succesvol geupload!")
            return redirect("logoklantdetail", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    return render(request, "partials/logoklantform.html", context)
    
@staff_member_required(login_url=reverse_lazy("logout"))
def GetBeheerderKlant(request, client_pk):
    klant = Beleggers.objects.get(id=client_pk)

    invitation = None
    if BeheerdersUitnodiging.objects.filter(klantenorganisatie=klant):
        invitation = BeheerdersUitnodiging.objects.filter(klantenorganisatie=klant).first()

    context = {}
    context["klant"] = klant
    context["client_pk"] = client_pk
    context["invitation"] = invitation
    return render(request, "partials/getbeheerderklant.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def BeheerderKlantForm(request, client_pk):
    klant = Beleggers.objects.get(id=client_pk)

    form = forms.BeheerderKlantForm(request.POST or None)

    context = {}
    context["client_pk"] = client_pk
    context["form"] = form
    context["klant"] = klant

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if form.cleaned_data["email"]:
                expiry_length = 10
                expire_date = timezone.now() + timezone.timedelta(expiry_length)
                invitation = BeheerdersUitnodiging.objects.create(key=secrets.token_urlsafe(30), expires=expire_date)
                invitation.invitee = form.cleaned_data["email"]
                invitation.klantenorganisatie = klant
                invitation.save()

                send_mail(
                    f"Programma van Eisen Tool - Uitnodiging als beheerder voor uw website",
                    f"""Beste, 
                    
                    Uw subwebsite is gereed. Maak een wachtwoord aan via de uitnodigingslink 
                    
                    Uitnodigingslink: https://pvegenerator.net/pvetool/{klant.id}/accept/{invitation.key}
                    """,
                    "admin@pvegenerator.net",
                    [form.cleaned_data["email"]],
                    fail_silently=False,
                )
                messages.warning(request, "Uitnodigings Email verstuurd! De beheerder is aangewezen aan deze klant zodra de uitnodiging is geaccepteerd en het account is aangemaakt.")

            return render(request, "partials/getbeheerderklant.html", context)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    return render(request, "partials/beheerderklantform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def DeletePVEVersie(request, belegger_pk, versie_pk):
    versie = models.PVEVersie.objects.get(belegger__id=belegger_pk, id=versie_pk)
    naam = versie.versie
    context = {}
    context["versie"] = versie
    context["versie_pk"] = versie_pk

    if request.headers["HX-Prompt"] == "VERWIJDEREN":
        versie.delete()
        messages.warning(request, f"Versie: {naam} succesvol verwijderd.")
        return HttpResponse("")
    else:
        messages.warning(request, f"Onjuiste invulling. Ververs de pagina en probeer het opnieuw.")
        return HttpResponse("")

@staff_member_required(login_url=reverse_lazy("logout"))
def PVEVersieDetail(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    context = {}
    context["item"] = versie
    context["versie_pk"] = versie_pk
    return render(request, "partials/getpveversie.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def GetPveVersieDetail(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    context = {}
    context["versie"] = versie
    context["versie_pk"] = versie_pk
    return render(request, "partials/pveversiedetail.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def PveVersieEditName(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    form = forms.PVEVersieNameForm(request.POST or None, instance=versie)

    if request.method == "POST":
        if form.is_valid():
            form.save()

            messages.warning(request, "Naam veranderd.")
            return redirect("getpveversiedetail", versie_pk=versie_pk)

    context = {}
    context["versie"] = versie
    context["form"] = form
    context["versie_pk"] = versie_pk
    return render(request, "partials/pveversieeditname.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def KlantToevoegen(request):
    form = forms.BeleggerForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            new_klant = Beleggers()
            new_klant.naam = form.cleaned_data["naam"]
            new_klant.abbonement = form.cleaned_data["abbonement"]
            new_klant.logo = form.cleaned_data["logo"]
            new_klant.save()

            if form.cleaned_data["email"]:
                invitation = BeheerdersUitnodiging()
                expiry_length = 10
                expire_date = timezone.now() + timezone.timedelta(expiry_length)
                invitation.expires = expire_date
                invitation.key = secrets.token_urlsafe(30)
                invitation.invitee = form.cleaned_data["email"]
                invitation.klantenorganisatie = new_klant
                invitation.save()

                send_mail(
                    f"Programma van Eisen Tool - Uitnodiging als beheerder voor uw website",
                    f"""Beste, 
                    
                    Uw subwebsite is gereed. Maak een wachtwoord aan via de uitnodigingslink 
                    
                    Uitnodigingslink: https://pvegenerator.net/pvetool/{new_klant.id}/accept/{invitation.key}
                    """,
                    "admin@pvegenerator.net",
                    [form.cleaned_data["email"]],
                    fail_silently=False,
                )

            return redirect("klantoverzicht")
        
    context = {}
    context["form"] = form
    return render(request, 'klantToevoegen.html', context)
    
@staff_member_required(login_url=reverse_lazy("logout"))
def PVEBeleggerVersieOverview(request):
    beleggers = Beleggers.objects.all()

    BeleggerVersieQuerySet = {}

    for belegger in beleggers:
        BeleggerVersieQuerySet[belegger] = belegger.versie.all()

    context = {}
    context["BeleggerVersieQuerySet"] = BeleggerVersieQuerySet
    context["beleggers"] = beleggers
    return render(request, "PVEVersieOverview.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def AddBelegger(request):
    form = forms.BeleggerForm(request.POST or None)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            form.save()
            return redirect("beleggerversieoverview")

    # View below modal
    beleggers = Beleggers.objects.all()

    BeleggerVersieQuerySet = {}

    for belegger in beleggers:
        BeleggerVersieQuerySet[belegger] = belegger.versie.all()

    context = {}
    context["BeleggerVersieQuerySet"] = BeleggerVersieQuerySet
    context["beleggers"] = beleggers
    context["form"] = form
    return render(request, "addBelegger.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def AddPvEVersie(request, belegger_pk):
    belegger = Beleggers.objects.get(id=belegger_pk)
    # form
    form = forms.PVEVersieForm(request.POST or None, initial={"belegger": belegger})

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            kopie_versie = form.cleaned_data["kopie_versie"]
            new_versie = form.cleaned_data["versie"]
            form.save()            
            new_versie_obj = models.PVEVersie.objects.filter(versie=new_versie).first()
            # maak kopie van andere versie, voeg nieuw toe.
            if kopie_versie:
                # items
                items = [i for i in kopie_versie.item.all()]
                old_items = [i.id for i in items]

                # keuzematrix
                bwsrt = [i for i in kopie_versie.bouwsoort.all()]
                tpobj = [i for i in kopie_versie.typeobject.all()]
                dlgrp = [i for i in kopie_versie.doelgroep.all()]
                old_bwsrt = [i.id for i in bwsrt]
                old_tpobj = [i.id for i in tpobj]
                old_dlgrp = [i.id for i in dlgrp]

                # hoofdstukken en paragraven
                hfstukken = [i for i in kopie_versie.hoofdstuk.all()]
                prgrfs = [i for i in kopie_versie.paragraaf.all()]
                old_hfstukken = [i.id for i in hfstukken]
                old_prgrfs = [i.id for i in prgrfs]

                # bijlages
                bijlagen_models = kopie_versie.itembijlage.all()
                bijlagen = []

                for bijlage_model in bijlagen_models:
                    for item in bijlage_model.items.all():
                        if item in items:
                            bijlagen.append(bijlage_model)

                bijlagen = list(set(bijlagen))
                old_bijlagen = [i.id for i in bijlagen]

                # make copy of all
                new_versie_obj = models.PVEVersie.objects.filter(versie=new_versie).first()

                #keuzematrices#################
                new_bwsrt = []
                new_tpobj = []
                new_dlgrp = []

                for i in bwsrt:
                    i.pk = None
                    i.versie = new_versie_obj
                    new_bwsrt.append(i)

                for i in tpobj:
                    i.pk = None
                    i.versie = new_versie_obj
                    new_tpobj.append(i)

                for i in dlgrp:
                    i.pk = None
                    i.versie = new_versie_obj
                    new_dlgrp.append(i)

                # create the new models
                models.Bouwsoort.objects.bulk_create(new_bwsrt)
                models.TypeObject.objects.bulk_create(new_tpobj)
                models.Doelgroep.objects.bulk_create(new_dlgrp)

                # map the old to new model ids for new foreignkey references
                new_bwsrt = [i for i in new_versie_obj.bouwsoort.all()]
                new_tpobj = [i for i in new_versie_obj.typeobject.all()]
                new_dlgrp = [i for i in new_versie_obj.doelgroep.all()]

                bwsrt_map = {}
                for old, new in zip(old_bwsrt, new_bwsrt):
                    bwsrt_map[old] = new

                tpobj_map = {}
                for old, new in zip(old_tpobj, new_tpobj):
                    tpobj_map[old] = new

                dlgrp_map = {}
                for old, new in zip(old_dlgrp, new_dlgrp):
                    dlgrp_map[old] = new
          
                # hoofdstukken paragravem #################
                new_hfst = []

                for i in hfstukken:
                    i.pk = None
                    i.versie = new_versie_obj
                    new_hfst.append(i)

                models.PVEHoofdstuk.objects.bulk_create(new_hfst)

                new_hfst = [i for i in new_versie_obj.hoofdstuk.all()]

                hfst_map = {}
                for old, new in zip(old_hfstukken, new_hfst):
                    hfst_map[old] = new
                
                # paragraven
                new_prgrf = []

                for i in prgrfs:
                    i.pk = None
                    i.versie = new_versie_obj
                    i.hoofdstuk = hfst_map[i.hoofdstuk.id]
                    new_prgrf.append(i)

                models.PVEParagraaf.objects.bulk_create(new_prgrf)

                new_prgrf = [i for i in new_versie_obj.paragraaf.all()]

                prgrf_map = {}
                for old, new in zip(old_prgrfs, new_prgrf):
                    prgrf_map[old] = new

                # finally, make new items with the new reference keys
                new_items = []
                cur_Bouwsoort_obj = []
                cur_TypeObject_obj = []
                cur_Doelgroep_obj = []

                for i in items:
                    # save reference keys for later appending
                    cur_Bouwsoort_obj.append([bwsrt_map[j.id] for j in i.Bouwsoort.all()])
                    cur_TypeObject_obj.append([tpobj_map[j.id] for j in i.TypeObject.all()])
                    cur_Doelgroep_obj.append([dlgrp_map[j.id] for j in i.Doelgroep.all()])

                    i.pk = None
                    i.versie = new_versie_obj

                    i.hoofdstuk = hfst_map[i.hoofdstuk.id]

                    if i.paragraaf:
                        i.paragraaf = prgrf_map[i.paragraaf.id]

                    new_items.append(i)

                models.PVEItem.objects.bulk_create(new_items)
                new_items = [i for i in new_versie_obj.item.all()]

                # map foreignkeys to new objects
                for i in range(len(new_items)):
                    new_items[i].Bouwsoort.clear()
                    new_items[i].Bouwsoort.add(*cur_Bouwsoort_obj[i])

                    new_items[i].TypeObject.clear()
                    new_items[i].TypeObject.add(*cur_TypeObject_obj[i])

                    new_items[i].Doelgroep.clear()
                    new_items[i].Doelgroep.add(*cur_Doelgroep_obj[i])

                    new_items[i].projects.clear()

                items_map = {}
                for old, new in zip(old_items, new_items):
                    items_map[old] = new

                # connect the bijlagen to it
                new_bijlagen = []
                cur_items_obj = []

                for i in bijlagen:
                    cur_items_obj.append([items_map[j.id] for j in i.items.all()])

                    i.pk = None
                    i.versie = new_versie_obj
                    new_bijlagen.append(i)

                models.ItemBijlages.objects.bulk_create(new_bijlagen)
                new_bijlagen = [i for i in new_versie_obj.itembijlage.all()]

                # foreignkeys change after bulk_create
                for i, j in zip(new_bijlagen, cur_items_obj):
                    i.items.clear()
                    i.items.add(*j)

            return redirect("pveversietable", belegger_pk=belegger_pk)

    context = {}
    context["form"] = form
    context["key"] = belegger_pk
    context["belegger"] = belegger
    return render(request, "partials/addpveversieform.html", context)

@staff_member_required(login_url=reverse_lazy('logout'))
def BeleggerVersieTable(request, belegger_pk):
    key = Beleggers.objects.get(id=belegger_pk)
    queryset = models.PVEVersie.objects.filter(belegger__id=key.id)
    context = {}
    context["queryset"] = queryset
    context["key"] = key
    return render(request, "partials/pveversietable.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def VersieActiviteit(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)
    versie_pk = versie.id
    context = {}
    context["versie"] = versie
    context["versie_pk"] = versie_pk
    return render(request, "partials/getpveactiviteit.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def ActivateVersie(request, versie_pk):
    versie = models.PVEVersie.objects.filter(id=versie_pk).first()
    versie.public = True
    versie.save()
    messages.warning(request, f"Versie geactiveerd: {versie}")
    return redirect("getpveactiviteit", versie_pk=versie_pk)

@staff_member_required(login_url=reverse_lazy("logout"))
def DeactivateVersie(request, versie_pk):
    versie = models.PVEVersie.objects.filter(id=versie_pk).first()
    versie.public = False
    versie.save()
    messages.warning(request, f"Versie gedeactiveerd: {versie}")
    return redirect("getpveactiviteit", versie_pk=versie_pk)

@staff_member_required(login_url=reverse_lazy("logout"))
def PVEBewerkOverview(request, versie_pk):
    pve_versie = models.PVEVersie.objects.get(id=versie_pk)
    client = pve_versie.belegger
    context = {}
    context["pve_versie"] = pve_versie
    context["client_pk"] = client.id
    return render(request, "PVEBewerkOverview.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEHoofdstukListView(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)
    hoofdstukken = versie.hoofdstuk.all()
    context = {}
    context["hoofdstukken"] = hoofdstukken
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "PVEListHfst.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def DownloadWorksheet(request, versie_pk):
    fl_path = settings.EXPORTS_ROOT

    worksheet = writeExcel.ExcelMaker()
    filename = worksheet.linewriter(versie_pk)

    filename = f"/{filename}.xlsx"

    try:
        fl = open(fl_path + filename, "rb")
    except OSError:
        raise Http404("404")

    response = HttpResponse(
        fl,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "inline; filename=%s" % filename

    return response


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEaddhoofdstukView(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)
    form = forms.ChapterForm(request.POST or None)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEHoofdstuk = models.PVEHoofdstuk()
            PVEHoofdstuk.hoofdstuk = form.cleaned_data["hoofdstuk"]
            PVEHoofdstuk.versie = versie
            PVEHoofdstuk.save()
            return redirect("hoofdstukview", versie_pk=versie_pk)

    hoofdstukken = versie.hoofdstuk.all()

    context = {}
    context["hoofdstukken"] = hoofdstukken
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    context["form"] = form
    return render(request, "addchapterform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEedithoofdstukView(request, versie_pk, pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if not versie.hoofdstuk.filter(id=pk):
        return Http404("404")

    # form, initial chapter in specific onderdeel
    hoofdstuk = versie.hoofdstuk.get(id=pk)
    form = forms.ChapterForm(request.POST or None, instance=hoofdstuk)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEhoofdstuk = versie.hoofdstuk.get(id=pk)
            PVEhoofdstuk.hoofdstuk = form.cleaned_data["hoofdstuk"]
            PVEhoofdstuk.save()
            return redirect("hoofdstukview", versie_pk=versie_pk)


    hoofdstukken = versie.hoofdstuk.all()

    # form, initial chapter in specific onderdeel
    context = {}
    context["hoofdstukken"] = hoofdstukken
    context["hoofdstuk"] = hoofdstuk
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    context["pk"] = pk
    context["form"] = form
    return render(request, "changechapterform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def paragraaflistView(request, versie_pk, pk):
    pk = int(pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if versie.hoofdstuk.filter(id=pk).exists():
        hoofdstuk = versie.hoofdstuk.get(id=pk)
    else:
        raise Http404("404")

    items = hoofdstuk.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None and not hoofdstuk.paragraaf.all():
            return redirect(
                "itemlistview", versie_pk=versie_pk, chapter_id=pk, paragraph_id=0
            )

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = hoofdstuk.paragraaf.all()
    context["sectie"] = hoofdstuk
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "PVEParagraphList.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def paragraaflistViewEdit(request, versie_pk, pk):
    pk = int(pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if versie.hoofdstuk.filter(id=pk).exists():
        hoofdstuk = versie.hoofdstuk.get(id=pk)
    else:
        raise Http404("404")

    items = hoofdstuk.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect(
                "itemlistviewedit", versie_pk=versie_pk, chapter_id=pk, paragraph_id=0
            )

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = hoofdstuk.paragraaf.all()
    context["sectie"] = hoofdstuk
    context["id"] = pk
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "PVEParagraphListEdit.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def paragraaflistViewDelete(request, versie_pk, pk):
    pk = int(pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if versie.hoofdstuk.filter(id=pk).exists():
        hoofdstuk = versie.hoofdstuk.get(id=pk)
    else:
        raise Http404("404")

    items = hoofdstuk.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect(
                "itemlistviewdelete", versie_pk=versie_pk, chapter_id=pk, paragraph_id=0
            )

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = hoofdstuk.paragraaf.all()
    context["sectie"] = hoofdstuk
    context["id"] = pk
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "PVEParagraphListDelete.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEaddparagraafView(request, versie_pk, pk):
    pk = int(pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)
    
    if versie.hoofdstuk.filter(id=pk).exists():
        hoofdstuk = versie.hoofdstuk.filter(id=pk).first()
    else:
        raise Http404("404")

    form = forms.ParagraafForm(request.POST or None, initial={"hoofdstuk": hoofdstuk})

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEParagraaf = models.PVEParagraaf()
            PVEParagraaf.hoofdstuk = hoofdstuk
            PVEParagraaf.paragraaf = form.cleaned_data["paragraaf"]
            PVEParagraaf.versie = versie
            PVEParagraaf.save()
            return HttpResponseRedirect(reverse("viewParagraaf", args=(versie_pk, pk)))

    # View below modal
    items = models.PVEItem.objects.filter(hoofdstuk=hoofdstuk)

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect(
                "itemlistview", versie_pk=versie_pk, chapter_id=pk, paragraph_id=0
            )


    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = hoofdstuk.paragraaf.all()
    context["sectie"] = hoofdstuk
    context["form"] = form
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "addparagraphform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEeditparagraafView(request, versie_pk, pk):
    pk = int(pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if versie.paragraaf.filter(id=pk).exists():
        paragraaf = versie.paragraaf.filter(id=pk).first()
        hoofdstuk = paragraaf.hoofdstuk
    else:
        raise Http404("404")
    form = forms.ParagraafForm(request.POST or None, instance=paragraaf)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEparagraaf = versie.paragraaf.filter(id=pk).first()
            PVEparagraaf.paragraaf = form.cleaned_data["paragraaf"]
            PVEparagraaf.versie = versie
            PVEparagraaf.save()
            return HttpResponseRedirect(
                reverse(
                    "viewParagraaf",
                    args=(
                        versie_pk,
                        hoofdstuk.id,
                    ),
                )
            )

    # View below modal
    items = hoofdstuk.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect(
                "itemlistview",
                versie_pk=versie_pk,
                chapter_id=hoofdstuk.id,
                paragraph_id=0,
            )


    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = hoofdstuk.paragraaf.all()
    context["sectie"] = hoofdstuk
    context["paragraph_id"] = pk
    context["id"] = hoofdstuk.id
    context["form"] = form
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "changeparagraphform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def itemListView(request, versie_pk, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)
    chapter_id = int(chapter_id)

    versie = models.PVEVersie.objects.get(id=versie_pk)
    
    # Chapter_id doesnt exist
    if not versie.hoofdstuk.filter(id=chapter_id).exists():
        raise Http404("404")

    hoofdstuk = versie.hoofdstuk.get(id=chapter_id)

    paragraven_exist = hoofdstuk.paragraaf.exists()

    # if no paragraph given but there are paragraphs in this chapter
    if paragraph_id == 0:
        if paragraven_exist:
            raise Http404("404")

    # if paragraphs arent connected to this chapter
    if paragraph_id != 0:
        if not paragraven_exist:
            raise Http404("404")

        paragraaf = versie.paragraaf.get(id=paragraph_id)

    context = {}

    # item niet in een paragraaf: haal ze van een hoofdstuk
    if paragraph_id == 0:
        context["queryset"] = hoofdstuk.item.all()
        context["hoofdstuk"] = hoofdstuk
    else:
        context["queryset"] = paragraaf.item.all()
        context["paragraaf"] = paragraaf
        context["hoofdstuk"] = hoofdstuk

    context["paragraaf_id"] = paragraph_id
    context["hoofdstuk_id"] = chapter_id
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "PVEItemList.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def viewItemView(request, versie_pk, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(versie__id=versie_pk, id=pk).exists():
        PVEItem = models.PVEItem.objects.filter(versie__id=versie_pk, id=pk).first()
    else:
        raise Http404("Item does not exist.")

    context = {}

    if models.ItemBijlages.objects.filter(versie__id=versie_pk, items__id__contains=PVEItem.id).exists():
        bijlage = models.ItemBijlages.objects.filter(versie__id=versie_pk, items__id__contains=PVEItem.id).first()
        context["bijlage"] = bijlage
        context["bijlagenaam"] = bijlage.naam

    context["PVEItem"] = PVEItem
    context["Bouwsoort"] = PVEItem.Bouwsoort.all()
    context["TypeObject"] = PVEItem.TypeObject.all()
    context["Doelgroep"] = PVEItem.Doelgroep.all()

    if not PVEItem.paragraaf:
        context["queryset"] = models.PVEItem.objects.filter(
            versie__id=versie_pk, hoofdstuk=PVEItem.hoofdstuk
        )
        context["hoofdstuk"] = PVEItem.hoofdstuk
        context["paragraaf_id"] = 0
    else:
        context["queryset"] = models.PVEItem.objects.filter(
            versie__id=versie_pk, hoofdstuk=PVEItem.hoofdstuk
        ).filter(versie__id=versie_pk, paragraaf=PVEItem.paragraaf)
        context["paragraaf"] = PVEItem.paragraaf
        context["hoofdstuk"] = PVEItem.hoofdstuk
        context["paragraaf_id"] = PVEItem.paragraaf.id

    context["hoofdstuk_id"] = PVEItem.hoofdstuk.id
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(id=versie_pk)
    return render(request, "PVEItemView.html", context)


@login_required(login_url="/404")
def downloadBijlageView(request, pk):
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    if models.PVEItem.objects.filter(id=pk).exists():
        item = models.PVEItem.objects.filter(id=pk).first()        
        if models.ItemBijlages.objects.filter(items__id__contains=item.id).exists():
            bijlage = models.ItemBijlages.objects.filter(items__id__contains=item.id).first().bijlage
    else:           
        bijlage = models.ItemBijlages.objects.filter(id=pk).first().bijlage


    expiration = 10000
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=settings.AWS_S3_REGION_NAME,
        config=botocore.client.Config(
            signature_version=settings.AWS_S3_SIGNATURE_VERSION
        ),
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": str(bijlage)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)


@staff_member_required(login_url=reverse_lazy("logout"))
def editItemView(request, versie_pk, pk):
    pk = int(pk)
    if models.PVEItem.objects.filter(versie__id=versie_pk, id=pk).exists():
        PVEItem = models.PVEItem.objects.filter(versie__id=versie_pk, id=pk).first()
    else:
        raise Http404("Item does not exist.")
    
    form = forms.PVEItemEditForm(request.POST or None, request.FILES or None, instance=PVEItem)
    form.fields["BestaandeBijlage"].queryset = models.ItemBijlages.objects.filter(
        versie__id=versie_pk
    ).all()
    form.fields["Bouwsoort"].queryset = models.Bouwsoort.objects.filter(
        versie__id=versie_pk
    ).all()    
    form.fields["TypeObject"].queryset = models.TypeObject.objects.filter(
        versie__id=versie_pk
    ).all()    
    form.fields["Doelgroep"].queryset = models.Doelgroep.objects.filter(
        versie__id=versie_pk
    ).all()

    if request.method == "POST":
        # get user entered form

        # check validity
        if form.is_valid():
            # get parameters and save new item
            PVEItem.inhoud = form.cleaned_data["inhoud"]
            PVEItem.save()

            PVEItem.Bouwsoort.set(form.cleaned_data["Bouwsoort"])
            PVEItem.TypeObject.set(form.cleaned_data["TypeObject"])
            PVEItem.Doelgroep.set(form.cleaned_data["Doelgroep"])
            PVEItem.Smarthome = form.cleaned_data["Smarthome"]
            PVEItem.AED = form.cleaned_data["AED"]
            PVEItem.EntreeUpgrade = form.cleaned_data["EntreeUpgrade"]
            PVEItem.Pakketdient = form.cleaned_data["Pakketdient"]
            PVEItem.JamesConcept = form.cleaned_data["JamesConcept"]
            PVEItem.basisregel = form.cleaned_data["basisregel"]

            PVEItem.save()

            if form.cleaned_data["bijlage"]:
                bijlage_item = models.ItemBijlages()
                bijlage_item.bijlage = form.cleaned_data["bijlage"]
                bijlage_item.versie = models.PVEVersie.objects.filter(id=versie_pk).first()
                bijlage_item.save()
                bijlage_item.items.add(PVEItem)
                bijlage_item.naam = f"Bijlage {bijlage_item.pk}"
                bijlage_item.save()

            if form.cleaned_data["BestaandeBijlage"]:
                bestaande_bijlage = form.cleaned_data["BestaandeBijlage"]
                bestaande_bijlage.items.add(PVEItem)

            # and reverse
            return HttpResponseRedirect(reverse("viewitem", args=(versie_pk, pk)))

    # if get method, just render the empty form
    context = {}
    context["form"] = form
    context["id"] = pk
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(id=versie_pk)
    return render(request, "PVEItemEdit.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def addItemView(request, versie_pk, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)

    form = forms.PVEItemEditForm(request.POST or None, request.FILES or None)
    form.fields["BestaandeBijlage"].queryset = models.ItemBijlages.objects.filter(
        versie__id=versie_pk
    ).all()
    form.fields["Bouwsoort"].queryset = models.Bouwsoort.objects.filter(
        versie__id=versie_pk
    ).all()    
    form.fields["TypeObject"].queryset = models.TypeObject.objects.filter(
        versie__id=versie_pk
    ).all()    
    form.fields["Doelgroep"].queryset = models.Doelgroep.objects.filter(
        versie__id=versie_pk
    ).all()

    if request.method == "POST":

        # check validity
        if form.is_valid():
            PVEItem = models.PVEItem()
            PVEItem.versie = models.PVEVersie.objects.get(id=versie_pk)
            # get parameters and save new item
            if int(paragraph_id) != 0:
                PVEItem.paragraaf = models.PVEParagraaf.objects.filter(
                    versie__id=versie_pk, id=paragraph_id
                ).first()

            PVEItem.hoofdstuk = models.PVEHoofdstuk.objects.filter(
                versie__id=versie_pk, id=chapter_id
            ).first()
            PVEItem.inhoud = form.cleaned_data["inhoud"]
            PVEItem.save()

            PVEItem.Bouwsoort.set(form.cleaned_data["Bouwsoort"])
            PVEItem.TypeObject.set(form.cleaned_data["TypeObject"])
            PVEItem.Doelgroep.set(form.cleaned_data["Doelgroep"])
            PVEItem.Smarthome = form.cleaned_data["Smarthome"]
            PVEItem.AED = form.cleaned_data["AED"]
            PVEItem.EntreeUpgrade = form.cleaned_data["EntreeUpgrade"]
            PVEItem.Pakketdient = form.cleaned_data["Pakketdient"]
            PVEItem.JamesConcept = form.cleaned_data["JamesConcept"]
            PVEItem.basisregel = form.cleaned_data["basisregel"]

            PVEItem.save()

            if form.cleaned_data["bijlage"]:
                bijlage_item = models.ItemBijlages()
                bijlage_item.bijlage = form.cleaned_data["bijlage"]
                bijlage_item.versie = models.PVEVersie.objects.filter(id=versie_pk).first()
                bijlage_item.save()
                bijlage_item.items.add(PVEItem)
                bijlage_item.naam = f"Bijlage {bijlage_item.pk}"
                bijlage_item.save()
                
            if form.cleaned_data["BestaandeBijlage"]:
                bestaande_bijlage = form.cleaned_data["BestaandeBijlage"]
                bestaande_bijlage.items.add(PVEItem)

            pk = PVEItem.id

            # and reverse
            return HttpResponseRedirect(reverse("viewitem", args=(versie_pk, pk)))

    context = {}
    context["form"] = form
    context["chapter_id"] = chapter_id
    context["paragraph_id"] = int(paragraph_id)
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(id=versie_pk)
    return render(request, "PVEAddItem.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def deleteItemView(request, versie_pk, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(versie__id=versie_pk, id=pk).exists():
        PVEItem = models.PVEItem.objects.filter(versie__id=versie_pk, id=pk).first()
        hoofdstuk = PVEItem.hoofdstuk
        paragraaf = PVEItem.paragraaf
    else:
        raise Http404("404.")

    PVEItem.delete()

    messages.success(request, f"Regel {pk} verwijderd.")

    if not paragraaf:
        return HttpResponseRedirect(
            reverse(
                "viewParagraaf",
                args=(
                    versie_pk,
                    hoofdstuk.id,
                ),
            )
        )

    return HttpResponseRedirect(
        reverse("itemlistview", args=(versie_pk, hoofdstuk.id, paragraaf.id))
    )


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEdeletehoofdstukView(request, versie_pk, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(versie__id=versie_pk, id=pk).exists():
        PVEHoofdstuk = models.PVEHoofdstuk.objects.filter(
            versie__id=versie_pk, id=pk
        ).first()
        hoofdstuk = PVEHoofdstuk.hoofdstuk
    else:
        raise Http404("404.")

    PVEHoofdstuk.delete()

    messages.success(request, f"Hoofdstuk {hoofdstuk} verwijderd.")

    return redirect("hoofdstukview", versie_pk=versie_pk)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEdeleteparagraafView(request, versie_pk, pk):
    pk = int(pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if versie.paragraaf.filter(id=pk).exists():
        PVEParagraaf = versie.paragraaf.get(id=pk)
        hoofdstuk = PVEParagraaf.hoofdstuk
        paragraaf = PVEParagraaf.paragraaf
    else:
        raise Http404("404.")

    PVEParagraaf.delete()

    messages.success(request, f"Paragraaf {paragraaf} verwijderd.")

    return HttpResponseRedirect(
        reverse("viewParagraaf", args=(versie_pk, hoofdstuk.id))
    )


@staff_member_required(login_url=reverse_lazy("logout"))
def kiesparametersView(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    context = {}
    context["bouwsoorten"] = versie.bouwsoort.all()
    context["typeObjecten"] = versie.typeobject.all()
    context["doelgroepen"] = versie.doelgroep.all()
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "kiesparameters.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def addkiesparameterView(request, versie_pk, type_id):
    type_id = int(type_id)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if request.method == "POST":
        # get user entered form
        form = forms.KiesParameterForm(request.POST)

        # check validity
        if form.is_valid():

            # If type_id not in available ones
            if type_id != 1 and type_id != 2 and type_id != 3:
                raise Http404("404")

            if type_id == 1:  # Bouwsoort
                item = models.Bouwsoort()

            if type_id == 2:  # Type Object
                item = models.TypeObject()

            if type_id == 3:  # Doelgroep
                item = models.Doelgroep()

            item.parameter = form.cleaned_data["parameter"]
            item.versie = versie
            item.save()

            return HttpResponseRedirect(
                reverse("kiesparametersview", args=(versie_pk,))
            )

    form = forms.KiesParameterForm()

    context = {}
    context["form"] = form
    context["type_id"] = type_id
    context["bouwsoorten"] = versie.bouwsoort.all()
    context["typeObjecten"] = versie.typeobject.all()
    context["doelgroepen"] = versie.doelgroep.all()
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "addkiesparameter.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def addkiesparameterform(request, versie_pk, type):
    type = int(type)
    versie = models.PVEVersie.objects.get(id=versie_pk)
    form = forms.KiesParameterForm(request.POST or None)

    if request.method == "POST":
        # check validity
        if form.is_valid():

            # If type_id not in available ones
            if type != 1 and type != 2 and type != 3:
                raise Http404("404")

            if type == 1:  # Bouwsoort
                item = models.Bouwsoort()

            if type == 2:  # Type Object
                item = models.TypeObject()

            if type == 3:  # Doelgroep
                item = models.Doelgroep()

            item.parameter = form.cleaned_data["parameter"]
            item.versie = versie
            item.save()

            return redirect("kiesparameterdetail", versie_pk=versie_pk, type=type, parameter_id=item.pk)


    context = {}
    context["form"] = form
    context["type"] = type
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    return render(request, "partials/addkiesparameterform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def kiesparameterform(request, versie_pk, type, parameter_id):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:  # Bouwsoort
        if not versie.bouwsoort.filter(id=parameter_id):
            raise Http404("404")

        parameter = versie.bouwsoort.filter(id=parameter_id).first()

    if type == 2:  # Type Object
        if not versie.typeobject.filter(id=parameter_id):
            raise Http404("404")

        parameter = versie.typeobject.filter(
            id=parameter_id
        ).first()

    if type == 3:  # Doelgroep
        if not versie.doelgroep.filter(id=parameter_id):
            raise Http404("404")

        parameter = versie.doelgroep.filter(id=parameter_id).first()

    form = forms.KiesParameterForm(request.POST or None, initial={"parameter": parameter.parameter})

    context = {}
    context["form"] = form
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    context["type"] = type
    context["parameter_id"] = parameter_id
    context["parameter"] = parameter

    if request.method == "POST":
        if form.is_valid():
            parameter.parameter = form.cleaned_data["parameter"]
            parameter.save()

            return redirect("kiesparameterdetail", versie_pk=versie_pk, type=type, parameter_id=parameter_id)
    

    return render(request, "partials/kiesparameterform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def kiesparameterdetail(request, versie_pk, type, parameter_id):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:  # Bouwsoort
        if not versie.bouwsoort.filter(id=parameter_id):
            raise Http404("404")

        parameter = versie.bouwsoort.filter(id=parameter_id).first()

    if type == 2:  # Type Object
        if not versie.typeobject.filter(id=parameter_id):
            raise Http404("404")

        parameter = versie.typeobject.filter(
            id=parameter_id
        ).first()

    if type == 3:  # Doelgroep
        if not versie.doelgroep.filter(id=parameter_id):
            raise Http404("404")

        parameter = versie.doelgroep.filter(id=parameter_id).first()

    context = {}
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    context["type"] = type
    context["parameter_id"] = parameter_id
    context["parameter"] = parameter
    context["type_id"] = type
    return render(request, "partials/kiesparameterdetail.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def kiesparametertable(request, versie_pk, type):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:  # Bouwsoort
        if not versie.bouwsoort.all():
            raise Http404("404")

        parameters = versie.bouwsoort.all()
        parameter_naam = "Bouwsoorten"

    if type == 2:  # Type Object
        if not versie.typeobject.all():
            raise Http404("404")

        parameters = versie.typeobject.all()
        parameter_naam = "Type Objecten"

    if type == 3:  # Doelgroep
        if not versie.doelgroep.all():
            raise Http404("404")

        parameters = versie.doelgroep.all()

        parameter_naam = "Doelgroepen"

    context = {}
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    context["parameters"] = parameters
    context["type_id"] = type
    context["parameter_naam"] = parameter_naam
    return render(request, "partials/kiesparametertable.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def kiesparametermodaladd(request, versie_pk, type):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:
        naam = "Bouwsoort"
    if type == 2:
        naam = "Type Object"
    if type == 3:
        naam = "Doelgroep"
    form = forms.KiesParameterForm(request.POST or None)

    context = {}
    context["form"] = form
    context["versie_pk"] = versie_pk
    context["versie"] = versie
    context["type"] = type
    context["type_id"] = type
    context["naam"] = naam

    if request.method == "POST":
        if form.is_valid():
            # If type_id not in available ones
            if type != 1 and type != 2 and type != 3:
                raise Http404("404")

            if type == 1:  # Bouwsoort
                item = models.Bouwsoort()

            if type == 2:  # Type Object
                item = models.TypeObject()

            if type == 3:  # Doelgroep
                item = models.Doelgroep()

            item.parameter = form.cleaned_data["parameter"]
            item.versie = versie
            item.save()

            return redirect("kiesparametertable", versie_pk=versie_pk, type=type)

    return render(request, "partials/addkiesparameterform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def deletekiesparameterView(request, versie_pk, type_id, item_id):

    type_id = int(type_id)
    item_id = int(item_id)
    versie_pk = int(versie_pk)
    versie = models.PVEVersie.objects.get(id=versie_pk)

    if type_id != 1 and type_id != 2 and type_id != 3:
        raise Http404("404")

    if type_id == 1:  # Bouwsoort
        if not versie.bouwsoort.filter(id=item_id):
            raise Http404("404")

        item = versie.bouwsoort.filter(id=item_id).first()

    if type_id == 2:  # Type Object
        if not versie.typeobject.filter(id=item_id):
            raise Http404("404")

        item = versie.typeobject.filter(
            id=item_id
        ).first()

    if type_id == 3:  # Doelgroep
        if not versie.doelgroep.filter(id=item_id):
            raise Http404("404")

        item = versie.doelgroep.filter(id=item_id).first()

    parameter = item.parameter

    if request.headers["HX-Prompt"] == "VERWIJDEREN":
        item.delete()
        messages.warning(request, f"Parameter: {parameter} verwijderd.")
        return HttpResponse("")
    else:
        messages.warning(request, f"Onjuiste invulling. Probeer het opnieuw.")
        return redirect("kiesparametersview", versie_pk=versie_pk)

#bijlagesView
#bijlageDetail
#bijlageEdit
#bijlageAdd
#bijlageDelete
#ItemBijlage: versie items bijlage naam
@staff_member_required(login_url=reverse_lazy("logout"))
def bijlagenView(request, versie_pk):
    context = {}
    context["bijlagen"] = models.ItemBijlages.objects.filter(versie__id=versie_pk)
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(pk=versie_pk)
    return render(request, "bijlagenView.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def bijlageDetail(request, versie_pk, pk):
    bijlagen = models.ItemBijlages.objects.filter(versie__id=versie_pk)
    bijlage = bijlagen.get(id=pk)

    items = bijlage.items.all()

    context = {}
    context["bijlage"] = bijlage
    context["bijlagen"] = bijlagen
    context["items"] = items
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(pk=versie_pk)
    return render(request, "bijlageDetail.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def bijlageAdd(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)
    form = forms.bijlageEditForm(request.POST or None, request.FILES or None)
    form.fields["items"].queryset = versie.item.all()

    if request.method == "POST":

        # check validity
        if form.is_valid():
            nieuw_bijlage = models.ItemBijlages()
            nieuw_bijlage.bijlage = form.cleaned_data["bijlage"]
            nieuw_bijlage.versie = versie
            if form.cleaned_data["naam"]:
                nieuw_bijlage.naam = form.cleaned_data["naam"]
            nieuw_bijlage.save()
            nieuw_bijlage.items.set(form.cleaned_data["items"])
            nieuw_bijlage.save()

            return HttpResponseRedirect(
                reverse("bijlageview", args=(versie_pk,))
            )
        else:
            print(form.errors())

    context = {}
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(pk=versie_pk)
    context["form"] = form
    return render(request, "bijlageAdd.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def bijlageEdit(request, versie_pk, pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)

    bijlage = versie.itembijlage.get(id=pk)
    form = forms.bijlageEditForm(request.POST or None, request.FILES or None, initial={'naam':bijlage.naam, 'bijlage':bijlage.bijlage, 'items':bijlage.items.all()})
    form.fields["items"].queryset = versie.item.all()

    if request.method == "POST":
        # get user entered form

        # check validity
        if form.is_valid():
            nieuw_bijlage = bijlage
            if form.cleaned_data["bijlage"]:
                nieuw_bijlage.bijlage = form.cleaned_data["bijlage"]
            nieuw_bijlage.versie = versie
            if form.cleaned_data["naam"]:
                nieuw_bijlage.naam = form.cleaned_data["naam"]
            nieuw_bijlage.save()
            nieuw_bijlage.items.set(form.cleaned_data["items"])
            nieuw_bijlage.save()

            return HttpResponseRedirect(
                reverse("bijlageview", args=(versie_pk,))
            )
        else:
            print(form.errors)

    context = {}
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(pk=versie_pk)
    context["form"] = form
    context["bijlage"] = bijlage
    return render(request, "bijlageEdit.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def bijlageDelete(request, versie_pk, pk):
    bijlage = models.ItemBijlages.objects.filter(versie__id=versie_pk, id=pk)
    bijlage.delete()
    return HttpResponseRedirect(
        reverse("bijlageview", args=(versie_pk,))
    )

@staff_member_required(login_url=reverse_lazy("logout"))
def projectHeatmap(request):
    context = {}

    projects = Project.objects.all()

    data = [[project.plaats.y, project.plaats.x, 1000] for project in projects]
    context["data"] = data
    return render(request, "heatmapProjects.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def AccountOverview(request):
    klanten = Beleggers.objects.all()
    context = {}
    context["klanten"] = klanten
    return render(request, "accountOverview.html", context)
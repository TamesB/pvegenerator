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
from django.views import View
from django.views.generic import FormView, TemplateView
from pvetool.views.utils import GetAWSURL
from pvetool.models import CommentRequirement, CommentStatus
from project.models import Beleggers, Project, BeheerdersUitnodiging
from utils import writeExcel
from users.models import CustomUser
from . import forms, models, mixins
import secrets
from django.utils import timezone
import time
class LoginPageView(View):
    form_class = forms.LoginForm
    template_name = "login.html"
        
    def get(self, request, *args, **kwargs):
        if not request.user.is_anonymous:
            if request.user.is_authenticated:
                return redirect("dashboard")
        
        return render(request, self.template_name, context={"form": self.form_class})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST or None)
        if form.is_valid():
            if "@" in form.cleaned_data["username"]:
                email = form.cleaned_data["username"].split("@")[0]
                user_check = CustomUser.objects.filter(username__iexact=email)
                
                if user_check.exists():
                    user_check = user_check.first()
                    
                    user = authenticate(request, username=email, password=form.cleaned_data["password"])
                else:
                    messages.warning(request, "Foute login credentials.")
            else:
                user = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            
            if user:
                login(request, user)
                return redirect("dashboard")
            else:
                messages.warning(request, "Foute login credentials.")
        else:
            messages.warning(request, "Vul de verplichte velden in.")
            
        return render(request, self.template_name, context={"form": self.form_class})
    
    
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")
    
class DashboardView(mixins.LogoutIfNotStaffMixin, TemplateView):
    template_name = "adminDashboard.html"
    
    def get(self, request, *args, **kwargs):        
        return render(request, self.template_name, context=self.get_context_data(request))
    
    def get_context_data(self, request, **kwargs):
        context = super().get_context_data(**kwargs)
        context["greeting"] = self.get_greeting()
        context["pve_activities"], context["client_activities"], context["project_activities"] = self.get_activities()
        return context    
    
    def get_greeting(self):
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
            
        return greeting

    def get_activities(self):
        pve_activities = models.Activity.objects.filter(activity_type="PvE")[0:5]
        project_activities = models.Activity.objects.filter(activity_type="P")[0:5]
        client_activities = models.Activity.objects.filter(activity_type="K")[0:5]     
        
        if pve_activities.count() > 5:
            pve_activities = pve_activities[0:4]
        if client_activities.count() > 5:
            client_activities = client_activities[0:4]
        if project_activities.count() > 5:
            project_activities = project_activities[0:4]
            
        return pve_activities, client_activities, project_activities
    
class KlantOverzicht(mixins.LogoutIfNotStaffMixin, TemplateView):
    template_name = "clientsOverzicht.html"
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context=self.get_context_data())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients"] = self.clients()
        return context
    
    def clients(self):
        return Beleggers.objects.all()
        
class KlantVerwijderen(mixins.LogoutIfNotStaffMixin, TemplateView):    
    def post(self, request, *args, **kwargs):
        if request.headers["HX-Prompt"] == "VERWIJDEREN":
            client = self.client()
            
            try:
                client.delete()
                messages.warning(request, f"Klant: {client.name} succesvol verwijderd!")
            except Exception:
                messages.warning(request, f"Klant: {client.name} fout met verwijderen. Probeer het opnieuw.")
                
            return HttpResponse("")
        else:
            messages.warning(request, f"Onjuiste invulling. Probeer het opnieuw.")
            return HttpResponse("")
    
    def client(self, **kwargs):
        return Beleggers.objects.get(pk=self.kwargs['client_pk'])

class GetLogo(mixins.LogoutIfNotStaffMixin, TemplateView):
    template_name = 'partials/getlogoclient.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context=self.get_context_data())
    
    def get_context_data(self, **kwargs):
        context = super(GetLogo, self).get_context_data(**kwargs)
        context['client'], context['logo_url'] = self.get_logo()
        context["client_pk"] = self.kwargs['client_pk']
        return context
        
    def get_logo(self, **kwargs):
        client = Beleggers.objects.get(id=self.kwargs['client_pk'])

        logo_url = None
        
        if client.logo:
            logo_url = GetAWSURL(client)
            
        return client, logo_url

def LogoKlantForm(request, client_pk):
    client = Beleggers.objects.get(id=client_pk)

    logo_url = None
    
    if client.logo:
        logo_url = GetAWSURL(client)

    form = forms.LogoKlantForm(request.POST or None, request.FILES or None, instance=client)
    if client.logo:
        form.fields["logo"].initial = client.logo

    context = {}
    context["client_pk"] = client_pk
    context["form"] = form
    context["client"] = client
    context["logo_url"] = logo_url

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            form.save()
            messages.warning(request, "Klantlogo succesvol geupload!")
            return redirect("logoclientdetail", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    return render(request, "partials/logoclientform.html", context)
    
@staff_member_required(login_url=reverse_lazy("logout"))
def GetBeheerderKlant(request, client_pk):
    client = Beleggers.objects.get(id=client_pk)

    invitation = None
    if BeheerdersUitnodiging.objects.filter(client=client):
        invitation = BeheerdersUitnodiging.objects.filter(client=client).first()

    context = {}
    context["client"] = client
    context["client_pk"] = client_pk
    context["invitation"] = invitation
    return render(request, "partials/getbeheerderclient.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def BeheerderKlantForm(request, client_pk):
    client = Beleggers.objects.get(id=client_pk)

    form = forms.BeheerderKlantForm(request.POST or None)

    context = {}
    context["client_pk"] = client_pk
    context["form"] = form
    context["client"] = client

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if form.cleaned_data["email"]:
                expiry_length = 10
                expire_date = timezone.now() + timezone.timedelta(expiry_length)
                invitation = BeheerdersUitnodiging.objects.create(key=secrets.token_urlsafe(30), expires=expire_date)
                invitation.invitee = form.cleaned_data["email"]
                invitation.client = client
                invitation.save()

                send_mail(
                    f"Programma van Eisen Tool - Uitnodiging als beheerder voor uw website",
                    f"""Beste, 
                    
                    Uw subwebsite is gereed. Maak een wachtwoord aan via de uitnodigingslink 
                    
                    Uitnodigingslink: https://pvegenerator.net/pvetool/{client.id}/accept/{invitation.key}
                    """,
                    "admin@pvegenerator.net",
                    [form.cleaned_data["email"]],
                    fail_silently=False,
                )
                messages.warning(request, "Uitnodigings Email verstuurd! De beheerder is aangewezen aan deze client zodra de uitnodiging is geaccepteerd en het account is aangemaakt.")

            return render(request, "partials/getbeheerderclient.html", context)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    return render(request, "partials/beheerderclientform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def DeletePVEVersie(request, client_pk, version_pk):
    version = models.PVEVersie.objects.get(client__id=client_pk, id=version_pk)
    name = version.version
    context = {}
    context["version"] = version
    context["version_pk"] = version_pk

    if request.headers["HX-Prompt"] == "VERWIJDEREN":
        version.delete()
        messages.warning(request, f"Versie: {name} succesvol verwijderd.")
        return HttpResponse("")
    else:
        messages.warning(request, f"Onjuiste invulling. Ververs de pagina en probeer het opnieuw.")
        return HttpResponse("")

@staff_member_required(login_url=reverse_lazy("logout"))
def PVEVersieDetail(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)
    
    downloadable = False
    if version.chapter.exists():
        downloadable = True
        
    context = {}
    context["item"] = version
    context["version_pk"] = version_pk
    context["downloadable"] = downloadable
    return render(request, "partials/getpveversion.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def GetPveVersieDetail(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)

    context = {}
    context["version"] = version
    context["version_pk"] = version_pk
    return render(request, "partials/pveversiondetail.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def PveVersieEditName(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)

    form = forms.PVEVersieNameForm(request.POST or None, instance=version)

    if request.method == "POST":
        if form.is_valid():
            form.save()

            messages.warning(request, "Naam veranderd.")
            return redirect("getpveversiedetail", version_pk=version_pk)

    context = {}
    context["version"] = version
    context["form"] = form
    context["version_pk"] = version_pk
    return render(request, "partials/pveversioneditname.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def KlantToevoegen(request):
    form = forms.BeleggerForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            new_client = Beleggers()
            new_client.name = form.cleaned_data["name"]
            new_client.subscription = form.cleaned_data["subscription"]
            new_client.logo = form.cleaned_data["logo"]
            new_client.save()

            if form.cleaned_data["email"]:
                invitation = BeheerdersUitnodiging()
                expiry_length = 10
                expire_date = timezone.now() + timezone.timedelta(expiry_length)
                invitation.expires = expire_date
                invitation.key = secrets.token_urlsafe(30)
                invitation.invitee = form.cleaned_data["email"]
                invitation.client = new_client
                invitation.save()

                send_mail(
                    f"Programma van Eisen Tool - Uitnodiging als beheerder voor uw website",
                    f"""Beste, 
                    
                    Uw subwebsite is gereed. Maak een wachtwoord aan via de uitnodigingslink 
                    
                    Uitnodigingslink: https://pvegenerator.net/pvetool/{new_client.id}/accept/{invitation.key}
                    """,
                    "admin@pvegenerator.net",
                    [form.cleaned_data["email"]],
                    fail_silently=False,
                )

            return redirect("clientoverzicht")
        
    context = {}
    context["form"] = form
    return render(request, 'clientToevoegen.html', context)
    
@staff_member_required(login_url=reverse_lazy("logout"))
def PVEBeleggerVersieOverview(request):
    clients = Beleggers.objects.all()

    BeleggerVersieQuerySet = {}

    for client in clients:
        BeleggerVersieQuerySet[client] = client.version.all()

    context = {}
    context["BeleggerVersieQuerySet"] = BeleggerVersieQuerySet
    context["clients"] = clients
    return render(request, "PVEVersieOverview.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def AddBelegger(request):
    form = forms.BeleggerForm(request.POST or None)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            form.save()
            return redirect("clientversieoverview")

    # View below modal
    clients = Beleggers.objects.all()

    BeleggerVersieQuerySet = {}

    for client in clients:
        BeleggerVersieQuerySet[client] = client.version.all()

    context = {}
    context["BeleggerVersieQuerySet"] = BeleggerVersieQuerySet
    context["clients"] = clients
    context["form"] = form
    return render(request, "addBelegger.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def AddPvEVersie(request, client_pk):
    client = Beleggers.objects.get(id=client_pk)
    # form
    form = forms.PVEVersieForm(request.POST or None, initial={"client": client})

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            version_copy = form.cleaned_data["version_copy"]
            new_version = form.cleaned_data["version"]
            form.save()            
            new_version_obj = models.PVEVersie.objects.all().order_by("-id").first()
            # maak kopie van andere version, voeg nieuw toe.
            if version_copy:

                # items
                items = [i for i in version_copy.item.select_related("chapter").select_related("paragraph").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").all()]

                # keuzematrix
                bwsrt = [i for i in version_copy.bouwsoort.all()]
                tpobj = [i for i in version_copy.typeobject.all()]
                dlgrp = [i for i in version_copy.doelgroep.all()]
                old_bwsrt = [i.id for i in bwsrt]
                old_tpobj = [i.id for i in tpobj]
                old_dlgrp = [i.id for i in dlgrp]

                # chapters en paragraphs
                hfstukken = [i for i in version_copy.chapter.all()]
                prgrfs = [i for i in version_copy.paragraph.select_related("chapter").all()]
                old_hfstukken = [i.id for i in hfstukken]
                old_prgrfs = [i.id for i in prgrfs]

                # attachments
                attachments_models = version_copy.itemAttachment.all()
                attachments = []

                for attachment_model in attachments_models:
                    for item in attachment_model.items.all():
                        if item in items:
                            attachments.append(attachment_model)

                attachments = list(set(attachments))

                # make copy of all
                new_version_obj = models.PVEVersie.objects.all().order_by("-id").first()

                #keuzematrices#################
                new_bwsrt = []
                new_tpobj = []
                new_dlgrp = []

                for i in bwsrt:
                    i.pk = None
                    i.version = new_version_obj
                    new_bwsrt.append(i)

                for i in tpobj:
                    i.pk = None
                    i.version = new_version_obj
                    new_tpobj.append(i)

                for i in dlgrp:
                    i.pk = None
                    i.version = new_version_obj
                    new_dlgrp.append(i)

                # create the new models
                models.Bouwsoort.objects.bulk_create(new_bwsrt)
                models.TypeObject.objects.bulk_create(new_tpobj)
                models.Doelgroep.objects.bulk_create(new_dlgrp)

                # map the old to new model ids for new foreignkey references
                new_bwsrt = [i for i in new_version_obj.bouwsoort.all()]
                new_tpobj = [i for i in new_version_obj.typeobject.all()]
                new_dlgrp = [i for i in new_version_obj.doelgroep.all()]

                bwsrt_map = {}
                for old, new in zip(old_bwsrt, new_bwsrt):
                    bwsrt_map[old] = new

                tpobj_map = {}
                for old, new in zip(old_tpobj, new_tpobj):
                    tpobj_map[old] = new

                dlgrp_map = {}
                for old, new in zip(old_dlgrp, new_dlgrp):
                    dlgrp_map[old] = new
                
                # chapters paragravem #################
                new_hfst = []

                for i in hfstukken:
                    i.pk = None
                    i.version = new_version_obj
                    new_hfst.append(i)

                models.PVEHoofdstuk.objects.bulk_create(new_hfst)

                new_hfst = [i for i in new_version_obj.chapter.all()]

                hfst_map = {}
                for old, new in zip(old_hfstukken, new_hfst):
                    hfst_map[old] = new
                
                # paragraphs
                new_prgrf = []

                for i in prgrfs:
                    i.pk = None
                    i.version = new_version_obj
                    i.chapter = hfst_map[i.chapter.id]
                    new_prgrf.append(i)

                models.PVEParagraaf.objects.bulk_create(new_prgrf)

                new_prgrf = [i for i in new_version_obj.paragraph.all()]

                prgrf_map = {}
                for old, new in zip(old_prgrfs, new_prgrf):
                    prgrf_map[old] = new

                # finally, make new items with the new reference keys
                new_items = []
                
                for i in items:
                    new_item = models.PVEItem()
                    new_item.version = new_version_obj
                    new_item.chapter = hfst_map[i.chapter.id]

                    if i.paragraph:
                        new_item.paragraph = prgrf_map[i.paragraph.id]
                    
                    new_item.inhoud = i.inhoud
                    new_item.basisregel = i.basisregel
                    new_item.Smarthome = i.Smarthome
                    new_item.AED = i.AED
                    new_item.EntreeUpgrade = i.EntreeUpgrade
                    new_item.Pakketdient = i.Pakketdient
                    new_item.JamesConcept = i.JamesConcept
                    new_items.append(new_item)

                models.PVEItem.objects.bulk_create(new_items)
                new_items = [i for i in new_version_obj.item.prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").all().order_by("id")]

                items_map = {}
                for old, new in zip(items, new_items):
                    items_map[old.id] = new
                
                # add parameters to all items
                for bwsrt in old_bwsrt:
                    bouwsoort = models.Bouwsoort.objects.get(id=bwsrt)
                    items = list(set([items_map[item.id] for item in bouwsoort.item.all()]))
                    bwsrt_map[bwsrt].item.set(items)
                    bwsrt_map[bwsrt].save()

                for tpobj in old_tpobj:
                    typeobject = models.TypeObject.objects.get(id=tpobj)
                    items = list(set([items_map[item.id] for item in typeobject.item.all()]))
                    tpobj_map[tpobj].item.set(items)
                    tpobj_map[tpobj].save()
                    
                for dlgrp in old_dlgrp:
                    doelgroep = models.Doelgroep.objects.get(id=dlgrp)
                    items = list(set([items_map[item.id] for item in doelgroep.item.all()]))
                    dlgrp_map[dlgrp].item.set(items)
                    dlgrp_map[dlgrp].save()
                    
                    
                # connect the attachments to it
                new_attachments = []
                cur_items_obj = []

                for i in attachments:
                    cur_items_obj.append([items_map[j.id] for j in i.items.all()])

                    i.pk = None
                    i.version = new_version_obj
                    new_attachments.append(i)

                models.ItemBijlages.objects.bulk_create(new_attachments)
                new_attachments = [i for i in new_version_obj.itemAttachment.all()]

                # foreignkeys change after bulk_create
                for i, j in zip(new_attachments, cur_items_obj):
                    i.items.clear()
                    i.items.add(*j)
                    
                # copy the comment permissions
                old_comment_requirements = CommentRequirement.objects.get(version__id=version_copy.id)
                
                new_comment_requirements = CommentRequirement()
                new_comment_requirements.version = new_version_obj
                new_comment_requirements.comment_allowed.add(*[obj for obj in old_comment_requirements.comment_allowed.all()])
                new_comment_requirements.comment_required.add(*[obj for obj in old_comment_requirements.comment_required.all()])
                new_comment_requirements.attachment_allowed(*[obj for obj in old_comment_requirements.attachment_allowed.all()])
                new_comment_requirements.save()

            return redirect("pveversietable", client_pk=client_pk)

    context = {}
    context["form"] = form
    context["key"] = client_pk
    context["client"] = client
    return render(request, "partials/addpveversionform.html", context)

@staff_member_required(login_url=reverse_lazy('logout'))
def BeleggerVersieTable(request, client_pk):
    key = Beleggers.objects.get(id=client_pk)
    queryset = models.PVEVersie.objects.filter(client__id=key.id)
    context = {}
    context["queryset"] = queryset
    context["key"] = key
    return render(request, "partials/pveversiontable.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def VersieActiviteit(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)
    version_pk = version.id
    context = {}
    context["version"] = version
    context["version_pk"] = version_pk
    return render(request, "partials/getpveactivity.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def ActivateVersie(request, version_pk):
    version = models.PVEVersie.objects.filter(id=version_pk).first()
    version.public = True
    version.save()
    messages.warning(request, f"Versie geactiveerd: {version}")
    return redirect("getpveactivity", version_pk=version_pk)

@staff_member_required(login_url=reverse_lazy("logout"))
def DeactivateVersie(request, version_pk):
    version = models.PVEVersie.objects.filter(id=version_pk).first()
    version.public = False
    version.save()
    messages.warning(request, f"Versie gedeactiveerd: {version}")
    return redirect("getpveactivity", version_pk=version_pk)

@staff_member_required(login_url=reverse_lazy("logout"))
def PVEBewerkOverview(request, version_pk):
    pve_versie = models.PVEVersie.objects.get(id=version_pk)
    client = pve_versie.client
    context = {}
    context["pve_versie"] = pve_versie
    context["client_pk"] = client.id
    return render(request, "PVEBewerkOverview.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEHoofdstukListView(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)
    chapters = version.chapter.all()
    context = {}
    context["chapters"] = chapters
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "PVEListHfst.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def DownloadWorksheet(request, excelFilename):
    # if pve version pk is used as the url (very hacky)
    try:
        excelFilename = int(excelFilename)
        if models.PVEItem.objects.filter(version__id=excelFilename).exists():
            version_pk = excelFilename
            items = models.PVEItem.objects.select_related("chapter").select_related("paragraph").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(version__id=version_pk)
            worksheet = writeExcel.ExcelMaker()
            excelFilename = worksheet.linewriter(items)
    except ValueError:
        pass
        
    #otherwise just use this filename
    excelFilename = f"/{excelFilename}.xlsx"

    fl_path = settings.EXPORTS_ROOT
    try:
        fl = open(fl_path + excelFilename, "rb")
    except OSError:
        raise Http404("404")

    response = HttpResponse(
        fl,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "inline; filename=%s" % excelFilename

    return response


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEaddchapterView(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)
    form = forms.ChapterForm(request.POST or None)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEHoofdstuk = models.PVEHoofdstuk()
            PVEHoofdstuk.chapter = form.cleaned_data["chapter"]
            PVEHoofdstuk.version = version
            PVEHoofdstuk.save()
            return redirect("chapterview", version_pk=version_pk)

    chapters = version.chapter.all()

    context = {}
    context["chapters"] = chapters
    context["version_pk"] = version_pk
    context["version"] = version
    context["form"] = form
    return render(request, "addchapterform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def PVEeditchapterView(request, version_pk, pk):
    version = models.PVEVersie.objects.get(id=version_pk)

    if not version.chapter.filter(id=pk):
        return Http404("404")

    # form, initial chapter in specific onderdeel
    chapter = version.chapter.get(id=pk)
    form = forms.ChapterForm(request.POST or None, instance=chapter)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEchapter = version.chapter.get(id=pk)
            PVEchapter.chapter = form.cleaned_data["chapter"]
            PVEchapter.save()
            return redirect("chapterview", version_pk=version_pk)

    chapters = version.chapter.all()

    # form, initial chapter in specific onderdeel
    context = {}
    context["chapters"] = chapters
    context["chapter"] = chapter
    context["version_pk"] = version_pk
    context["version"] = version
    context["pk"] = pk
    context["form"] = form
    return render(request, "changechapterform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def paragraphlistView(request, version_pk, pk):
    pk = int(pk)
    version = models.PVEVersie.objects.get(id=version_pk)

    if version.chapter.filter(id=pk).exists():
        chapter = version.chapter.get(id=pk)
    else:
        raise Http404("404")

    items = chapter.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraph is None and not chapter.paragraph.all():
            return redirect(
                "itemlistview", version_pk=version_pk, chapter_id=pk, paragraph_id=0
            )

    # otherwise, show paragraphs
    context = {}
    context["paragraphs"] = chapter.paragraph.all()
    context["sectie"] = chapter
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "PVEParagraphList.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def paragraphlistViewEdit(request, version_pk, pk):
    pk = int(pk)
    version = models.PVEVersie.objects.get(id=version_pk)

    if version.chapter.filter(id=pk).exists():
        chapter = version.chapter.get(id=pk)
    else:
        raise Http404("404")

    items = chapter.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraph is None:
            return redirect(
                "itemlistviewedit", version_pk=version_pk, chapter_id=pk, paragraph_id=0
            )

    # otherwise, show paragraphs
    context = {}
    context["paragraphs"] = chapter.paragraph.all()
    context["sectie"] = chapter
    context["id"] = pk
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "PVEParagraphListEdit.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def paragraphlistViewDelete(request, version_pk, pk):
    pk = int(pk)
    version = models.PVEVersie.objects.get(id=version_pk)

    if version.chapter.filter(id=pk).exists():
        chapter = version.chapter.get(id=pk)
    else:
        raise Http404("404")

    items = chapter.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraph is None:
            return redirect(
                "itemlistviewdelete", version_pk=version_pk, chapter_id=pk, paragraph_id=0
            )

    # otherwise, show paragraphs
    context = {}
    context["paragraphs"] = chapter.paragraph.all()
    context["sectie"] = chapter
    context["id"] = pk
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "PVEParagraphListDelete.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEaddparagraphView(request, version_pk, pk):
    pk = int(pk)
    version = models.PVEVersie.objects.get(id=version_pk)
    
    if version.chapter.filter(id=pk).exists():
        chapter = version.chapter.filter(id=pk).first()
    else:
        raise Http404("404")

    form = forms.ParagraafForm(request.POST or None, initial={"chapter": chapter})

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEParagraaf = models.PVEParagraaf()
            PVEParagraaf.chapter = chapter
            PVEParagraaf.paragraph = form.cleaned_data["paragraph"]
            PVEParagraaf.version = version
            PVEParagraaf.save()
            return HttpResponseRedirect(reverse("viewParagraaf", args=(version_pk, pk)))

    # View below modal
    items = models.PVEItem.objects.filter(chapter=chapter)

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraph is None:
            return redirect(
                "itemlistview", version_pk=version_pk, chapter_id=pk, paragraph_id=0
            )


    # otherwise, show paragraphs
    context = {}
    context["paragraphs"] = chapter.paragraph.all()
    context["sectie"] = chapter
    context["form"] = form
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "addparagraphform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEeditparagraphView(request, version_pk, pk):
    pk = int(pk)
    version = models.PVEVersie.objects.get(id=version_pk)

    if version.paragraph.filter(id=pk).exists():
        paragraph = version.paragraph.filter(id=pk).first()
        chapter = paragraph.chapter
    else:
        raise Http404("404")
    form = forms.ParagraafForm(request.POST or None, instance=paragraph)

    if request.method == "POST":
        # check whether it's valid:
        if form.is_valid():
            PVEparagraph = version.paragraph.filter(id=pk).first()
            PVEparagraph.paragraph = form.cleaned_data["paragraph"]
            PVEparagraph.version = version
            PVEparagraph.save()
            return HttpResponseRedirect(
                reverse(
                    "viewParagraaf",
                    args=(
                        version_pk,
                        chapter.id,
                    ),
                )
            )

    # View below modal
    items = chapter.item.all()

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraph is None:
            return redirect(
                "itemlistview",
                version_pk=version_pk,
                chapter_id=chapter.id,
                paragraph_id=0,
            )


    # otherwise, show paragraphs
    context = {}
    context["paragraphs"] = chapter.paragraph.all()
    context["sectie"] = chapter
    context["paragraph_id"] = pk
    context["id"] = chapter.id
    context["form"] = form
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "changeparagraphform.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def itemListView(request, version_pk, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)
    chapter_id = int(chapter_id)

    version = models.PVEVersie.objects.get(id=version_pk)
    
    # Chapter_id doesnt exist
    if not version.chapter.filter(id=chapter_id).exists():
        raise Http404("404")

    chapter = version.chapter.get(id=chapter_id)

    paragraphs_exist = chapter.paragraph.exists()

    # if no paragraph given but there are paragraphs in this chapter
    if paragraph_id == 0:
        if paragraphs_exist:
            raise Http404("404")

    # if paragraphs arent connected to this chapter
    if paragraph_id != 0:
        if not paragraphs_exist:
            raise Http404("404")

        paragraph = version.paragraph.get(id=paragraph_id)

    context = {}

    # item niet in een paragraph: haal ze van een chapter
    if paragraph_id == 0:
        context["queryset"] = chapter.item.all()
        context["chapter"] = chapter
    else:
        context["queryset"] = paragraph.item.all()
        context["paragraph"] = paragraph
        context["chapter"] = chapter

    context["paragraph_id"] = paragraph_id
    context["chapter_id"] = chapter_id
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "PVEItemList.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def viewItemView(request, version_pk, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(version__id=version_pk, id=pk).exists():
        PVEItem = models.PVEItem.objects.filter(version__id=version_pk, id=pk).first()
    else:
        raise Http404("Item does not exist.")

    context = {}

    if models.ItemBijlages.objects.filter(version__id=version_pk, items__id__contains=PVEItem.id).exists():
        attachment = models.ItemBijlages.objects.filter(version__id=version_pk, items__id__contains=PVEItem.id).first()
        context["attachment"] = attachment
        context["attachmentsame"] = attachment.name

    context["PVEItem"] = PVEItem
    context["Bouwsoort"] = PVEItem.Bouwsoort.all()
    context["TypeObject"] = PVEItem.TypeObject.all()
    context["Doelgroep"] = PVEItem.Doelgroep.all()

    if not PVEItem.paragraph:
        context["queryset"] = models.PVEItem.objects.filter(
            version__id=version_pk, chapter=PVEItem.chapter
        )
        context["chapter"] = PVEItem.chapter
        context["paragraph_id"] = 0
    else:
        context["queryset"] = models.PVEItem.objects.filter(
            version__id=version_pk, chapter=PVEItem.chapter
        ).filter(version__id=version_pk, paragraph=PVEItem.paragraph)
        context["paragraph"] = PVEItem.paragraph
        context["chapter"] = PVEItem.chapter
        context["paragraph_id"] = PVEItem.paragraph.id

    context["chapter_id"] = PVEItem.chapter.id
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(id=version_pk)
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
            attachment = models.ItemBijlages.objects.filter(items__id__contains=item.id).first().attachment
    else:           
        attachment = models.ItemBijlages.objects.filter(id=pk).first().attachment


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
            Params={"Bucket": bucket_name, "Key": str(attachment)},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return HttpResponseRedirect(response)


@staff_member_required(login_url=reverse_lazy("logout"))
def editItemView(request, version_pk, pk):
    pk = int(pk)
    if models.PVEItem.objects.filter(version__id=version_pk, id=pk).exists():
        PVEItem = models.PVEItem.objects.filter(version__id=version_pk, id=pk).first()
    else:
        raise Http404("Item does not exist.")
    
    form = forms.PVEItemEditForm(request.POST or None, request.FILES or None, instance=PVEItem)
    form.fields["existing_attachment"].queryset = models.ItemBijlages.objects.filter(
        version__id=version_pk
    ).all()
    form.fields["Bouwsoort"].queryset = models.Bouwsoort.objects.filter(
        version__id=version_pk
    ).all()    
    form.fields["TypeObject"].queryset = models.TypeObject.objects.filter(
        version__id=version_pk
    ).all()    
    form.fields["Doelgroep"].queryset = models.Doelgroep.objects.filter(
        version__id=version_pk
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

            if form.cleaned_data["attachment"]:
                attachment_item = models.ItemBijlages()
                attachment_item.attachment = form.cleaned_data["attachment"]
                attachment_item.version = models.PVEVersie.objects.filter(id=version_pk).first()
                attachment_item.save()
                attachment_item.items.add(PVEItem)
                attachment_item.name = f"Bijlage {attachment_item.pk}"
                attachment_item.save()

            if form.cleaned_data["existing_attachment"]:
                existing_attachment = form.cleaned_data["existing_attachment"]
                existing_attachment.items.add(PVEItem)

            # and reverse
            return HttpResponseRedirect(reverse("viewitem", args=(version_pk, pk)))

    # if get method, just render the empty form
    context = {}
    context["form"] = form
    context["id"] = pk
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(id=version_pk)
    return render(request, "PVEItemEdit.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def addItemView(request, version_pk, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)

    form = forms.PVEItemEditForm(request.POST or None, request.FILES or None)
    form.fields["existing_attachment"].queryset = models.ItemBijlages.objects.filter(
        version__id=version_pk
    ).all()
    form.fields["Bouwsoort"].queryset = models.Bouwsoort.objects.filter(
        version__id=version_pk
    ).all()    
    form.fields["TypeObject"].queryset = models.TypeObject.objects.filter(
        version__id=version_pk
    ).all()    
    form.fields["Doelgroep"].queryset = models.Doelgroep.objects.filter(
        version__id=version_pk
    ).all()

    if request.method == "POST":

        # check validity
        if form.is_valid():
            PVEItem = models.PVEItem()
            PVEItem.version = models.PVEVersie.objects.get(id=version_pk)
            # get parameters and save new item
            if int(paragraph_id) != 0:
                PVEItem.paragraph = models.PVEParagraaf.objects.filter(
                    version__id=version_pk, id=paragraph_id
                ).first()

            PVEItem.chapter = models.PVEHoofdstuk.objects.filter(
                version__id=version_pk, id=chapter_id
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

            if form.cleaned_data["attachment"]:
                attachment_item = models.ItemBijlages()
                attachment_item.attachment = form.cleaned_data["attachment"]
                attachment_item.version = models.PVEVersie.objects.filter(id=version_pk).first()
                attachment_item.save()
                attachment_item.items.add(PVEItem)
                attachment_item.name = f"Bijlage {attachment_item.pk}"
                attachment_item.save()
                
            if form.cleaned_data["existing_attachment"]:
                existing_attachment = form.cleaned_data["existing_attachment"]
                existing_attachment.items.add(PVEItem)

            pk = PVEItem.id

            # and reverse
            return HttpResponseRedirect(reverse("viewitem", args=(version_pk, pk)))

    context = {}
    context["form"] = form
    context["chapter_id"] = chapter_id
    context["paragraph_id"] = int(paragraph_id)
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(id=version_pk)
    return render(request, "PVEAddItem.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def deleteItemView(request, version_pk, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(version__id=version_pk, id=pk).exists():
        PVEItem = models.PVEItem.objects.filter(version__id=version_pk, id=pk).first()
        chapter = PVEItem.chapter
        paragraph = PVEItem.paragraph
    else:
        raise Http404("404.")

    PVEItem.delete()

    messages.success(request, f"Regel {pk} verwijderd.")

    if not paragraph:
        return HttpResponseRedirect(
            reverse(
                "viewParagraaf",
                args=(
                    version_pk,
                    chapter.id,
                ),
            )
        )

    return HttpResponseRedirect(
        reverse("itemlistview", args=(version_pk, chapter.id, paragraph.id))
    )


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEdeletechapterView(request, version_pk, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(version__id=version_pk, id=pk).exists():
        PVEHoofdstuk = models.PVEHoofdstuk.objects.filter(
            version__id=version_pk, id=pk
        ).first()
        chapter = PVEHoofdstuk.chapter
    else:
        raise Http404("404.")

    PVEHoofdstuk.delete()

    messages.success(request, f"Hoofdstuk {chapter} verwijderd.")

    return redirect("chapterview", version_pk=version_pk)


@staff_member_required(login_url=reverse_lazy("logout"))
def PVEdeleteparagraphView(request, version_pk, pk):
    pk = int(pk)
    version = models.PVEVersie.objects.get(id=version_pk)

    if version.paragraph.filter(id=pk).exists():
        PVEParagraaf = version.paragraph.get(id=pk)
        chapter = PVEParagraaf.chapter
        paragraph = PVEParagraaf.paragraph
    else:
        raise Http404("404.")

    PVEParagraaf.delete()

    messages.success(request, f"Paragraaf {paragraph} verwijderd.")

    return HttpResponseRedirect(
        reverse("viewParagraaf", args=(version_pk, chapter.id))
    )


@staff_member_required(login_url=reverse_lazy("logout"))
def parameterchoicesView(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)

    context = {}
    context["bouwsoorten"] = version.bouwsoort.all()
    context["typeObjecten"] = version.typeobject.all()
    context["doelgroepen"] = version.doelgroep.all()
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "parameterchoice.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def addparameterchoiceView(request, version_pk, type_id):
    type_id = int(type_id)
    version = models.PVEVersie.objects.get(id=version_pk)

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
            item.version = version
            item.save()

            return HttpResponseRedirect(
                reverse("parameterchoicesview", args=(version_pk,))
            )

    form = forms.KiesParameterForm()

    context = {}
    context["form"] = form
    context["type_id"] = type_id
    context["bouwsoorten"] = version.bouwsoort.all()
    context["typeObjecten"] = version.typeobject.all()
    context["doelgroepen"] = version.doelgroep.all()
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "addparameterchoice.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def addparameterchoiceform(request, version_pk, type):
    type = int(type)
    version = models.PVEVersie.objects.get(id=version_pk)
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
            item.version = version
            item.save()

            return redirect("parameterchoicedetail", version_pk=version_pk, type=type, parameter_id=item.pk)


    context = {}
    context["form"] = form
    context["type"] = type
    context["version_pk"] = version_pk
    context["version"] = version
    return render(request, "partials/addparameterchoiceform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def parameterchoiceform(request, version_pk, type, parameter_id):
    version = models.PVEVersie.objects.get(id=version_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:  # Bouwsoort
        if not version.bouwsoort.filter(id=parameter_id):
            raise Http404("404")

        parameter = version.bouwsoort.filter(id=parameter_id).first()

    if type == 2:  # Type Object
        if not version.typeobject.filter(id=parameter_id):
            raise Http404("404")

        parameter = version.typeobject.filter(
            id=parameter_id
        ).first()

    if type == 3:  # Doelgroep
        if not version.doelgroep.filter(id=parameter_id):
            raise Http404("404")

        parameter = version.doelgroep.filter(id=parameter_id).first()

    form = forms.KiesParameterForm(request.POST or None, initial={"parameter": parameter.parameter})

    context = {}
    context["form"] = form
    context["version_pk"] = version_pk
    context["version"] = version
    context["type"] = type
    context["parameter_id"] = parameter_id
    context["parameter"] = parameter

    if request.method == "POST":
        if form.is_valid():
            parameter.parameter = form.cleaned_data["parameter"]
            parameter.save()

            return redirect("parameterchoicedetail", version_pk=version_pk, type=type, parameter_id=parameter_id)
    

    return render(request, "partials/parameterchoiceform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def parameterchoicedetail(request, version_pk, type, parameter_id):
    version = models.PVEVersie.objects.get(id=version_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:  # Bouwsoort
        if not version.bouwsoort.filter(id=parameter_id):
            raise Http404("404")

        parameter = version.bouwsoort.filter(id=parameter_id).first()

    if type == 2:  # Type Object
        if not version.typeobject.filter(id=parameter_id):
            raise Http404("404")

        parameter = version.typeobject.filter(
            id=parameter_id
        ).first()

    if type == 3:  # Doelgroep
        if not version.doelgroep.filter(id=parameter_id):
            raise Http404("404")

        parameter = version.doelgroep.filter(id=parameter_id).first()

    context = {}
    context["version_pk"] = version_pk
    context["version"] = version
    context["type"] = type
    context["parameter_id"] = parameter_id
    context["parameter"] = parameter
    context["type_id"] = type
    return render(request, "partials/parameterchoicedetail.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def parameterchoicetable(request, version_pk, type):
    version = models.PVEVersie.objects.get(id=version_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:  # Bouwsoort
        if not version.bouwsoort.all():
            raise Http404("404")

        parameters = version.bouwsoort.all()
        parameter_name = "Bouwsoorten"

    if type == 2:  # Type Object
        if not version.typeobject.all():
            raise Http404("404")

        parameters = version.typeobject.all()
        parameter_name = "Type Objecten"

    if type == 3:  # Doelgroep
        if not version.doelgroep.all():
            raise Http404("404")

        parameters = version.doelgroep.all()

        parameter_name = "Doelgroepen"

    context = {}
    context["version_pk"] = version_pk
    context["version"] = version
    context["parameters"] = parameters
    context["type_id"] = type
    context["parameter_name"] = parameter_name
    return render(request, "partials/parameterchoicetable.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def parameterchoicemodaladd(request, version_pk, type):
    version = models.PVEVersie.objects.get(id=version_pk)

    if type != 1 and type != 2 and type != 3:
        raise Http404("404")

    if type == 1:
        name = "Bouwsoort"
    if type == 2:
        name = "Type Object"
    if type == 3:
        name = "Doelgroep"
    form = forms.KiesParameterForm(request.POST or None)

    context = {}
    context["form"] = form
    context["version_pk"] = version_pk
    context["version"] = version
    context["type"] = type
    context["type_id"] = type
    context["name"] = name

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
            item.version = version
            item.save()

            return redirect("parameterchoicetable", version_pk=version_pk, type=type)

    return render(request, "partials/addparameterchoiceform.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def deleteparameterchoiceView(request, version_pk, type_id, item_id):

    type_id = int(type_id)
    item_id = int(item_id)
    version_pk = int(version_pk)
    version = models.PVEVersie.objects.get(id=version_pk)

    if type_id != 1 and type_id != 2 and type_id != 3:
        raise Http404("404")

    if type_id == 1:  # Bouwsoort
        if not version.bouwsoort.filter(id=item_id):
            raise Http404("404")

        item = version.bouwsoort.filter(id=item_id).first()

    if type_id == 2:  # Type Object
        if not version.typeobject.filter(id=item_id):
            raise Http404("404")

        item = version.typeobject.filter(
            id=item_id
        ).first()

    if type_id == 3:  # Doelgroep
        if not version.doelgroep.filter(id=item_id):
            raise Http404("404")

        item = version.doelgroep.filter(id=item_id).first()

    parameter = item.parameter

    if request.headers["HX-Prompt"] == "VERWIJDEREN":
        item.delete()
        messages.warning(request, f"Parameter: {parameter} verwijderd.")
        return HttpResponse("")
    else:
        messages.warning(request, f"Onjuiste invulling. Probeer het opnieuw.")
        return redirect("parameterchoicesview", version_pk=version_pk)

#attachmentsView
#attachmentDetail
#attachmentEdit
#attachmentAdd
#attachmentDelete
#ItemBijlage: version items attachment name
@staff_member_required(login_url=reverse_lazy("logout"))
def attachmentsView(request, version_pk):
    context = {}
    context["attachments"] = models.ItemBijlages.objects.filter(version__id=version_pk)
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(pk=version_pk)
    return render(request, "attachmentView.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def attachmentDetail(request, version_pk, pk):
    attachments = models.ItemBijlages.objects.filter(version__id=version_pk)
    attachment = attachments.get(id=pk)

    items = attachment.items.all()

    context = {}
    context["attachment"] = attachment
    context["attachments"] = attachments
    context["items"] = items
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(pk=version_pk)
    return render(request, "attachmentDetail.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def attachmentAdd(request, version_pk):
    version = models.PVEVersie.objects.get(id=version_pk)
    form = forms.attachmentEditForm(request.POST or None, request.FILES or None)
    form.fields["items"].queryset = version.item.all()

    if request.method == "POST":

        # check validity
        if form.is_valid():
            new_attachment = models.ItemBijlages()
            new_attachment.attachment = form.cleaned_data["attachment"]
            new_attachment.version = version
            if form.cleaned_data["name"]:
                new_attachment.name = form.cleaned_data["name"]
            new_attachment.save()
            new_attachment.items.set(form.cleaned_data["items"])
            new_attachment.save()

            return HttpResponseRedirect(
                reverse("attachmentview", args=(version_pk,))
            )
        else:
            print(form.errors())

    context = {}
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(pk=version_pk)
    context["form"] = form
    return render(request, "attachmentAdd.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def attachmentEdit(request, version_pk, pk):
    version = models.PVEVersie.objects.get(id=version_pk)

    attachment = version.itemAttachment.get(id=pk)
    form = forms.attachmentEditForm(request.POST or None, request.FILES or None, initial={'name':attachment.name, 'attachment':attachment.attachment, 'items':attachment.items.all()})
    form.fields["items"].queryset = version.item.all()

    if request.method == "POST":
        # get user entered form

        # check validity
        if form.is_valid():
            new_attachment = attachment
            if form.cleaned_data["attachment"]:
                new_attachment.attachment = form.cleaned_data["attachment"]
            new_attachment.version = version
            if form.cleaned_data["name"]:
                new_attachment.name = form.cleaned_data["name"]
            new_attachment.save()
            new_attachment.items.set(form.cleaned_data["items"])
            new_attachment.save()

            return HttpResponseRedirect(
                reverse("attachmentview", args=(version_pk,))
            )
        else:
            print(form.errors)

    context = {}
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(pk=version_pk)
    context["form"] = form
    context["attachment"] = attachment
    return render(request, "attachmentEdit.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def attachmentDelete(request, version_pk, pk):
    attachment = models.ItemBijlages.objects.filter(version__id=version_pk, id=pk)
    attachment.delete()
    return HttpResponseRedirect(
        reverse("attachmentview", args=(version_pk,))
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
    clients = Beleggers.objects.all()
    context = {}
    context["clients"] = clients
    return render(request, "accountOverview.html", context)


@staff_member_required(login_url=reverse_lazy("logout"))
def EditCommentPermissionsOverview(request, version_pk):
    qs = CommentRequirement.objects.prefetch_related("comment_allowed").prefetch_related("comment_required").prefetch_related("attachment_allowed").prefetch_related("attachment_required").prefetch_related("costs_allowed").prefetch_related("costs_required").get(version__id=version_pk)
    
    statuses = CommentStatus.objects.all()
    status_dict = {}
    
    for status in statuses:
        status_dict[status.status] = {
            "comment_allowed": True if status in qs.comment_allowed.all() else False,
            "comment_required": True if status in qs.comment_required.all() else False,
            "attachment_allowed": True if status in qs.attachment_allowed.all() else False,
            "attachment_required": True if status in qs.attachment_required.all() else False,
            "costs_allowed": True if status in qs.costs_allowed.all() else False,
            "costs_required": True if status in qs.costs_required.all() else False
        }

    print(status_dict)
    context = {}
    context["version_pk"] = version_pk
    context["version"] = models.PVEVersie.objects.get(id=version_pk)
    context["status_dict"] = status_dict
    return render(request, "editCommentPermissionsOverview.html", context)

@staff_member_required(login_url=reverse_lazy("logout"))
def detailReqButton(request, version_pk, active, status_str, type):
    context = {}
    context["active"] = active
    context["version_pk"] = version_pk
    context["status_str"] = status_str
    context["type"] = type
    return render(request, 'partials/detailCommentReqButton.html', context)


@staff_member_required(login_url=reverse_lazy("logout"))
def makeReqActive(request, version_pk, status_str, type):
    qs = CommentRequirement.objects.prefetch_related("comment_allowed").prefetch_related("comment_required").prefetch_related("attachment_allowed").prefetch_related("attachment_required").prefetch_related("costs_allowed").prefetch_related("costs_required").get(version__id=version_pk)

    status = CommentStatus.objects.get(status=status_str)
    if type == 1:
        qs.comment_allowed.add(status)
    if type == 2:
        qs.comment_required.add(status)
    if type == 3:
        qs.attachment_allowed.add(status)
    if type == 4:
        qs.attachment_required.add(status)
    if type == 5:
        qs.costs_allowed.add(status)
    if type == 6:
        qs.costs_required.add(status)
        
    context = {}
    context["active"] = 1
    context["version_pk"] = version_pk
    context["status_str"] = status_str
    context["type"] = type
    return render(request, 'partials/detailCommentReqButton.html', context)

@staff_member_required(login_url=reverse_lazy("logout"))
def makeReqInactive(request, version_pk, status_str, type):
    qs = CommentRequirement.objects.prefetch_related("comment_allowed").prefetch_related("comment_required").prefetch_related("attachment_allowed").prefetch_related("attachment_required").prefetch_related("costs_allowed").prefetch_related("costs_required").get(version__id=version_pk)

    status = CommentStatus.objects.get(status=status_str)
    
    if type == 1:
        qs.comment_allowed.remove(status)
    if type == 2:
        qs.comment_required.remove(status)
    if type == 3:
        qs.attachment_allowed.remove(status)
    if type == 4:
        qs.attachment_required.remove(status)
    if type == 5:
        qs.costs_allowed.remove(status)
    if type == 6:
        qs.costs_required.remove(status)
        
    context = {}
    context["active"] = 0
    context["version_pk"] = version_pk
    context["status_str"] = status_str
    context["type"] = type
    return render(request, 'partials/detailCommentReqButton.html', context)
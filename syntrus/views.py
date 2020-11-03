from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from syntrus import forms
from project.models import Project, PVEItemAnnotation, Beleggers
from users.models import Invitation, CustomUser
from syntrus.models import FAQ, Room, CommentStatus
from syntrus.forms import KoppelDerdeUserForm, StartProjectForm
from users.forms import AcceptInvitationForm
from app import models
import datetime
from django.utils import timezone
from geopy.geocoders import Nominatim
from django.db.models import Q
from utils import writePdf
from utils import createBijlageZip
from utils.writePdf import PDFMaker
from utils.createBijlageZip import ZipMaker
import secrets
from django.core.mail import send_mail
import pytz
utc=pytz.UTC


def LoginView(request):
    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            return redirect('dashboard_syn')

    if request.method == "POST":
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            (username, password) = (
                form.cleaned_data["username"], form.cleaned_data["password"])
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard_syn')
            else:
                messages.warning(request, 'Invalid login credentials')

    # render the page
    context = {}
    context["form"] = forms.LoginForm()

    return render(request, 'login_syn.html', context)
 

@login_required
def DashboardView(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user.username, belegger__naam='Syntrus'):
        projects = Project.objects.filter(belegger__naam='Syntrus').filter(permitted__username__contains=request.user.username).distinct()
        context["projects"] = projects
    
    if PVEItemAnnotation.objects.filter(gebruiker=request.user):
        opmerkingen = PVEItemAnnotation.objects.filter(gebruiker=request.user, project__belegger__naam='Syntrus')
        context["opmerkingen"] = opmerkingen

    if request.user.type_user == 'B':
        return render(request, 'dashboardBeheerder_syn.html', context)
    if request.user.type_user == 'SB':
        return render(request, 'dashboardBeheerder_syn.html', context)
    if request.user.type_user == "SOG":
        return render(request, 'dashboardOpdrachtgever_syn.html', context)
    if request.user.type_user == "SD":
        return render(request, 'dashboardDerde_syn.html', context)

@login_required(login_url='login_syn')
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
    return render(request, 'FAQ_syn.html', context)

@login_required(login_url='login_syn')
def LogoutView(request):
    logout(request)
    return redirect('login_syn')

# Create your views here.
@login_required(login_url='login_syn')
def GeneratePVEView(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    if request.method == "POST":
        # get user entered form
        form = forms.PVEParameterForm(request.POST)
        # check validity
        if form.is_valid():
            # get parameters, find all pveitems with that
            (Bouwsoort1, TypeObject1, Doelgroep1, Bouwsoort2, TypeObject2, Doelgroep2, Bouwsoort3, TypeObject3, Doelgroep3, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort1"], form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"], form.cleaned_data["Bouwsoort2"], form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"], form.cleaned_data["Bouwsoort3"], form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )
            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(basisregel=True)
            basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort1))

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort2))
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort3))
            if TypeObject1:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(TypeObject__parameter__contains=TypeObject1))
            if TypeObject2:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(TypeObject__parameter__contains=TypeObject2))
            if TypeObject3:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(TypeObject__parameter__contains=TypeObject3))
            if Doelgroep1:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Doelgroep__parameter__contains=Doelgroep1))
            if Doelgroep2:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Doelgroep__parameter__contains=Doelgroep2))
            if Doelgroep3:
                basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Doelgroep__parameter__contains=Doelgroep3))
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(AED=True)))
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Smarthome=True)))
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(EntreeUpgrade=True)))
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Pakketdient=True)))
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(JamesConcept=True)))

            basic_PVE = basic_PVE.order_by('id')
            # make pdf
            parameters = []
            if Bouwsoort1:
                parameters += f"{Bouwsoort1.parameter} (Hoofd)",
            if Bouwsoort2:
                parameters += f"{Bouwsoort2.parameter} (Sub)",
            if Bouwsoort3:
                parameters += f"{Bouwsoort3.parameter} (Sub)",
            if TypeObject1:
                parameters += f"{TypeObject1.parameter} (Hoofd)",
            if TypeObject2:
                parameters += f"{TypeObject2.parameter} (Sub)",
            if TypeObject3:
                parameters += f"{TypeObject3.parameter} (Sub)",
            if Doelgroep1:
                parameters += f"{Doelgroep1.parameter} (Hoofd)",
            if Doelgroep2:
                parameters += f"{Doelgroep2.parameter} (Sub)",
            if Doelgroep3:
                parameters += f"{Doelgroep3.parameter} (Sub)",
            date = datetime.datetime.now()
            fileExt = "%s%s%s%s%s%s" % (
                date.strftime("%H"),
                date.strftime("%M"),
                date.strftime("%S"),
                date.strftime("%d"),
                date.strftime("%m"),
                date.strftime("%Y")
            )
            filename = f"PvE-{fileExt}"
            zipFilename = f"PvE_Compleet-{fileExt}"
            pdfmaker = writePdf.PDFMaker()
            pdfmaker.makepdf(filename, basic_PVE, parameters)
            # get bijlagen
            bijlagen = [item for item in basic_PVE if item.bijlage]
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
            return render(request, 'PVEResult_syn.html', context)
        else:
            messages.warning(request, "Vul de verplichte keuzes in.")

    # if get method, just render the empty form
    context = {}
    context["form"] = forms.PVEParameterForm()
    return render(request, 'GeneratePVE_syn.html', context)

@login_required
def download_pve_overview(request):    
    projects = Project.objects.filter(permitted__username__contains=request.user.username)

    context = {}
    context["projects"] = projects
    return render(request, 'downloadPveOverview_syn.html', context)
    
@login_required
def download_pve(request, pk):
    if not Project.objects.filter(id=pk):
        raise Http404('404')
    
    if request.user.type_user != 'B':
        if not Project.objects.filter(id=pk, permitted__username__contains=request.user.username):
            raise Http404('404')

    project = Project.objects.filter(id=pk).first()
    basic_PVE = models.PVEItem.objects.filter(projects__id__contains=pk)

    # make sure pve is ordered
    basic_PVE = basic_PVE.order_by('id')
    # make pdf
    parameters = []

    parameters += f"Project: {project.naam}",

    date = datetime.datetime.now()

    fileExt = "%s%s%s%s%s%s" % (
        date.strftime("%H"),
        date.strftime("%M"),
        date.strftime("%S"),
        date.strftime("%d"),
        date.strftime("%m"),
        date.strftime("%Y")
    )

    filename = f"PvE-{fileExt}"
    zipFilename = f"PvE_Compleet-{fileExt}"

    pdfmaker = writePdf.PDFMaker()
    pdfmaker.makepdf(filename, basic_PVE, parameters)

    # get bijlagen
    bijlagen = [item for item in basic_PVE if item.bijlage]

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
    return render(request, 'PVEResult_syn.html', context)

@login_required(login_url='login_syn')
def ViewProjectOverview(request):
    projects = Project.objects.filter(belegger__naam='Syntrus', permitted__username__contains=request.user.username)

    context = {}
    context["projects"]=projects
    return render(request, 'MyProjecten_syn.html', context)

@login_required(login_url='login_syn')
def ViewProject(request, pk):
    if not Project.objects.filter(id=pk, belegger__naam='Syntrus'):
        return render(request, '404_syn.html')

    if not Project.objects.filter(id=pk, belegger__naam='Syntrus', permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk, belegger__naam='Syntrus').first()

    if Room.objects.filter(project=project):
        chatroom = Room.objects.get(project=project)
    else:
        chatroom = Room()
        chatroom.description = f"Chat van {project.naam}"
        chatroom.project = project
        chatroom.save()

    medewerkers = [medewerker.username for medewerker in project.permitted.all()]
    context = {}
    context["project"] = project
    context["chatroom"] = chatroom
    context["medewerkers"] = medewerkers
    return render(request, 'ProjectPagina_syn.html', context)    

@login_required(login_url='login_syn')
def AddCommentOverview(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user):
        projects = Project.objects.filter(permitted__username__contains=request.user)
        context["projects"] = projects

    return render(request, 'plusOpmerkingOverview_syn.html', context)

@login_required(login_url='login_syn')
def MyComments(request, pk):
    context = {}

    if not Project.objects.filter(pk=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(pk=pk).first()

    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')
    
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("item_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(dict(item_id=item_id, annotation=opmrk, status=status, kostenConsequenties=kosten))
            for item_id, opmrk, status, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()]
        # second check, save in annotations. May this code save the meek.

        for form in ann_forms:
            # true comment if either comment or voldoet
            if form.cleaned_data["annotation"] or form.cleaned_data["status"]:
                if PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()):
                    ann = PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()).first()
                else:
                    raise Http404("404.")
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()
                ann.annotation = form.cleaned_data["annotation"]
                ann.status = form.cleaned_data["status"]
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                if form.cleaned_data["annbijlage"]:
                    ann.annbijlage = form.cleaned_data["annbijlage"]
                ann.save()
        return redirect('mijnopmerkingen_syn', pk=project.id)        

    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    comments = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user)
    ann_forms = []

    for comment in comments:
            ann_forms.append(forms.PVEItemAnnotationForm(initial={
                'item_id':comment.item.id,
                'annotation':comment.annotation,
                'status':comment.status,
                'kostenConsequenties':comment.kostenConsequenties,
                'annbijlage':comment.annbijlage,
                }))

    # easy entrance to item ids
    form_item_ids = [comment.item.id for comment in comments]

    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(project=project, gebruiker=request.user)
    context["project"] = project
    context["forms"] = ann_forms
    context["totale_kosten"] = totale_kosten
    context["form_item_ids"] = form_item_ids

    return render(request, 'MyComments.html', context)

@login_required(login_url='login_syn')
def AllComments(request, pk):
    context = {}

    if not Project.objects.filter(pk=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(pk=pk).first()

    if not Project.objects.filter(permitted__username__contains=request.user.username):
        return render(request, '404_syn.html')
    
    totale_kosten = 0
    totale_kosten_lijst = [comment.kostenConsequenties for comment in PVEItemAnnotation.objects.filter(project=project) if comment.kostenConsequenties]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    gebruiker = PVEItemAnnotation.objects.filter(project=project).first()
    auteur = gebruiker.gebruiker
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(project=project).order_by('gebruiker')
    context["project"] = project
    context["totale_kosten"] = totale_kosten
    context["gebruiker"] = gebruiker
    context["aantal_opmerkingen_gedaan"] = PVEItemAnnotation.objects.filter(project=project).count()
    return render(request, 'AllCommentsOfProject_syn.html', context)

@login_required(login_url='login_syn')
def AddComment(request, pk):
    context = {}

    if not Project.objects.filter(id=pk):
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

    if request.user not in project.permitted.all():
        return render(request, '404_syn.html')

    # multiple forms
    if request.method == "POST":
        item_id_list = [number for number in request.POST.getlist("item_id")]
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(dict(item_id=item_id, annotation=opmrk, status=status, kostenConsequenties=kosten, annbijlage=annbijlage))
            for item_id, opmrk, status, kosten, annbijlage in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("kostenConsequenties"),
                request.FILES.getlist("annbijlage"),
            )
        ]

        # only use valid forms
        ann_forms = [ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()]

        for form in ann_forms:
            # true comment if either comment or voldoet
            if form.cleaned_data["annotation"] or form.cleaned_data["status"]:
                if PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()):
                    ann = PVEItemAnnotation.objects.filter(item=models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()).first()
                else:
                    ann = PVEItemAnnotation()
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(id=form.cleaned_data["item_id"]).first()
                ann.annotation = form.cleaned_data["annotation"]
                ann.status = form.cleaned_data["status"]
                ann.annbijlage = form.cleaned_data["annbijlage"]
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                ann.save()

        # remove duplicate entries
        return redirect('alleopmerkingen_syn', pk=project.id)

    if models.PVEItem.objects.filter(projects__id__contains=pk):
        items = models.PVEItem.objects.filter(projects__id__contains=pk).order_by('id')
        ann_forms = []
        bijlage_forms = []

        for item in items:
            if not PVEItemAnnotation.objects.filter(Q(project=project) & Q(gebruiker=request.user) & Q(item=item)):
                ann_forms.append(forms.PVEItemAnnotationForm(initial={'item_id':item.id}))
            else:
                opmerking = PVEItemAnnotation.objects.filter(Q(project=project) & Q(gebruiker=request.user) & Q(item=item)).first()
                ann_forms.append(forms.PVEItemAnnotationForm(initial={
                    'item_id':opmerking.item.id,
                    'annotation':opmerking.annotation,
                    'status':opmerking.status,
                    'kostenConsequenties':opmerking.kostenConsequenties,
                    }))


        hoofdstuk_ordered_items = {}

        for item in items:
            if item.paragraaf:
                if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                    	hoofdstuk_ordered_items[item.hoofdstuk] = {}

                if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk]:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(item)
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [item]
            else:
                if item.hoofdstuk in hoofdstuk_ordered_items:
                    hoofdstuk_ordered_items[item.hoofdstuk].append(item)
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [item]

        # easy entrance to item ids
        form_item_ids = [item.id for item in items]

        aantal_opmerkingen_gedaan = PVEItemAnnotation.objects.filter(Q(project=project) & Q(gebruiker=request.user)).count()

        if aantal_opmerkingen_gedaan < items.count():
            progress = "niet_klaar"
        else:
            progress = "klaar"

        context["forms"] = ann_forms
        context["items"] = items
        context["progress"] = progress
        context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
        context["form_item_ids"] = form_item_ids
        context["hoofdstuk_ordered_items"] = hoofdstuk_ordered_items

    context["project"] = project
    return render(request, 'plusOpmerking_syn.html', context)


@login_required(login_url='login_syn')
def AddProject(request):
    allowed_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    if request.method == "POST":
        form = forms.StartProjectForm(request.POST)

        if form.is_valid():
            form.save()

            project = Project.objects.all().order_by("-id")[0]
            project.permitted.add(request.user)
            project.belegger = Beleggers.objects.filter(naam="Syntrus").first()

            geolocator = Nominatim(user_agent="pvegenerator")
            if 'city' in geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address'].keys():
                project.plaatsnamen = geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address']['city']
            else:
                project.plaatsnamen = geolocator.reverse(f"{project.plaats.y}, {project.plaats.x}").raw['address']['town']

            project.save()
            return redirect('connectpve_syn', pk=project.id)

    context = {}
    context["form"] = StartProjectForm()
    return render(request, 'plusProject_syn.html', context)

@login_required(login_url='login_syn')
def ConnectPVE(request, pk):
    allowed_users = ["B", "SB", "SOG"]

    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

    project = Project.objects.filter(id=pk).first()

    if project.pveconnected:
        return render(request, '404_syn.html')

    if request.method == 'POST':
        form = forms.PVEParameterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # get parameters, find all pveitems with that
            (Bouwsoort1, TypeObject1, Doelgroep1, Bouwsoort2, TypeObject2, Doelgroep2, Bouwsoort3, TypeObject3, Doelgroep3, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort1"], form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"], form.cleaned_data["Bouwsoort2"], form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"], form.cleaned_data["Bouwsoort3"], form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )
            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(basisregel=True)
            basic_PVE = basic_PVE.union(models.PVEItem.objects.filter(Bouwsoort__parameter__contains=Bouwsoort1))
            project.bouwsoort1 = models.Bouwsoort.objects.filter(parameter=Bouwsoort1).first()

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Bouwsoort__parameter__contains=Bouwsoort2))
                project.bouwsoort2 = models.Bouwsoort.objects.filter(parameter=Bouwsoort2).first()

            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                   models.PVEItem.objects.filter(
                        Bouwsoort__parameter__contains=Bouwsoort3))
                project.bouwsoort2 = models.Bouwsoort.objects.filter(parameter=Bouwsoort3).first()

            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject1))
                project.typeObject1 = models.TypeObject.objects.filter(parameter=TypeObject1).first()

            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject2))
                project.typeObject2 = models.TypeObject.objects.filter(parameter=TypeObject2).first()

            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject3))
                project.typeObject2 = models.TypeObject.objects.filter(parameter=TypeObject3).first()

            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep1))
                project.doelgroep1 = models.Doelgroep.objects.filter(parameter=Doelgroep1).first()

            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep2))
                project.doelgroep2 = models.Doelgroep.objects.filter(parameter=Doelgroep2).first()
            
            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep3))
                project.doelgroep2 = models.Doelgroep.objects.filter(parameter=Doelgroep3).first()
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(AED=True)))
                project.AED = True

            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Smarthome=True)))
                # add the parameter to the project
                project.Smarthome = True

            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(EntreeUpgrade=True)))
                project.EntreeUpgrade = True

            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Pakketdient=True)))
                project.Pakketdient = True

            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(JamesConcept=True)))
                project.JamesConcept = True

            # add the project to all the pve items
            for item in basic_PVE:
                item.projects.add(project)

            # succesfully connected, save the project
            project.pveconnected = True
            project.save()
            return redirect('viewproject_syn', pk=project.id)

    # form
    form = forms.PVEParameterForm()

    context = {}
    context["form"] = form
    context["project"] = project
    return render(request, 'ConnectPVE_syn.html', context)


@login_required(login_url='login_syn')
def AddAccount(request):
    allowed_users = ["B", "SB", "SOG"]
    staff_users = ["B", "SB"]
    if request.user.type_user not in allowed_users:
        return render(request, '404_syn.html')

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
            invitation.project = form.cleaned_data["project"]
            invitation.user_functie = form.cleaned_data["user_functie"]
            invitation.user_afdeling = form.cleaned_data["user_afdeling"]
            
            # Als syntrus beheerder invitatie doet kan hij ook rang geven (projectmanager/derde)
            manager = False

            if request.user.type_user in staff_users:
                invitation.rang = form.cleaned_data["rang"]

                if form.cleaned_data["rang"] == 'SOG':
                    manager = True

            expiry_length = 10
            expire_date = timezone.now() + timezone.timedelta(expiry_length)
            invitation.expires = expire_date
            invitation.key = secrets.token_urlsafe(30)
            invitation.save()
            project = form.cleaned_data["project"]

            if manager:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {form.cleaned_data['project']}",
                    f"""{ request.user } heeft u uitgenodigd om projectmanager te zijn voor het project { form.cleaned_data['project'] } van Syntrus.
                    
                    Klik op de uitnodigingslink om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    'admin@pvegenerator.net',
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )
            else:
                send_mail(
                    f"Syntrus Projecten - Uitnodiging voor project {form.cleaned_data['project']}",
                    f"""{ request.user } nodigt u uit voor het commentaar leveren en het checken van het Programma van Eisen voor het project { form.cleaned_data['project'] } van Syntrus.
                    
                    Klik op de uitnodigingslink om rechtstreeks het project in te gaan.
                    Link: https://pvegenerator.net/syntrus/invite/{invitation.key}
                    
                    Deze link is 10 dagen geldig.""",
                    'admin@pvegenerator.net',
                    [f'{form.cleaned_data["invitee"]}'],
                    fail_silently=False,
                )

            messages.warning(request, f"Uitnodiging verstuurd naar { form.cleaned_data['invitee'] } voor project { form.cleaned_data['project'] }. De uitnodiging zal verlopen in { expiry_length } dagen.)")
            return redirect("viewproject_syn", pk=project.id)

    projecten = Project.objects.filter(permitted__username__contains=request.user.username)

    if request.user.type_user in staff_users:
        form = forms.PlusAccountForm()
    else:
        form = forms.KoppelDerdeUserForm()

    # set projects to own
    form.fields["project"].queryset = projecten
    context = {}
    context["form"] = form

    if request.user.type_user in staff_users:
        return render(request, 'plusAccount_syn.html', context)
    else:
        return render(request, 'plusDerde_syn.html', context)

def AcceptInvite(request, key):
    if not key or not Invitation.objects.filter(key=key):
        return render(request, '404_syn.html')
    
    invitation = Invitation.objects.filter(key=key).first()

    if utc.localize(datetime.datetime.now()) > invitation.expires:
        return render(request, '404verlopen_syn.html')

    if request.method == "POST":
        form = AcceptInvitationForm(request.POST)

        if form.is_valid():
            form.save()

            user = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password1"])
            user.email = invitation.invitee
            user.functie = invitation.user_functie
            user.afdeling = invitation.user_afdeling

            if invitation.rang:
                user.type_user = invitation.rang

            project = invitation.project
            project.permitted.add(user)

            if invitation.rang:
                if invitation.rang == "SOG":
                    project.projectmanager = user

            invitation.delete()
            project.save()
            user.save()
            if user is not None:
                login(request, user)
                return redirect('viewproject_syn', pk=project.id)

    form = AcceptInvitationForm()
    context = {}
    context["form"] = form
    context["key"] = key
    return render(request, 'acceptInvitation_syn.html', context)

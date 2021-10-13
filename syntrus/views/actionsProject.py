import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation
from syntrus import forms
from syntrus.models import BijlageToReply, CommentReply, FrozenComments
from utils import createBijlageZip, writePdf


@login_required(login_url="login_syn")
def ViewProjectOverview(request):
    projects = request.user.projectspermitted.all()

    medewerkers = [proj.permitted.all() for proj in projects]

    derden_toegevoegd = []
    for medewerker_list in medewerkers:
        derdes = False
        for medewerker in medewerker_list:
            if medewerker.type_user == "SD":
                derdes = True
        derden_toegevoegd.append(derdes)

        
    context = {}
    context["projects"] = projects
    context["derden_toegevoegd"] = derden_toegevoegd
    context["first_annotate"] = [project.first_annotate for project in projects]
    return render(request, "MyProjecten_syn.html", context)


@login_required(login_url="login_syn")
def ViewProject(request, pk):
    if not request.user.projectspermitted.filter(id=pk).exists():
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, id=pk)

    medewerkers = [medewerker.username for medewerker in project.permitted.all()]
    derden = [medewerker.username for medewerker in project.permitted.all() if medewerker.type_user == "SD"]
    
    context = {}

    if project.frozenLevel == 0:
        pve_item_count = project.item.count()
        comment_count = project.annotation.count()
        context["pve_item_count"] = pve_item_count
        context["comment_count"] = comment_count
        if project.pveconnected:
            context["done_percentage"] = int(100 * (comment_count) / pve_item_count)
        else:
            context["done_percentage"] = 0
        
        context["first_annotate"] = project.first_annotate

    if project.frozenLevel >= 1:
        frozencomments_accepted = project.phase.first().accepted_comments.count()
        frozencomments_todo = project.phase.first().todo_comments.count()
        frozencomments_total = frozencomments_todo + frozencomments_accepted + project.phase.first().comments.count()
        context["frozencomments_accepted"] = frozencomments_accepted
        context["frozencomments_todo"] = frozencomments_todo
        context["frozencomments_total"] = frozencomments_total
        context["frozencomments_percentage"] = int(
            100 * (frozencomments_accepted) / frozencomments_total
        )

        freeze_ready = False
        if frozencomments_total == frozencomments_accepted:
            freeze_ready = True

        context["freeze_ready"] = freeze_ready

    context["project"] = project
    context["medewerkers"] = medewerkers
    context["derden"] = derden
    return render(request, "ProjectPagina_syn.html", context)


@login_required(login_url="login_syn")
def ConnectPVE(request, pk):
    allowed_users = ["B", "SB", "SOG"]

    if request.user.type_user not in allowed_users:
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, pk=pk)

    # we get the active version of the pve based on what is active right now
    versie = models.ActieveVersie.objects.get(belegger__naam="Syntrus").versie

    if project.pveconnected:
        return render(request, "404_syn.html")

    if request.method == "POST":
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

            # add the project to all the pve items, quicken?
            for item in basic_PVE:
                item.projects.add(project)

            # succesfully connected, save the project
            project.pveconnected = True

            # set current pve version to project
            project.pve_versie = versie
            project.save()
            messages.warning(
                request, f"Parameters van het Programma van Eisen van project {project.naam} zijn toegevoegd. U kunt het PvE downloaden vanaf de projecthomepagina."
            )
            return redirect("projectenaddprojmanager_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
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

    context = {}
    context["form"] = form
    context["project"] = project
    context["versie"] = versie
    return render(request, "ConnectPVE_syn.html", context)


@login_required
def download_pve_overview(request):
    projects = Project.objects.filter(
        Q(permitted__username__iregex=r"\y{0}\y".format(request.user.username))
    ).distinct()

    context = {}
    context["projects"] = projects
    return render(request, "downloadPveOverview_syn.html", context)


@login_required
def download_pve(request, pk):
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, 
            permitted__username__iregex=r"\y{0}\y".format(request.user.username)
        ).exists():
            raise Http404("404")

    project = get_object_or_404(Project, id=pk)
    versie = project.pve_versie

    basic_PVE = (
        models.PVEItem.objects.select_related("hoofdstuk")
        .select_related("paragraaf")
        .filter(projects__id__contains=pk)
        .order_by("id")
    )

    # make pdf
    parameters = []

    parameters += (f"Project: {project.naam}",)

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

    # Opmerkingen in kleur naast de regels
    opmerkingen = {}
    bijlagen = {}
    reacties = {}
    reactiebijlagen = {}
    kostenverschil = 0

    comments = (
        PVEItemAnnotation.objects.select_related("item")
        .select_related("status")
        .select_related("gebruiker")
        .filter(project=project)
    )

    for opmerking in comments:
        opmerkingen[opmerking.item.id] = opmerking
        if opmerking.kostenConsequenties:
            kostenverschil += opmerking.kostenConsequenties
        if opmerking.bijlage:
            bijlage = BijlageToAnnotation.objects.get(ann=opmerking)
            bijlagen[opmerking.item.id] = bijlage

    replies = (
        CommentReply.objects.select_related("gebruiker")
        .select_related("onComment")
        .select_related("onComment__item")
        .filter(commentphase__project=project)
        .exclude(commentphase=project.phase.first())
        .order_by("datum")
    )

    for reply in replies:
        if reply.onComment.item.id in reacties.keys():
            reacties[reply.onComment.item.id].append(reply)
        else:
            reacties[reply.onComment.item.id] = [reply]

        if reply.bijlage:
            bijlage = BijlageToReply.objects.get(reply=reply)
            reactiebijlagen[reply.id] = bijlage

    geaccepteerde_regels_ids = []

    if project.frozenLevel > 0:
        commentphase = FrozenComments.objects.filter(
            project=project, level=project.frozenLevel
        ).first()
        geaccepteerde_regels_ids = [
            accepted_id.id for accepted_id in commentphase.accepted_comments.all()
        ]

    pdfmaker = writePdf.PDFMaker(versie.versie)

    # verander CONCEPT naar DEFINITIEF als het project volbevroren is.
    if project.fullyFrozen:
        pdfmaker.Topright = "DEFINITIEF"
    else:
        pdfmaker.Topright = f"CONCEPT SNAPSHOT {date.strftime('%d')}-{date.strftime('%m')}-{date.strftime('%Y')}"
        pdfmaker.TopRightPadding = 75

    pdfmaker.kostenverschil = kostenverschil
    pdfmaker.makepdf(
        filename,
        basic_PVE,
        versie.id,
        opmerkingen,
        bijlagen,
        reacties,
        reactiebijlagen,
        parameters,
        geaccepteerde_regels_ids,
    )

    # get bijlagen        
    bijlagen_models = models.ItemBijlages.objects.all()
    bijlagen = []

    for bijlage_model in bijlagen_models:
        for item in bijlage_model.items.all():
            if item in basic_PVE:
                bijlagen.append(bijlage_model)

    bijlagen = list(set(bijlagen))

    if BijlageToAnnotation.objects.filter(ann__project=project).exists():
        bijlagen_ann = BijlageToAnnotation.objects.filter(ann__project=project)
        for item in bijlagen_ann:
            bijlagen.append(item)

    if BijlageToReply.objects.filter(reply__onComment__project=project).exists():
        replybijlagen = BijlageToReply.objects.filter(reply__onComment__project=project)
        for bijlage in replybijlagen:
            bijlagen.append(bijlage)

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
    context["project"] = project
    return render(request, "PVEResult_syn.html", context)

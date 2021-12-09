import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation, Beleggers
from pvetool import forms
from pvetool.models import BijlageToReply, CommentReply, FrozenComments
from utils import createBijlageZip, writePdf
from pvetool.views.utils import GetAWSURL


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def ViewProjectOverview(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    projects = request.user.projectspermitted.filter(client__id=client_pk)

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
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyProjecten_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def ViewProject(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    if not request.user.projectspermitted.filter(id=pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, id=pk)

    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    medewerkers = [medewerker.username for medewerker in project.permitted.all()]
    derden = [
        medewerker.username
        for medewerker in project.permitted.all()
        if medewerker.type_user == "SD"
    ]

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
        frozencomments_total = (
            frozencomments_todo
            + frozencomments_accepted
            + project.phase.first().comments.count()
        )
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
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "ProjectPagina_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def KiesPVE(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    allowed_users = ["B", "SB", "SOG"]

    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)

    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    form = forms.PVEVersieKeuzeForm(request.POST or None)
    qs = models.PVEVersie.objects.filter(
        client=client, public=True
    )
    form.fields["pve_versie"].queryset = qs

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            return redirect(
                "connectpve_syn",
                client_pk=client_pk,
                pk=pk,
                version_pk=form.cleaned_data["pve_versie"].id,
            )

    context = {}
    context["form"] = form
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    context["pk"] = pk
    context["project"] = project
    context["qs"] = qs
    return render(request, "kiespve.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def ConnectPVE(request, client_pk, pk, version_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    allowed_users = ["B", "SB", "SOG"]

    if request.user.type_user not in allowed_users:
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)

    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    # we get the active version of the pve based on what is active right now
    version = models.PVEVersie.objects.filter(id=version_pk).first()

    if project.pveconnected:
        return redirect("logout_syn", client_pk=client_pk)

    if request.method == "POST":
        form = forms.PVEParameterForm(request.POST)

        bouwsoort = version.bouwsoort.all()
        form.fields["Bouwsoort1"].queryset = bouwsoort
        form.fields["Bouwsoort2"].queryset = bouwsoort
        form.fields["Bouwsoort3"].queryset = bouwsoort

        typeObject = version.typeobject.all()
        form.fields["TypeObject1"].queryset = typeObject
        form.fields["TypeObject2"].queryset = typeObject
        form.fields["TypeObject3"].queryset = typeObject

        doelgroep = version.doelgroep.all()
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
            basic_PVE = (
                version.item.select_related("paragraph")
                .select_related("chapter")
                .filter(basisregel=True)
            )
            
            print(basic_PVE)

            basic_PVE = basic_PVE.union(
                Bouwsoort1.item.select_related("chapter")
                .select_related("paragraph")
                .all()
            )
            
            project.bouwsoort1 = Bouwsoort1

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    Bouwsoort2.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.bouwsoort2 = Bouwsoort2
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    Bouwsoort3.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.bouwsoort3 = Bouwsoort3

            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    TypeObject1.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.typeObject1 = TypeObject1

            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    TypeObject2.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.typeObject2 = TypeObject2

            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    TypeObject3.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.typeObject3 = TypeObject3

            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    Doelgroep1.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.doelgroep1 = Doelgroep1

            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    Doelgroep2.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.doelgroep2 = Doelgroep2

            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    Doelgroep3.item.select_related("chapter")
                    .select_related("paragraph")
                    .all()
                )
                project.doelgroep3 = Doelgroep3


            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    version.item.select_related("paragraph")
                    .select_related("chapter")
                    .filter(AED=True)
                )
                project.AED = True
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    version.item.select_related("paragraph")
                    .select_related("chapter")
                    .filter(Smarthome=True)
                )
                project.Smarthome = True

            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    version.item.select_related("paragraph")
                    .select_related("chapter")
                    .filter(EntreeUpgrade=True)
                )
                project.EntreeUpgrade = True

            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    version.item.select_related("paragraph")
                    .select_related("chapter")
                    .filter(Pakketdient=True)
                )
                project.Pakketdient = True

            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    version.item.select_related("paragraph")
                    .select_related("chapter")
                    .filter(JamesConcept=True)
                )
                project.JamesConcept = True


            basic_PVE = basic_PVE.order_by("id")

            # add the project to all the pve items, quicken?
            project.item.add(*basic_PVE)

            # succesfully connected, save the project
            project.pveconnected = True

            # set current pve version to project
            project.pve_versie = version
            project.save()
            messages.warning(
                request,
                f"Parameters van het Programma van Eisen van project {project.name} zijn toegevoegd. U kunt het PvE downloaden vanaf de projecthomepagina.",
            )
            return redirect("manageprojecten_syn", client_pk=client_pk)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
    form = forms.PVEParameterForm()
    bouwsoort = version.bouwsoort.all()
    form.fields["Bouwsoort1"].queryset = bouwsoort
    form.fields["Bouwsoort2"].queryset = bouwsoort
    form.fields["Bouwsoort3"].queryset = bouwsoort

    typeObject = version.typeobject.all()
    form.fields["TypeObject1"].queryset = typeObject
    form.fields["TypeObject2"].queryset = typeObject
    form.fields["TypeObject3"].queryset = typeObject

    doelgroep = version.doelgroep.all()
    form.fields["Doelgroep1"].queryset = doelgroep
    form.fields["Doelgroep2"].queryset = doelgroep
    form.fields["Doelgroep3"].queryset = doelgroep

    context = {}
    context["form"] = form
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    context["version"] = version
    context["version_pk"] = version_pk
    return render(request, "ConnectPVE_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def download_pve_overview(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    projects = (
        client.project.all()
        .filter(Q(permitted__username__iregex=r"\y{0}\y".format(request.user.username)))
        .distinct()
    )

    context = {}
    context["projects"] = projects
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "downloadPveOverview_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def download_pve(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return redirect("logout_syn", client_pk=client_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__iregex=r"\y{0}\y".format(request.user.username)
        ).exists():
            raise Http404("404")

    project = get_object_or_404(Project, id=pk)
    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    version = project.pve_versie

    basic_PVE = (
        models.PVEItem.objects.select_related("chapter")
        .select_related("paragraph")
        .filter(projects__id__contains=pk)
        .order_by("id")
    )
    
    # make pdf
    parameters = []

    parameters += (f"Project: {project.name}",)

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
    attachments = {}
    reacties = {}
    reactieattachments = {}
    kostenverschil = 0

    comments = (
        PVEItemAnnotation.objects.select_related("item")
        .select_related("status")
        .select_related("user")
        .filter(project=project)
    )

    for opmerking in comments:
        opmerkingen[opmerking.item.id] = opmerking
        if opmerking.consequentCosts:
            kostenverschil += opmerking.consequentCosts
        if opmerking.attachment:
            attachmentsqs = BijlageToAnnotation.objects.filter(ann=opmerking)
            for attachment in attachmentsqs:
                if attachment.attachment:
                    if opmerking.item.id in attachments.keys():
                        attachments[opmerking.item.id].append(attachment)
                    else:
                        attachments[opmerking.item.id] = [attachment]
    print(attachments)
    replies = (
        CommentReply.objects.select_related("user")
        .select_related("onComment")
        .select_related("onComment__item")
        .filter(commentphase__project=project)
        .exclude(commentphase=project.phase.first())
        .order_by("date")
    )

    for reply in replies:
        if reply.onComment.item.id in reacties.keys():
            reacties[reply.onComment.item.id].append(reply)
        else:
            reacties[reply.onComment.item.id] = [reply]
        if reply.attachment:
            attachmentsqs = BijlageToReply.objects.filter(reply=reply)
            for attachment in attachmentsqs:
                if attachment.attachment:
                    if reply.id in reactieattachments.keys():
                        reactieattachments[reply.id].append(attachment)
                    else:
                        reactieattachments[reply.id] = [attachment]

    geaccepteerde_regels_ids = []

    if project.frozenLevel > 0:
        commentphase = FrozenComments.objects.filter(
            project=project, level=project.frozenLevel
        ).first()
        geaccepteerde_regels_ids = [
            accepted_id.id for accepted_id in commentphase.accepted_comments.all()
        ]

    pdfmaker = writePdf.PDFMaker(version.version, logo_url)

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
        version.id,
        opmerkingen,
        attachments,
        reacties,
        reactieattachments,
        parameters,
        geaccepteerde_regels_ids,
    )

    # get attachments
    attachments_models = models.ItemBijlages.objects.all()
    attachmentspve = []

    for attachment_model in attachments_models:
        for item in attachment_model.items.all():
            if item in basic_PVE:
                attachmentspve.append(attachment_model)

    attachmentspve = list(set(attachmentspve))

    if BijlageToAnnotation.objects.filter(ann__project=project).exists():
        attachments_ann = BijlageToAnnotation.objects.filter(ann__project=project)
        for item in attachments_ann:
            if item.attachment:
                attachmentspve.append(item)

    if BijlageToReply.objects.filter(reply__onComment__project=project).exists():
        replyattachments = BijlageToReply.objects.filter(reply__onComment__project=project)
        for attachment in replyattachments:
            if attachment.attachment:
                attachmentspve.append(attachment)

    if attachmentspve:
        zipmaker = createBijlageZip.ZipMaker()
        zipmaker.makeZip(zipFilename, filename, attachmentspve)
    else:
        zipFilename = False

    # and render the result page
    context = {}
    context["itemsPVE"] = basic_PVE
    context["filename"] = filename
    context["zipFilename"] = zipFilename
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url

    if request.htmx:
        return render(request, "partials/pveresult_project.html", context)
    else:
        return render(request, "PVEResult_syn.html", context)
        
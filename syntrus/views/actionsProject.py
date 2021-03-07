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
    projects = Project.objects.filter(
        belegger__naam="Syntrus", permitted__username__contains=request.user.username
    ).distinct()

    context = {}
    context["projects"] = projects
    return render(request, "MyProjecten_syn.html", context)


@login_required(login_url="login_syn")
def ViewProject(request, pk):
    if not Project.objects.filter(
        id=pk,
        belegger__naam="Syntrus",
        permitted__username__contains=request.user.username,
    ).exists():
        return render(request, "404_syn.html")

    project = get_object_or_404(Project, id=pk)

    medewerkers = [medewerker.username for medewerker in project.permitted.all()]

    context = {}

    if project.frozenLevel == 0:
        pve_item_count = models.PVEItem.objects.filter(
            projects__id__contains=pk
        ).count()
        comment_count = PVEItemAnnotation.objects.filter(project__id=pk).count()
        context["pve_item_count"] = pve_item_count
        context["comment_count"] = comment_count
        if project.pveconnected:
            context["done_percentage"] = int(100 * (comment_count) / pve_item_count)
        else:
            context["done_percentage"] = 0

    if project.frozenLevel >= 1:
        frozencomments_accepted = (
            FrozenComments.objects.filter(project__id=project.id)
            .order_by("-level")
            .first()
            .accepted_comments.count()
        )
        frozencomments_todo = (
            FrozenComments.objects.filter(project__id=project.id)
            .order_by("-level")
            .first()
            .todo_comments.count()
        )
        frozencomments_total = (
            frozencomments_todo
            + frozencomments_accepted
            + FrozenComments.objects.filter(Q(project__id=project.id))
            .order_by("-level")
            .first()
            .comments.count()
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

        # check whether it's valid:
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
            basic_PVE = models.PVEItem.objects.prefetch_related("projects").filter(
                Q(versie=versie) & Q(basisregel=True)
            )
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.prefetch_related("projects").filter(
                    versie=versie, Bouwsoort__parameter__contains=Bouwsoort1
                )
            )
            project.bouwsoort1 = models.Bouwsoort.objects.filter(
                versie=versie, parameter=Bouwsoort1
            ).first()

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, Bouwsoort__parameter__contains=Bouwsoort2
                    )
                )
                project.bouwsoort2 = models.Bouwsoort.objects.filter(
                    versie=versie, parameter=Bouwsoort2
                ).first()

            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, Bouwsoort__parameter__contains=Bouwsoort3
                    )
                )
                project.bouwsoort2 = models.Bouwsoort.objects.filter(
                    versie=versie, parameter=Bouwsoort3
                ).first()

            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, TypeObject__parameter__contains=TypeObject1
                    )
                )
                project.typeObject1 = models.TypeObject.objects.filter(
                    versie=versie, parameter=TypeObject1
                ).first()

            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, TypeObject__parameter__contains=TypeObject2
                    )
                )
                project.typeObject2 = models.TypeObject.objects.filter(
                    versie=versie, parameter=TypeObject2
                ).first()

            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, TypeObject__parameter__contains=TypeObject3
                    )
                )
                project.typeObject2 = models.TypeObject.objects.filter(
                    versie=versie, parameter=TypeObject3
                ).first()

            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, Doelgroep__parameter__contains=Doelgroep1
                    )
                )
                project.doelgroep1 = models.Doelgroep.objects.filter(
                    versie=versie, parameter=Doelgroep1
                ).first()

            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, Doelgroep__parameter__contains=Doelgroep2
                    )
                )
                project.doelgroep2 = models.Doelgroep.objects.filter(
                    versie=versie, parameter=Doelgroep2
                ).first()

            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        versie=versie, Doelgroep__parameter__contains=Doelgroep3
                    )
                )
                project.doelgroep2 = models.Doelgroep.objects.filter(
                    versie=versie, parameter=Doelgroep3
                ).first()
            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        Q(versie=versie) & Q(AED=True)
                    )
                )
                project.AED = True

            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        Q(versie=versie) & Q(Smarthome=True)
                    )
                )
                # add the parameter to the project
                project.Smarthome = True

            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        Q(versie=versie) & Q(EntreeUpgrade=True)
                    )
                )
                project.EntreeUpgrade = True

            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        Q(versie=versie) & Q(Pakketdient=True)
                    )
                )
                project.Pakketdient = True

            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.prefetch_related("projects").filter(
                        Q(versie=versie) & Q(JamesConcept=True)
                    )
                )
                project.JamesConcept = True

            # add the project to all the pve items
            for item in basic_PVE:
                item.projects.add(project)

            # succesfully connected, save the project
            project.pveconnected = True

            # set current pve version to project
            project.pve_versie = versie
            project.save()
            return redirect("projectenaddprojmanager_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    # form
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

    context = {}
    context["form"] = form
    context["project"] = project
    context["versie"] = versie
    return render(request, "ConnectPVE_syn.html", context)


@login_required
def download_pve_overview(request):
    projects = Project.objects.filter(
        permitted__username__contains=request.user.username
    ).distinct()

    context = {}
    context["projects"] = projects
    return render(request, "downloadPveOverview_syn.html", context)


@login_required
def download_pve(request, pk):
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
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

    pdfmaker = writePdf.PDFMaker()

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
    bijlagen = [item for item in basic_PVE if item.bijlage]

    if BijlageToAnnotation.objects.filter(ann__project=project).exists():
        bijlagen = BijlageToAnnotation.objects.filter(ann__project=project)
        for item in bijlagen:
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

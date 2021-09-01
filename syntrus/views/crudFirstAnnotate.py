from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation
from syntrus import forms
from syntrus.forms import BijlageToAnnotationForm
from syntrus.models import CommentStatus

@login_required(login_url="login_syn")
def AddCommentOverview(request):
    context = {}

    if Project.objects.filter(permitted__username__contains=request.user).exists():
        projects = Project.objects.filter(permitted__username__contains=request.user)
        context["projects"] = projects

    return render(request, "plusOpmerkingOverview_syn.html", context)


@login_required(login_url="login_syn")
def MyComments(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user.type_user != project.first_annotate:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")
        # multiple forms
    if request.method == "POST":
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(
                dict(
                    item_id=item_id,
                    annotation=opmrk,
                    status=status,
                    init_accepted=init_accepted,
                    kostenConsequenties=kosten,
                )
            )
            for item_id, opmrk, status, init_accepted, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("init_accepted"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        changed = False
        for form in ann_forms:
            # true comment if either comment or voldoet
            if form.cleaned_data["status"] or form.cleaned_data["init_accepted"]:
                ann = PVEItemAnnotation.objects.filter(
                    item=models.PVEItem.objects.filter(
                        id=form.cleaned_data["item_id"]
                    ).first()
                ).first()
                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(
                    id=form.cleaned_data["item_id"]
                ).first()
                if form.cleaned_data["annotation"]:
                    ann.annotation = form.cleaned_data["annotation"]
                if form.cleaned_data["status"]:
                    ann.status = form.cleaned_data["status"]
                # bijlage uit cleaned data halen en opslaan!
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                ann.save()
                changed = True

        if changed:
            bericht = "Statussen toegevoegd aan een of meerdere regels. U kunt altijd terug naar de status aanwijzing pagina om het aan te passen voordat u de lijst opstuurt naar de andere partij."
        else:
            bericht = "Geen nieuwe statussen toegevoegd / regels geaccepteerd. U kunt altijd terug naar de status aanwijzing pagina om statussen aan te wijzen aan regels."

        messages.warning(
            request, bericht
        )

        return redirect("mijnopmerkingen_syn", pk=project.id)

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    comments = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("-datum")

    for comment in comments:
        form = forms.PVEItemAnnotationForm(
            initial={
                "item_id": comment.item.id,
                "annotation": comment.annotation,
                "status": comment.status,
                "init_accepted": comment.init_accepted,
                "kostenConsequenties": comment.kostenConsequenties,
            }
        )

        ann_forms.append(form)

        form_item_ids.append(comment.item.id)

    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = comments
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).count()
    return render(request, "MyComments.html", context)


@login_required(login_url="login_syn")
def MyCommentsDelete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    aantal_opmerkingen_gedaan = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).count()

    context = {}
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    return render(request, "MyCommentsDelete.html", context)


@login_required(login_url="login_syn")
def deleteAnnotationPve(request, project_id, ann_id):
    # check if project exists
    project = get_object_or_404(Project, id=project_id)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=project_id, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(id=ann_id, gebruiker=request.user).exists():
        raise Http404("404")

    comment = PVEItemAnnotation.objects.filter(id=ann_id).first()

    if request.method == "POST":
        comment.delete()
        messages.warning(
            request, f"Opmerking verwijderd."
        )
        return HttpResponseRedirect(
            reverse("mijnopmerkingendelete_syn", args=(project.id,))
        )

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["comment"] = comment
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten

    return render(request, "deleteAnnotationModal_syn.html", context)


@login_required(login_url="login_syn")
def AddAnnotationAttachment(request, projid, annid):
    project = get_object_or_404(Project, pk=projid)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    annotation = PVEItemAnnotation.objects.filter(project=project, pk=annid).first()
    comments = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")

    if annotation.gebruiker != request.user:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.BijlageToAnnotationForm(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["bijlage"]:
                form.save()
                annotation.bijlage = True
                annotation.save()
                messages.warning(
                    request, f"Bijlage toegevoegd."
                )
                return redirect("mijnopmerkingen_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    form = BijlageToAnnotationForm(initial={"ann": annotation})
    context["annotation"] = annotation
    context["form"] = form
    context["project"] = project
    context["comments"] = comments
    return render(request, "addBijlagetoAnnotation_syn.html", context)


@login_required(login_url="login_syn")
def VerwijderAnnotationAttachment(request, projid, annid):
    # check if project exists
    project = get_object_or_404(Project, pk=projid)
    
    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=projid, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(id=annid, gebruiker=request.user).exists():
        raise Http404("404")

    comment = PVEItemAnnotation.objects.filter(id=annid).first()
    attachment = BijlageToAnnotation.objects.filter(ann_id=annid).first()

    if request.method == "POST":
        messages.warning(request, f"Bijlage van {attachment.ann} verwijderd.")
        comment.bijlage = False
        comment.save()
        attachment.delete()
        return HttpResponseRedirect(
            reverse("mijnopmerkingendelete_syn", args=(project.id,))
        )

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project, ann__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["comment"] = comment
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["comments"] = PVEItemAnnotation.objects.filter(
        project=project, gebruiker=request.user
    ).order_by("id")
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten

    return render(request, "deleteAttachmentAnnotation_syn.html", context)


@login_required(login_url="login_syn")
def AllComments(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in PVEItemAnnotation.objects.filter(project=project)
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    if PVEItemAnnotation.objects.filter(project=project):
        gebruiker = PVEItemAnnotation.objects.filter(project=project).first()
        context["gebruiker"] = gebruiker
        context["comments"] = PVEItemAnnotation.objects.filter(
            project=project
        ).order_by("-datum")

    context["items"] = models.PVEItem.objects.filter(
        projects__id__contains=project.id
    ).order_by("id")
    context["project"] = project
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = PVEItemAnnotation.objects.filter(
        project=project
    ).count()
    return render(request, "AllCommentsOfProject_syn.html", context)


@login_required(login_url="login_syn")
def AddComment(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if request.user.type_user != project.first_annotate:
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if not models.PVEItem.objects.filter(projects__id__contains=pk).exists():
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # multiple forms
    if request.method == "POST":
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.PVEItemAnnotationForm(
                dict(
                    item_id=item_id,
                    annotation=opmrk,
                    status=status,
                    kostenConsequenties=kosten,
                )
            )
            for item_id, opmrk, status, kosten in zip(
                request.POST.getlist("item_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        for form in ann_forms:
            # true comment if either status or voldoet
            if form.cleaned_data["status"]:
                if PVEItemAnnotation.objects.filter(
                    Q(
                        item=models.PVEItem.objects.filter(
                            id=form.cleaned_data["item_id"]
                        ).first()
                    )
                    & Q(project=project)
                    & Q(gebruiker=request.user)
                ).exists():
                    ann = PVEItemAnnotation.objects.filter(
                        Q(
                            item=models.PVEItem.objects.filter(
                                id=form.cleaned_data["item_id"]
                            ).first()
                        )
                        & Q(project=project)
                        & Q(gebruiker=request.user)
                    ).first()
                else:
                    ann = PVEItemAnnotation()

                ann.project = project
                ann.gebruiker = request.user
                ann.item = models.PVEItem.objects.filter(
                    id=form.cleaned_data["item_id"]
                ).first()

                if form.cleaned_data["annotation"]:
                    ann.annotation = form.cleaned_data["annotation"]
                if form.cleaned_data["status"]:
                    ann.status = form.cleaned_data["status"]
                # bijlage uit cleaned data halen en opslaan!
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                ann.save()
        messages.warning(
            request,
            "Opmerkingen opgeslagen. U kunt later altijd terug naar deze pagina of naar de opmerkingpagina om uw opmerkingen te bewerken voordat u ze opstuurt.",
        )
        # remove duplicate entries
        return redirect("mijnopmerkingen_syn", pk=project.id)

    items = (
        models.PVEItem.objects.select_related("hoofdstuk")
        .select_related("paragraaf")
        .filter(projects__id__contains=pk)
        .order_by("id")
    )
    annotations = {}

    for annotation in (
        PVEItemAnnotation.objects.select_related("item")
        .select_related("status")
        .filter(Q(project=project) & Q(gebruiker=request.user))
    ):
        annotations[annotation.item] = annotation

    ann_forms = []
    hoofdstuk_ordered_items = {}

    itembijlages = [_ for _ in models.ItemBijlages.objects.prefetch_related("items").filter(versie=project.pve_versie)]
    items_has_bijlages = [item.items.all() for item in itembijlages]

    for item in items:
        opmerking = None
        
        bijlage = None

        if item in items_has_bijlages:
            bijlage = models.ItemBijlages.objects.get(items__id__contains=item.id)

        # create forms
        if item not in annotations.keys():
            form = forms.PVEItemAnnotationForm(initial={"item_id": item.id})
        else:
            opmerking = annotations[item]
            form = forms.PVEItemAnnotationForm(
                    initial={
                        "item_id": opmerking.item.id,
                        "annotation": opmerking.annotation,
                        "status": opmerking.status,
                        "kostenConsequenties": opmerking.kostenConsequenties,
                    }
                )
        
        # create ordered items
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                hoofdstuk_ordered_items[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk].keys():
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(
                        [item, item.id, opmerking.status, bijlage, form]
                    )
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(
                        [item, item.id, None, bijlage, form]
                    )
            else:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [
                        [item, item.id, opmerking.status, bijlage, form]
                    ]
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [
                        [item, item.id, None, bijlage, form]
                    ]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items.keys():
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk].append(
                        [item, item.id, opmerking.status, bijlage, form]
                    )
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk].append(
                        [item, item.id, None, bijlage, form]
                    )
            else:
                if opmerking:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [
                        [item, item.id, opmerking.status, bijlage, form]
                    ]
                else:
                    hoofdstuk_ordered_items[item.hoofdstuk] = [
                        [item, item.id, None, bijlage, form]
                    ]

    # easy entrance to item ids
    form_item_ids = [item.id for item in items]

    aantal_opmerkingen_gedaan = len(annotations.keys())

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
    return render(request, "plusOpmerking_syn.html", context)

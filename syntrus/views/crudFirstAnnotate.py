from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation, Beleggers
from syntrus import forms
from syntrus.forms import BijlageToAnnotationForm
from syntrus.models import CommentStatus
from syntrus.views.utils import GetAWSURL

from django.core.paginator import Paginator
import asyncio

@login_required(login_url="login_syn")
def AddCommentOverview(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    context = {}

    if request.user.projectspermitted.all().filter(belegger__id=client_pk).exists():
        projects = request.user.projectspermitted.all().filter(belegger__id=client_pk)
        context["projects"] = projects

    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusOpmerkingOverview_syn.html", context)


@login_required(login_url="login_syn")
def MyComments(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    context = {}

    project = get_object_or_404(Project, pk=pk)

    if project.belegger != client:
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user.type_user != project.first_annotate:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

        
    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in project.annotation.all()
        if comment.kostenConsequenties
    ]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    comments = project.annotation.prefetch_related("status").select_related("item").all()

    paginator = Paginator(comments, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    item_id_post = None
    if request.method == "POST":
        item_id_post = request.POST.getlist("item_id")
        annotation_post = request.POST.getlist("annotation")
        status_post = request.POST.getlist("status")
        kostenConsequenties_post = request.POST.getlist("kostenConsequenties")
        print(item_id_post, annotation_post, status_post, kostenConsequenties_post)

    i = 0
    for comment in page_obj:
        form = forms.PVEItemAnnotationForm(
            dict(
                item_id=item_id_post[i],
                annotation=annotation_post[i],
                status=status_post[i],
                kostenConsequenties=kostenConsequenties_post[i],
            ) if item_id_post else None, 
            initial={
                "item_id": comment.item.id,
                "annotation": comment.annotation,
                "status": comment.status,
                "kostenConsequenties": comment.kostenConsequenties,
            }
        )

        ann_forms.append(form)

        form_item_ids.append(comment.item.id)
        i += 1

        # multiple forms
    if request.method == "POST":

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        changed = False
        for form in ann_forms:
            # true comment if either comment or voldoet
            if form.has_changed():
                if form.changed_data != ['status'] or (form.cleaned_data['status'] and form.fields['status'].initial != form.cleaned_data['status'].id):
                    item = models.PVEItem.objects.get(id=form.cleaned_data["item_id"])

                    ann = item.annotation.first()
                    ann.project = project
                    ann.gebruiker = request.user
                    ann.item = item
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

        return redirect("mijnopmerkingen_syn", client_pk=client_pk, pk=project.id)

    context["page_obj"] = page_obj
    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = project.item.all()
    context["comments"] = comments
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = project.annotation.count()
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyComments.html", context)


@login_required(login_url="login_syn")
def MyCommentsDelete(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != client:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in project.annotation.all()
        if comment.kostenConsequenties
    ]
    totale_kosten = sum(totale_kosten_lijst)

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    aantal_opmerkingen_gedaan = project.annotation.count()

    comments = project.annotation.all()

    paginator = Paginator(comments, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {}
    context["page_obj"] = page_obj
    context["items"] = project.item.all()
    context["comments"] = comments
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyCommentsDelete.html", context)


@login_required(login_url="login_syn")
def deleteAnnotationPve(request, client_pk, project_id, ann_id):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    # check if project exists
    project = get_object_or_404(Project, id=project_id)
    if project.belegger != client:
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not request.user.projectspermitted.filter(id=project_id).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(id=ann_id).exists():
        raise Http404("404")

    comment = PVEItemAnnotation.objects.get(id=ann_id)

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
        for comment in project.annotation.all()
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    comments = project.annotation.all()
    
    paginator = Paginator(comments, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {}
    context["page_obj"] = page_obj
    context["comment"] = comment
    context["items"] = project.item.all()
    context["comments"] = project.annotation.all()
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url

    return render(request, "deleteAnnotationModal_syn.html", context)


@login_required(login_url="login_syn")
def AddAnnotationAttachment(request, client_pk, projid, annid):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    project = get_object_or_404(Project, pk=projid)

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    comments = project.annotation.all()
    annotation = comments.get(pk=annid)

    paginator = Paginator(comments, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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
                return redirect("mijnopmerkingen_syn", client_pk=client_pk, pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    form = BijlageToAnnotationForm(initial={"ann": annotation})
    context["annotation"] = annotation
    context["form"] = form
    context["project"] = project
    context["comments"] = comments
    context["page_obj"] = page_obj
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "addBijlagetoAnnotation_syn.html", context)


@login_required(login_url="login_syn")
def VerwijderAnnotationAttachment(request, client_pk, projid, annid):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    # check if project exists
    project = get_object_or_404(Project, pk=projid)
    
    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not request.user.projectspermitted.filter(id=projid).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not PVEItemAnnotation.objects.filter(id=annid).exists():
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
        for comment in project.annotation.all()
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    bijlages = []

    for bijlage in BijlageToAnnotation.objects.filter(
        ann__project=project
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    comments = project.annotation.all()

    paginator = Paginator(comments, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {}
    context["comment"] = comment
    context["items"] = project.item.all()
    context["project"] = project
    context["bijlages"] = bijlages
    context["totale_kosten"] = totale_kosten
    context["page_obj"] = page_obj
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "deleteAttachmentAnnotation_syn.html", context)


@login_required(login_url="login_syn")
def AllComments(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    context = {}

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != client:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    totale_kosten = 0
    totale_kosten_lijst = [
        comment.kostenConsequenties
        for comment in project.annotation.all()
        if comment.kostenConsequenties
    ]
    for kosten in totale_kosten_lijst:
        totale_kosten += kosten

    if project.annotation.exists():
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
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "AllCommentsOfProject_syn.html", context)


@login_required(login_url="login_syn")
def AddComment(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return render(request, "404_syn.html")

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = GetAWSURL(client)

    context = {}

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != client:
        return render(request, "404_syn.html")

    if request.user.type_user != project.first_annotate:
        return render(request, "404_syn.html")

    if project.frozenLevel > 0:
        return render(request, "404_syn.html")

    if not project.item.exists():
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    items = project.item.select_related("hoofdstuk").select_related("paragraaf").all()

    annotations = {}

    for annotation in project.annotation.select_related("item").select_related("status"):
        annotations[annotation.item] = annotation

    ann_forms = []
    hoofdstuk_ordered_items = {}

    itembijlages = [_ for _ in project.pve_versie.itembijlage.prefetch_related("items")]
    items_has_bijlages = [item.items.all() for item in itembijlages]

    item_id_post = None

    if request.method == "POST":
        item_id_post = request.POST.getlist("item_id")
        annotation_post = request.POST.getlist("annotation")
        status_post = request.POST.getlist("status")
        kostenConsequenties_post = request.POST.getlist("kostenConsequenties")

    i = 0
    for item in items:
        opmerking = None
        bijlage = None

        if item in items_has_bijlages:
            bijlage = item.itembijlage.first()

        # create forms
        if item not in annotations.keys():
            form = forms.PVEItemAnnotationForm(
                dict(
                    item_id=item_id_post[i],
                    annotation=annotation_post[i],
                    status=status_post[i],
                    kostenConsequenties=kostenConsequenties_post[i],
                ) if item_id_post else None, 
                initial={"item_id": item.id}
            )
            if item_id_post:
                print(item_id_post[i], annotation_post[i], status_post[i], kostenConsequenties_post[i])
        else:
            opmerking = annotations[item]
            form = forms.PVEItemAnnotationForm(
                    dict(
                        item_id=item_id_post[i],
                        annotation=annotation_post[i],
                        status=status_post[i],
                        kostenConsequenties=kostenConsequenties_post[i],
                    ) if item_id_post else None,
                    initial={
                        "item_id": opmerking.item.id,
                        "annotation": opmerking.annotation,
                        "status": opmerking.status,
                        "kostenConsequenties": opmerking.kostenConsequenties,
                    }
                )
            if item_id_post:
                print(f"already made: {item_id_post[i], annotation_post[i], status_post[i], kostenConsequenties_post[i]}")

        ann_forms.append(form)

        i += 1

        total_context = [item, None, bijlage, form]

        if opmerking:
            total_context = [item, opmerking, bijlage, form]

        # create ordered items
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                hoofdstuk_ordered_items[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk].keys():
                hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(
                    total_context
                )
            else:
                hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [
                    total_context
                ]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items.keys():
                hoofdstuk_ordered_items[item.hoofdstuk].append(
                    total_context
                )
            else:
                hoofdstuk_ordered_items[item.hoofdstuk] = [
                    total_context
                ]

    # easy entrance to item ids
    form_item_ids = [item.id for item in items]

    aantal_opmerkingen_gedaan = len(annotations.keys())

    if aantal_opmerkingen_gedaan < items.count():
        progress = "niet_klaar"
    else:
        progress = "klaar"

    # multiple forms
    if request.method == "POST":
        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        for form in ann_forms:
            if form.has_changed():
                print(form.changed_data)
                if (form.cleaned_data["status"] and form.fields['status'].initial != form.cleaned_data['status'].id) and (form.changed_data != ['item_id']):
                    item = models.PVEItem.objects.get(id=form.cleaned_data["item_id"])

                    if project.annotation.filter(item=item).exists():
                        ann = project.annotation.filter(item=item).first()
                    else:
                        ann = PVEItemAnnotation()

                    ann.project = project
                    ann.gebruiker = request.user
                    ann.item = item


                    if form.cleaned_data["annotation"]:
                        ann.annotation = form.cleaned_data["annotation"]
                    if form.cleaned_data["status"] and form.fields['status'].initial != form.cleaned_data['status'].id:
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
        return redirect("mijnopmerkingen_syn", client_pk=client_pk, pk=project.id)

    context["forms"] = ann_forms
    context["items"] = items
    context["progress"] = progress
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    context["form_item_ids"] = form_item_ids
    context["hoofdstuk_ordered_items"] = hoofdstuk_ordered_items
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusOpmerking_syn.html", context)

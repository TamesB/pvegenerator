from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation, Beleggers
from syntrus import forms
from syntrus.forms import BijlageToAnnotationForm, FirstBijlageForm, FirstAnnotationForm, FirstStatusForm, FirstKostenverschilForm
from syntrus.models import CommentStatus
from syntrus.views.utils import GetAWSURL

from django.core.paginator import Paginator
import asyncio

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddCommentOverview(request, client_pk):
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

    if request.user.projectspermitted.all().filter(belegger__id=client_pk).exists():
        projects = request.user.projectspermitted.all().filter(belegger__id=client_pk)
        context["projects"] = projects

    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusOpmerkingOverview_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def MyComments(request, client_pk, pk):
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

    project = get_object_or_404(Project, pk=pk)

    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

        
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


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def MyCommentsDelete(request, client_pk, pk):
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

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

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


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def deleteAnnotationPve(request, client_pk, project_id, ann_id):
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

    # check if project exists
    project = get_object_or_404(Project, id=project_id)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

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


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddAnnotationAttachment(request, client_pk, projid, annid):
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

    project = get_object_or_404(Project, pk=projid)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    comments = project.annotation.all()
    annotation = comments.get(pk=annid)

    paginator = Paginator(comments, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if annotation.gebruiker != request.user:
        return redirect("logout_syn", client_pk=client_pk)

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


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def VerwijderAnnotationAttachment(request, client_pk, projid, annid):
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

    # check if project exists
    project = get_object_or_404(Project, pk=projid)
    
    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

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


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AllComments(request, client_pk, pk):
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

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

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

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddComment(request, client_pk, pk):
    context = {}

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


    project = get_object_or_404(Project, pk=pk)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    items = project.item.select_related("hoofdstuk").select_related("paragraaf").all()
    hoofdstukken = {}

    for item in items:
        if item.hoofdstuk not in hoofdstukken:
            if item.paragraaf:
                hoofdstukken[item.hoofdstuk] = True
            else:
                hoofdstukken[item.hoofdstuk] = False

    annotations = {}

    for annotation in project.annotation.select_related("item").select_related("status"):
        annotations[annotation.item] = annotation

    aantal_opmerkingen_gedaan = len(annotations.keys())

    if aantal_opmerkingen_gedaan < items.count():
        progress = "niet_klaar"
    else:
        progress = "klaar"

    context["items"] = items
    context["progress"] = progress
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    context["hoofdstukken"] = hoofdstukken
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusOpmerking_syn.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def GetParagravenFirstAnnotate(request, client_pk, pk, hoofdstuk_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    items = project.item.select_related("hoofdstuk").select_related("paragraaf").filter(hoofdstuk__id=hoofdstuk_pk).all()
    paragraven = []

    for item in items:
        if item.paragraaf not in paragraven:
            paragraven.append(item.paragraaf)

    context["items"] = items
    context["paragraven"] = paragraven
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/paragravenpartial.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def GetItemsFirstAnnotate(request, client_pk, pk, hoofdstuk_pk, paragraaf_id):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    if paragraaf_id == 0:
        pve_items = project.item.select_related("hoofdstuk").select_related("paragraaf").filter(hoofdstuk__id=hoofdstuk_pk).all()
    else:
        pve_items = project.item.select_related("hoofdstuk").select_related("paragraaf").filter(hoofdstuk__id=hoofdstuk_pk, paragraaf__id=paragraaf_id).all()

    annotations = {}

    for annotation in project.annotation.select_related("item").select_related("status"):
        annotations[annotation.item] = annotation

    itembijlages = [_ for _ in project.pve_versie.itembijlage.prefetch_related("items")]
    items_has_bijlages = [item.items.all() for item in itembijlages]


    items = []

    for item in pve_items:
        bijlage = None

        if item in items_has_bijlages:
            bijlage = item.itembijlage.first()
        
        items.append([item, bijlage])

    context["items"] = items
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/itempartial.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailStatusFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    return render(request, "partials/detail_status_first.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailAnnotationFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    bijlage = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()
        if annotation.bijlageobject.exists():
            bijlage = annotation.bijlageobject.first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["bijlage"] = bijlage
    return render(request, "partials/detail_annotation_first.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailKostenverschilFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    return render(request, "partials/detail_kostenverschil_first.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddBijlageFirst(request, client_pk, project_pk, item_pk, annotation_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)
    annotation = PVEItemAnnotation.objects.filter(id=annotation_pk).first()

    bijlagemodel = None
    if BijlageToAnnotation.objects.filter(ann__id=annotation_pk).exists():
        bijlagemodel = BijlageToAnnotation.objects.filter(ann__id=annotation_pk).first()
        form = FirstBijlageForm(request.POST or None, request.FILES or None, instance=bijlagemodel)
    else:
        form = FirstBijlageForm(request.POST or None, request.FILES or None, initial={'ann': annotation})

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            form.save()
            messages.warning(request, "Bijlage toegevoegd!")
            return redirect("detailfirstannotation", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk)

        messages.warning(request, "Fout met bijlage toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["annotation_pk"] = annotation_pk
    context["item_pk"] = item_pk
    context["form"] = form
    context["annotation"] = annotation
    return render(request, "partials/form_bijlage_first.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddStatusFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()
        form = FirstStatusForm(request.POST or None, initial={'status': annotation.status})
    else:
        form = FirstStatusForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                annotation.status = form.cleaned_data['status']
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.status = form.cleaned_data['status']
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.gebruiker = request.user
                annotation.save()

            messages.warning(request, "Status toegevoegd!")
            return redirect("detailfirststatus", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["form"] = form
    return render(request, "partials/form_status_first.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddKostenverschilFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()
        form = FirstKostenverschilForm(request.POST or None, initial={'kostenverschil': annotation.kostenConsequenties})
    else:
        form = FirstKostenverschilForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                annotation.kostenConsequenties = form.cleaned_data['kostenverschil']
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.kostenConsequenties = form.cleaned_data['kostenverschil']
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.gebruiker = request.user
                annotation.save()

            messages.warning(request, "Kostenverschil toegevoegd!")
            return redirect("detailfirstkostenverschil", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["form"] = form
    return render(request, "partials/form_kostenverschil_first.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddAnnotationFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()
        form = FirstAnnotationForm(request.POST or None, initial={'annotation': annotation.annotation})
    else:
        form = FirstAnnotationForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                annotation.annotation = form.cleaned_data['annotation']
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.annotation = form.cleaned_data['annotation']
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.gebruiker = request.user
                annotation.save()

            messages.warning(request, "Opmerking toegevoegd!")
            return redirect("detailfirstannotation", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk)

    context["form"] = form
    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    return render(request, "partials/form_annotation_first.html", context)

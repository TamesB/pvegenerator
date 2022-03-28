from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation, Client
from pvetool.forms import (
    FirstBijlageForm,
    FirstAnnotationForm,
    FirstStatusForm,
    FirstKostenverschilForm,
)
from pvetool.views.utils import GetAWSURL
from pvetool.views import hardcoded_values
from pvetool.models import CommentRequirement

# the URL map for whether a chapter has paragraphs or not
has_paragraphs = {
    False: 0
}

# further maps from URLsafe values to boolean values
exists = {
    True: 1,
    False: 0
}

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddCommentOverview(request, client_pk):
    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Client.objects.filter(pk=client_pk).first()
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

    context = {}

    if request.user.projectspermitted.all().filter(client__id=client_pk).exists():
        projects = request.user.projectspermitted.all().filter(client__id=client_pk)
        context["projects"] = projects

    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusOpmerkingOverview_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddComment(request, client_pk, pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Client.objects.filter(pk=client_pk).first()
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

    project = get_object_or_404(Project, pk=pk)
    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        if request.user == project.projectmanager:
            return redirect("kiespveversie", client_pk=client_pk, pk=pk)
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    items = project.item.select_related("chapter").select_related("paragraph").all().order_by("id")
    chapters_false = {}
    chapters = {}

    for item in items:
        if item.chapter not in chapters_false:
            if item.paragraph:
                chapters_false[item.chapter] = True
            else:
                chapters_false[item.chapter] = False
            
    chapters_ordered = models.PVEHoofdstuk.objects.filter(version__pk=items.first().version.pk).order_by("id")
               
    for chapter in chapters_ordered:
        if chapter in chapters_false.keys():
            chapters[chapter] = chapters_false[chapter]
    
    annotations = {}
    annotations_hfst = {chapter.id: 0 for chapter in chapters}
    items_per_chapter = {chapter.id: 0 for chapter in chapters}
    
    for chapter in chapters.keys():
        items_per_chapter_count = project.item.select_related("chapter").filter(chapter=chapter).count()
        items_per_chapter[chapter.id] += items_per_chapter_count
    
    
    for annotation in project.annotation.select_related("item").select_related("item__chapter").select_related(
        "status"
    ):
        annotations[annotation.item] = annotation
        annotations_hfst[annotation.item.chapter.id] += 1

    aantal_opmerkingen_gedaan = len(annotations.keys())

    if aantal_opmerkingen_gedaan < items.count():
        progress = "niet_klaar"
    else:
        progress = "klaar"

    context["items"] = items
    context["progress"] = progress
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    context["chapters"] = chapters
    context["items_per_chapter"] = items_per_chapter
    context["annotations_hfst"] = annotations_hfst
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "plusOpmerking_syn.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetParagravenFirstAnnotate(request, client_pk, pk, chapter_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)
    
    chapter = models.PVEHoofdstuk.objects.filter(pk=chapter_pk).first()

    items = (
        project.item.select_related("chapter")
        .select_related("paragraph")
        .filter(chapter=chapter)
        .all()
        .order_by("id")
    )
    
    paragraphs_ids_false = {}
    paragraph_ids = {}
    for item in items:
        if item.paragraph:
            if item.paragraph.id not in paragraphs_ids_false.keys():
                paragraphs_ids_false[item.paragraph.id] = item.paragraph
    
    paragraphs_ordered = models.PVEParagraaf.objects.filter(version__pk=items.first().version.pk).order_by("id")
    
    for paragraph in paragraphs_ordered:
        if paragraph.id in paragraphs_ids_false.keys():
            paragraph_ids[paragraph.id] = paragraphs_ids_false[paragraph.id]
    
    paragraphs = [paragraph for _, paragraph in paragraph_ids.items()]
    
    context["paragraphs"] = paragraphs
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/paragraphspartial.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetItemsFirstAnnotate(request, client_pk, pk, chapter_pk, paragraph_id):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    if paragraph_id == has_paragraphs[False]:
        pve_items = (
            project.item.select_related("chapter")
            .select_related("paragraph")
            .filter(chapter__id=chapter_pk)
            .all()
            .order_by("id")
        )
    else:
        pve_items = (
            project.item.select_related("chapter")
            .select_related("paragraph")
            .filter(chapter__id=chapter_pk, paragraph__id=paragraph_id)
            .all()
            .order_by("id")
        )
        
    context["items"] = pve_items
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/itempartial.html", context)

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailItemFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    if models.PVEItem.objects.filter(pk=item_pk):
        item = models.PVEItem.objects.get(pk=item_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)
    
    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
    
    attachments = []
        
    for attachment in item.itemAttachment.all():
        attachments.append(attachment)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["item"] = item
    context["attachments"] = attachments
    return render(request, "partials/detail_item_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailStatusFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    return render(request, "partials/detail_status_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailAnnotationFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    attachments = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        if annotation.attachmentobject.exists():
            attachments = annotation.attachmentobject.all()
            
    context["comment_allowed"] = False
    context["attachment_allowed"] = False
    
    # manual input as to what statuses allow comments / attachments    
    if annotation:
        if annotation.status:
            requirement_obj = CommentRequirement.objects.get(version__pk=project.pve_versie.pk)
            comment_allowed = [obj.status for obj in requirement_obj.comment_allowed.all()]
            attachment_allowed = [obj.status for obj in requirement_obj.attachment_allowed.all()]

            if annotation.status.status in comment_allowed:
                context["comment_allowed"] = True
            if annotation.status.status in attachment_allowed:
                context["attachment_allowed"] = True

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["attachments"] = attachments
    return render(request, "partials/detail_annotation_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailKostenverschilFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    context["cost_allowed"] = False

    if annotation:
        if annotation.status:
            requirement_obj = CommentRequirement.objects.get(version__pk=project.pve_versie.pk)
            costs_allowed = [obj.status for obj in requirement_obj.costs_allowed.all()]

            if annotation.status.status in costs_allowed:
                context["cost_allowed"] = True

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    return render(request, "partials/detail_kostenverschil_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddBijlageFirst(request, client_pk, project_pk, item_pk, annotation_pk, attachment_id):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)
    
    if annotation_pk != 0:
        annotation = PVEItemAnnotation.objects.filter(id=annotation_pk).first()
    else:
        annotation = PVEItemAnnotation.objects.create(project=project, item=models.PVEItem.objects.get(id=item_pk), user=request.user)
        annotation_pk = annotation.id

    attachmentmodel = None
    if attachment_id != 0 and annotation_pk != 0 and BijlageToAnnotation.objects.filter(id=attachment_id, ann__id=annotation_pk).exists():
        attachmentmodel = BijlageToAnnotation.objects.filter(id=attachment_id, ann__id=annotation_pk).first()
        form = FirstBijlageForm(
            request.POST or None, request.FILES or None, instance=attachmentmodel
        )
    else:
        form = FirstBijlageForm(
            request.POST or None, request.FILES or None, initial={"ann": annotation}
        )

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if form.cleaned_data["name"]: 
                if not BijlageToAnnotation.objects.filter(name=form.cleaned_data["name"], ann__project=project).exists(): 
                    form.save()
                    annotation.attachment = True
                    annotation.save()
                    messages.warning(request, "Bijlage toegevoegd!")
                    return redirect(
                        "detailfirstannotation",
                        client_pk=client_pk,
                        project_pk=project_pk,
                        item_pk=item_pk,
                    )
                else:
                    messages.warning(request, "Naam bestaat al voor een attachment in dit project. Kies een andere.")
            else:
                # else save and the attachment ID is the attachment name.
                form.save()
                annotation.attachment = True
                annotation.save()
                attachment = annotation.attachmentobject.all().order_by("-id").first()
                attachment.name = attachment.id
                attachment.save()
                messages.warning(request, "Bijlage toegevoegd!")
                return redirect(
                    "detailfirstannotation",
                    client_pk=client_pk,
                    project_pk=project_pk,
                    item_pk=item_pk,
                )

        else:
            messages.warning(request, "Fout met attachment toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["attachment_id"] = attachment_id
    context["annotation_pk"] = annotation_pk
    context["item_pk"] = item_pk
    context["form"] = form
    context["annotation"] = annotation
    return render(request, "partials/form_attachment_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddStatusFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        form = FirstStatusForm(
            request.POST or None, initial={"status": annotation.status}
        )
    else:
        form = FirstStatusForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                requirement_obj = CommentRequirement.objects.get(version__pk=project.pve_versie.pk)
                comment_allowed = [obj.status for obj in requirement_obj.comment_allowed.all()]
                attachment_allowed = [obj.status for obj in requirement_obj.attachment_allowed.all()]
                
                if form.cleaned_data["status"] not in comment_allowed:
                    annotation.annotation = None
                if form.cleaned_data["status"] not in attachment_allowed:
                    annotation.attachment = False

                annotation.status = form.cleaned_data["status"]
                annotation.firststatus = form.cleaned_data["status"]
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.status = form.cleaned_data["status"]
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.user = request.user
                annotation.firststatus = form.cleaned_data["status"]
                annotation.save()

            messages.warning(request, "Status toegevoegd!")
            return redirect(
                "detailitemfirst",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
            )

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["form"] = form
    return render(request, "partials/form_status_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddKostenverschilFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        form = FirstKostenverschilForm(
            request.POST or None,
            initial={"kostenverschil": annotation.consequentCosts},
        )
    else:
        form = FirstKostenverschilForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                annotation.consequentCosts = form.cleaned_data["kostenverschil"]
                annotation.costtype = form.cleaned_data["costtype"]
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.consequentCosts = form.cleaned_data["kostenverschil"]
                annotation.costtype = form.cleaned_data["costtype"]
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.user = request.user
                annotation.save()

            messages.warning(request, "Kostenverschil toegevoegd!")
            return redirect(
                "detailfirstkostenverschil",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
            )

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["form"] = form
    return render(request, "partials/form_kostenverschil_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddAnnotationFirst(request, client_pk, project_pk, item_pk):
    context = {}

    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        form = FirstAnnotationForm(
            request.POST or None, initial={"annotation": annotation.annotation}
        )
    else:
        form = FirstAnnotationForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                annotation.annotation = form.cleaned_data["annotation"]
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.annotation = form.cleaned_data["annotation"]
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.user = request.user
                annotation.save()

            messages.warning(request, "Opmerking toegevoegd!")
            return redirect(
                "detailfirstannotation",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
            )

    context["form"] = form
    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    return render(request, "partials/form_annotation_first.html", context)

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteKostenverschilFirst(request, client_pk, project_pk, item_pk):
    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    if annotation:
        annotation.consequentCosts = None
        annotation.costtype = None
        annotation.save()
        messages.warning(request, "Kostenverschil verwijderd.")
        return redirect(
            "detailfirstkostenverschil",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
        )

    messages.warning(request, "Fout met kostenverschil verwijderen. Probeer het nog eens.")
    return redirect(
        "detailfirstkostenverschil",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
    )

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteAnnotationFirst(request, client_pk, project_pk, item_pk):
    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    if annotation:
        annotation.annotation = None
        annotation.save()

        if annotation.attachmentobject.exists():
            attachment = annotation.attachmentobject.first()
            attachment.delete()
            
        messages.warning(request, "Aanvulling verwijderd. Als u een attachment heb toegevoegd, is deze ook verwijderd.")
        return redirect(
            "detailfirstannotation",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
        )

    messages.warning(request, "Fout met aanvulling verwijderen. Probeer het nog eens.")
    return redirect(
        "detailfirstannotation",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
    )

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteStatusFirst(request, client_pk, project_pk, item_pk):
    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    attachments = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
    if BijlageToAnnotation.objects.filter(ann=annotation):
        attachments = BijlageToAnnotation.objects.filter(ann=annotation)
        
    if annotation:
        annotation.delete()
        if attachments:
            for attachment in attachments:
                attachment.delete()
            
        messages.warning(request, "Status verwijderd.")
        return redirect(
            "detailitemfirst",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
        )

    messages.warning(request, "Fout met status verwijderen. Probeer het nog eens.")
    return redirect(
        "detailitemfirst",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
    )

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteBijlageFirst(request, client_pk, project_pk, annotation_pk, pk):
    if not Client.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.client != Client.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if request.user.type_user != project.first_annotate:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel > 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    attachment = None
    if BijlageToAnnotation.objects.filter(id=pk).exists():
        attachment = BijlageToAnnotation.objects.filter(
            id=pk
        ).first()
    
    annotation = None
    if PVEItemAnnotation.objects.filter(
            id=annotation_pk
        ).exists():
        annotation = PVEItemAnnotation.objects.get(
            id=annotation_pk
        )

    if attachment:
        attachment.delete()
        if annotation:
            if not BijlageToAnnotation.objects.filter(ann=annotation).exists():
                annotation.attachment = False
                annotation.save()
                
        messages.warning(request, "Bijlage verwijderd.")
        return redirect(
            "detailfirstannotation",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=annotation.item.id,
        )

    messages.warning(request, "Fout met attachment verwijderen. Probeer het nog eens.")
    return redirect(
        "detailfirstannotation",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=annotation.item.id,
    )

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from app import models
from project.models import BijlageToAnnotation, Project, PVEItemAnnotation, Beleggers
from pvetool.forms import (
    FirstBijlageForm,
    FirstAnnotationForm,
    FirstStatusForm,
    FirstKostenverschilForm,
)
from pvetool.views.utils import GetAWSURL


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddCommentOverview(request, client_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.klantenorganisatie:
        if (
            request.user.klantenorganisatie.id != client.id
            and request.user.type_user != "B"
        ):
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


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddComment(request, client_pk, pk):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    if request.user.klantenorganisatie:
        if (
            request.user.klantenorganisatie.id != client.id
            and request.user.type_user != "B"
        ):
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

    for annotation in project.annotation.select_related("item").select_related(
        "status"
    ):
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


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
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

    items = (
        project.item.select_related("hoofdstuk")
        .select_related("paragraaf")
        .filter(hoofdstuk__id=hoofdstuk_pk)
        .all()
    )
    paragraven = []

    for item in items:
        if item.paragraaf not in paragraven:
            paragraven.append(item.paragraaf)

    context["items"] = items
    context["paragraven"] = paragraven
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/paragravenpartial.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
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
        pve_items = (
            project.item.select_related("hoofdstuk")
            .select_related("paragraaf")
            .filter(hoofdstuk__id=hoofdstuk_pk)
            .all()
        )
    else:
        pve_items = (
            project.item.select_related("hoofdstuk")
            .select_related("paragraaf")
            .filter(hoofdstuk__id=hoofdstuk_pk, paragraaf__id=paragraaf_id)
            .all()
        )

    annotations = {}

    for annotation in project.annotation.select_related("item").select_related(
        "status"
    ):
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


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
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
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        if annotation.bijlageobject.exists():
            bijlage = annotation.bijlageobject.first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["bijlage"] = bijlage
    return render(request, "partials/detail_annotation_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
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
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    return render(request, "partials/detail_kostenverschil_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
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
        form = FirstBijlageForm(
            request.POST or None, request.FILES or None, instance=bijlagemodel
        )
    else:
        form = FirstBijlageForm(
            request.POST or None, request.FILES or None, initial={"ann": annotation}
        )

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            form.save()
            messages.warning(request, "Bijlage toegevoegd!")
            return redirect(
                "detailfirstannotation",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
            )

        messages.warning(request, "Fout met bijlage toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["annotation_pk"] = annotation_pk
    context["item_pk"] = item_pk
    context["form"] = form
    context["annotation"] = annotation
    return render(request, "partials/form_bijlage_first.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
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
                annotation.status = form.cleaned_data["status"]
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.status = form.cleaned_data["status"]
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.gebruiker = request.user
                annotation.save()

            messages.warning(request, "Status toegevoegd!")
            return redirect(
                "detailfirststatus",
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
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        form = FirstKostenverschilForm(
            request.POST or None,
            initial={"kostenverschil": annotation.kostenConsequenties},
        )
    else:
        form = FirstKostenverschilForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if annotation:
                annotation.kostenConsequenties = form.cleaned_data["kostenverschil"]
                annotation.save()
            else:
                annotation = PVEItemAnnotation()
                annotation.kostenConsequenties = form.cleaned_data["kostenverschil"]
                annotation.project = project
                annotation.item = models.PVEItem.objects.get(id=item_pk)
                annotation.gebruiker = request.user
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
                annotation.gebruiker = request.user
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
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    if annotation:
        annotation.kostenConsequenties = None
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
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    if annotation:
        annotation.annotation = None
        annotation.save()

        if annotation.bijlageobject.exists():
            bijlage = annotation.bijlageobject.first()
            bijlage.delete()
            
        messages.warning(request, "Aanvulling verwijderd. Als u een bijlage heb toegevoegd, is deze ook verwijderd.")
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
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    if annotation:
        annotation.status = None
        annotation.save()
        messages.warning(request, "Status verwijderd.")
        return redirect(
            "detailfirststatus",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
        )

    messages.warning(request, "Fout met status verwijderen. Probeer het nog eens.")
    return redirect(
        "detailfirststatus",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
    )

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
    annotations_hfst = {}

    for annotation in project.annotation.select_related("item").select_related("item__hoofdstuk").select_related(
        "status"
    ):
        annotations[annotation.item] = annotation

        if annotation.item.hoofdstuk.id in annotations_hfst.keys():
            annotations_hfst[annotation.item.hoofdstuk.id] += 1
        else:
            annotations_hfst[annotation.item.hoofdstuk.id] = 1

    aantal_opmerkingen_gedaan = len(annotations.keys())

    if aantal_opmerkingen_gedaan < items.count():
        progress = "niet_klaar"
    else:
        progress = "klaar"

    context["items"] = items
    context["progress"] = progress
    context["aantal_opmerkingen_gedaan"] = aantal_opmerkingen_gedaan
    context["hoofdstukken"] = hoofdstukken
    context["annotations_hfst"] = annotations_hfst
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
    
    hoofdstuk = models.PVEHoofdstuk.objects.filter(pk=hoofdstuk_pk).first()

    items = (
        project.item.select_related("hoofdstuk")
        .select_related("paragraaf")
        .filter(hoofdstuk=hoofdstuk)
        .all()
    )
    
    paragraven_ids = {}
    
    for item in items:
        if item.paragraaf:
            if item.paragraaf.id not in paragraven_ids.keys():
                paragraven_ids[item.paragraaf.id] = item.paragraaf
        
    paragraven = [paragraaf for _, paragraaf in paragraven_ids.items()]
    
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
        
    context["items"] = pve_items
    context["project"] = project
    context["client_pk"] = client_pk
    return render(request, "partials/itempartial.html", context)

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailItemFirst(request, client_pk, project_pk, item_pk):
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

    if models.PVEItem.objects.filter(pk=item_pk):
        item = models.PVEItem.objects.get(pk=item_pk)
    else:
        return redirect("logout_syn", client_pk=client_pk)
    
    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
    
    bijlages = []
        
    for bijlage in item.itembijlage.all():
        bijlages.append(bijlage)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["item"] = item
    context["bijlages"] = bijlages
    return render(request, "partials/detail_item_first.html", context)


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
    bijlagen = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        if annotation.bijlageobject.exists():
            bijlagen = annotation.bijlageobject.all()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["bijlagen"] = bijlagen
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
def AddBijlageFirst(request, client_pk, project_pk, item_pk, annotation_pk, bijlage_id):
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
    
    if annotation_pk != 0:
        annotation = PVEItemAnnotation.objects.filter(id=annotation_pk).first()
    else:
        annotation = PVEItemAnnotation.objects.create(project=project, item=models.PVEItem.objects.get(id=item_pk), gebruiker=request.user)
        annotation_pk = annotation.id

    bijlagemodel = None
    if bijlage_id != 0 and annotation_pk != 0 and BijlageToAnnotation.objects.filter(id=bijlage_id, ann__id=annotation_pk).exists():
        bijlagemodel = BijlageToAnnotation.objects.filter(id=bijlage_id, ann__id=annotation_pk).first()
        form = FirstBijlageForm(
            request.POST or None, request.FILES or None, instance=bijlagemodel
        )
    else:
        form = FirstBijlageForm(
            request.POST or None, request.FILES or None, initial={"ann": annotation}
        )

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if not BijlageToAnnotation.objects.filter(naam=form.cleaned_data["naam"]).exists(): 
                form.save()
                annotation.bijlage=True
                annotation.save()
                messages.warning(request, "Bijlage toegevoegd!")
                return redirect(
                    "detailfirstannotation",
                    client_pk=client_pk,
                    project_pk=project_pk,
                    item_pk=item_pk,
                )
            else:
                messages.warning(request, "Naam bestaat al voor een bijlage in dit project. Kies een andere.")
        else:
            messages.warning(request, "Fout met bijlage toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["bijlage_id"] = bijlage_id
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

    bijlage = None
    if BijlageToAnnotation.objects.filter(id=pk).exists():
        bijlage = BijlageToAnnotation.objects.filter(
            id=pk
        ).first()
    
    annotation = None
    if PVEItemAnnotation.objects.filter(
            id=annotation_pk
        ).exists():
        annotation = PVEItemAnnotation.objects.get(
            id=annotation_pk
        )
        
    if bijlage:
        bijlage.delete()
        if annotation:
            if not BijlageToAnnotation.objects.filter(ann=annotation).exists():
                annotation.bijlage = False
                annotation.save()
                
        messages.warning(request, "Bijlage verwijderd.")
        return redirect(
            "detailfirstannotation",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=annotation_pk,
        )

    messages.warning(request, "Fout met bijlage verwijderen. Probeer het nog eens.")
    return redirect(
        "detailfirstannotation",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=annotation_pk,
    )

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from app import models
from project.models import Project, PVEItemAnnotation, Beleggers
from pvetool import forms
from pvetool.models import BijlageToReply, CommentReply, FrozenComments
from pvetool.views.utils import GetAWSURL

# this function checks if the client exists, whether the user is authenticated to the client, project is of the client,
# the project is not in first annotate stage, the project contains a pve,
# whether the user is permitted to the project,
# and the current phase allows the usertype to see the page.
def passed_commentcheck_guardclauses(request, client_pk, project_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return False, False

    client = Beleggers.objects.filter(pk=client_pk).first()

    if request.user.klantenorganisatie:
        if (
            request.user.klantenorganisatie.id != client.id
            and request.user.type_user != "B"
        ):
            return False, False
    else:
        return False, False

    if not Project.objects.filter(pk=project_pk).exists():
        return False, False

    project = Project.objects.get(pk=project_pk)

    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return False, False

    if request.user not in project.permitted.all():
        return False, False

    if project.frozenLevel == 0:
        return False, False

    if not project.item.exists():
        return False, False

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return False, False
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return False, False

    return project, current_phase


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def CheckComments(request, client_pk, proj_id):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, proj_id
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    non_accepted_comments = (
        current_phase.comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )

    accepted_comments = (
        current_phase.accepted_comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )

    todo_comments = (
        current_phase.todo_comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )

    hoofdstukken_non_accept = make_hoofdstukken(non_accepted_comments)
    hoofdstukken_accept = make_hoofdstukken(accepted_comments)
    hoofdstukken_todo = make_hoofdstukken(todo_comments)

    non_accepted_hfst_replies = {}
    accepted_hfst_replies = {}
    todo_hfst_replies = {}

    non_accepted_replies = current_phase.reply.select_related("onComment__item__hoofdstuk").filter(onComment__in=non_accepted_comments)
    accepted_replies = current_phase.reply.select_related("onComment__item__hoofdstuk").filter(onComment__in=accepted_comments)
    todo_replies = current_phase.reply.select_related("onComment__item__hoofdstuk").filter(onComment__in=todo_comments)

    for reply in non_accepted_replies:
        hoofdstuk = reply.onComment.item.hoofdstuk.id
        if hoofdstuk in non_accepted_hfst_replies:
            non_accepted_hfst_replies[hoofdstuk] += 1
        else:
            non_accepted_hfst_replies[hoofdstuk] = 1
            
    for reply in accepted_replies:
        hoofdstuk = reply.onComment.item.hoofdstuk.id
        if hoofdstuk in accepted_hfst_replies:
            accepted_hfst_replies[hoofdstuk] += 1
        else:
            accepted_hfst_replies[hoofdstuk] = 1
            
    for reply in todo_replies:
        hoofdstuk = reply.onComment.item.hoofdstuk.id
        if hoofdstuk in todo_hfst_replies:
            todo_hfst_replies[hoofdstuk] += 1
        else:
            todo_hfst_replies[hoofdstuk] = 1

    context["hoofdstukken_non_accept"] = hoofdstukken_non_accept
    context["hoofdstukken_accept"] = hoofdstukken_accept
    context["hoofdstukken_todo"] = hoofdstukken_todo
    context["non_accepted_hfst_replies"] = non_accepted_hfst_replies
    context["accepted_hfst_replies"] = accepted_hfst_replies
    context["todo_hfst_replies"] = todo_hfst_replies
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["commentphase"] = current_phase
    context["last_level"] = current_phase.level - 1
    context["logo_url"] = logo_url
    context["totale_kosten"] = PVEItemAnnotation.objects.filter(
        project=project
    ).aggregate(Sum("kostenConsequenties"))["kostenConsequenties__sum"]

    return render(request, "CheckComments_temp.html", context)


def make_hoofdstukken(comments):
    hoofdstuk_ordered_items = {}

    for comment in comments:
        item = comment.item
        if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
            if item.paragraaf:
                hoofdstuk_ordered_items[item.hoofdstuk] = True
            else:
                hoofdstuk_ordered_items[item.hoofdstuk] = False

    return hoofdstuk_ordered_items


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetParagravenPingPong(request, client_pk, pk, hoofdstuk_pk, type, accept):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(request, client_pk, pk)

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    comments = None

    if type == 1:
        comments = (
            current_phase.comments.select_related("status")
            .select_related("item")
            .select_related("item__hoofdstuk")
            .select_related("item__paragraaf")
            .filter(item__hoofdstuk__id=hoofdstuk_pk)
            .order_by("item__id")
            .all()
        )
    if type == 2:
        comments = (
            current_phase.accepted_comments.select_related("status")
            .select_related("item")
            .select_related("item__hoofdstuk")
            .select_related("item__paragraaf")
            .filter(item__hoofdstuk__id=hoofdstuk_pk)
            .order_by("item__id")
            .all()
        )
    if type == 0:
        comments = (
            current_phase.todo_comments.select_related("status")
            .select_related("item")
            .select_related("item__hoofdstuk")
            .select_related("item__paragraaf")
            .filter(item__hoofdstuk__id=hoofdstuk_pk)
            .order_by("item__id")
            .all()
        )

    items = [comment.item for comment in comments]

    paragraven = []
    paragraven_ids = []

    for item in items:
        if item.paragraaf.id not in paragraven_ids:
            paragraven.appends(item.paragraaf)
            paragraven_ids.append(item.paragraaf.id)
    
    context["comments"] = comments
    context["items"] = items
    context["type"] = type
    context["paragraven"] = paragraven
    context["project"] = project
    context["client_pk"] = client_pk
    context["accept"] = accept
    return render(request, "partials/paragravenpartialpong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetItemsPingPong(request, client_pk, pk, hoofdstuk_pk, paragraaf_id, type, accept):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(request, client_pk, pk)

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    comments = None

    if type == 1:
        if paragraaf_id == 0:
            comments = (
                current_phase.comments.select_related("status")
                .select_related("item")
                .select_related("item__hoofdstuk")
                .select_related("item__paragraaf")
                .filter(item__hoofdstuk__id=hoofdstuk_pk)
                .order_by("item__id")
                .all()
            )
        else:
            comments = (
                current_phase.comments.select_related("status")
                .select_related("item")
                .select_related("item__hoofdstuk")
                .select_related("item__paragraaf")
                .filter(item__hoofdstuk__id=hoofdstuk_pk)
                .filter(item__paragraaf__id=paragraaf_id)
                .order_by("item__id")
                .all()
            )
    if type == 2:
        if paragraaf_id == 0:
            comments = (
                current_phase.accepted_comments.select_related("status")
                .select_related("item")
                .select_related("item__hoofdstuk")
                .select_related("item__paragraaf")
                .filter(item__hoofdstuk__id=hoofdstuk_pk)
                .order_by("item__id")
                .all()
            )
        else:
            comments = (
                current_phase.accepted_comments.select_related("status")
                .select_related("item")
                .select_related("item__hoofdstuk")
                .select_related("item__paragraaf")
                .filter(item__hoofdstuk__id=hoofdstuk_pk)
                .filter(item__paragraaf__id=paragraaf_id)
                .order_by("item__id")
                .all()
            )
    if type == 0:
        if paragraaf_id == 0:
            comments = (
                current_phase.todo_comments.select_related("status")
                .select_related("item")
                .select_related("item__hoofdstuk")
                .select_related("item__paragraaf")
                .filter(item__hoofdstuk__id=hoofdstuk_pk)
                .order_by("item__id")
                .all()
            )
        else:
            comments = (
                current_phase.todo_comments.select_related("status")
                .select_related("item")
                .select_related("item__hoofdstuk")
                .select_related("item__paragraaf")
                .filter(item__hoofdstuk__id=hoofdstuk_pk)
                .filter(item__paragraaf__id=paragraaf_id)
                .order_by("item__id")
                .all()
            )

    items = [comment.item for comment in comments]

    context["items"] = items
    context["project"] = project
    context["client_pk"] = client_pk
    context["type"] = type
    context["accept"] = accept
    return render(request, "partials/itempartialpong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    item = project.item.filter(id=item_pk).first()

    itembijlage = None
    if models.ItemBijlages.objects.filter(items__id=item.id).exists():
        itembijlage = models.ItemBijlages.objects.filter(items__id=item.id).first()

    replies = None
    bijlagen = {}

    if CommentReply.objects.filter(onComment__item__id=item.id, commentphase__project__id=current_phase.project.id).exists():
        replies = CommentReply.objects.filter(
            Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)
        ).order_by("id")

        for reply in replies:
            if reply.bijlagetoreply.exists():
                bijlagen[reply] = reply.bijlagetoreply.all()
                

    annotation = None
    if PVEItemAnnotation.objects.filter(
        project__id=project_pk, item__id=item.id
    ).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project__id=project_pk, item__id=item.id
        ).first()

        annotationbijlagen = None
        if annotation.bijlageobject.exists():
            annotationbijlagen = annotation.bijlageobject.all()

    context["item"] = item
    context["itembijlage"] = itembijlage
    context["replies"] = replies
    context["bijlagen"] = bijlagen
    context["annotation"] = annotation
    context["annotationbijlagen"] = annotationbijlagen
    context["client_pk"] = client_pk
    context["type"] = type
    context["project_pk"] = project_pk
    return render(request, "partials/getitempartial.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailStatusPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    # find last changed status
    status_reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, commentphase__project__id=current_phase.project.id).exists():
        replies = CommentReply.objects.filter(
            Q(onComment__id=annotation.id) & ~Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)
        ).order_by("id")

        for reply in replies:
            if reply.status:
                status_reply = reply

    current_reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id, commentphase=current_phase
    ).exists():
        current_reply = CommentReply.objects.filter(
            onComment__id=annotation.id, commentphase=current_phase
        ).first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["current_reply"] = current_reply
    context["status_reply"] = status_reply
    context["type"] = type
    return render(request, "partials/detail_status_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailReplyPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    reply = None
    bijlagen = None

    if CommentReply.objects.filter(
        commentphase=current_phase, onComment__item__id=item_pk
    ).exists():
        reply = CommentReply.objects.filter(
            commentphase=current_phase, onComment__item__id=item_pk
        ).first()

        if reply.bijlagetoreply.exists():
            bijlagen = reply.bijlagetoreply.all()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["reply"] = reply
    context["current_reply"] = reply
    context["bijlagen"] = bijlagen
    context["type"] = type
    return render(request, "partials/detail_annotation_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailKostenverschilPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    current_reply = None
    if CommentReply.objects.filter(
        commentphase=current_phase, onComment__id=annotation.id
    ).exists():
        current_reply = CommentReply.objects.filter(
            commentphase=current_phase, onComment__id=annotation.id
        ).first()

    # find last changed status
    last_reply = None
    if CommentReply.objects.filter(onComment__item__id=item_pk, commentphase__project__id=current_phase.project.id).exists():
        replies = CommentReply.objects.filter(
            Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)
        ).order_by("id")

        for reply in replies:
            if reply.status:
                last_reply = reply

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["current_reply"] = current_reply
    context["last_reply"] = last_reply
    context["type"] = type
    return render(request, "partials/detail_kostenverschil_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailAcceptPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    current_reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id, commentphase=current_phase
    ).exists():
        current_reply = CommentReply.objects.get(
            onComment__id=annotation.id, commentphase=current_phase
        )

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["current_reply"] = current_reply
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AcceptItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    current_reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id, commentphase=current_phase
    ).exists():
        current_reply = CommentReply.objects.get(
            onComment__id=annotation.id, commentphase=current_phase
        )
        current_reply.accept = True

        # remove all comments/statuschange/costs/attachment of the current person who accepted the rule
        # they have accepted the previous comments/statuses after all
        if current_reply.comment:
            current_reply.comment = None

        if current_reply.bijlage:
            current_reply.bijlage = None
            bijlageobject = current_reply.bijlagetoreply.first()
            bijlageobject.delete()
        if current_reply.kostenConsequenties:
            current_reply.kostenConsequenties = None
        if current_reply.status:
            current_reply.status = None

        current_reply.save()
    else:
        current_reply = CommentReply.objects.create(
            commentphase=current_phase,
            gebruiker=request.user,
            onComment=annotation,
            accept=True,
        )
        current_reply.save()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["current_reply"] = current_reply
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def NonAcceptItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    current_reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id, commentphase=current_phase
    ).exists():
        current_reply = CommentReply.objects.get(
            onComment__id=annotation.id, commentphase=current_phase
        )
        current_reply.accept = False
        current_reply.save()
    else:
        current_reply = CommentReply.objects.create(
            commentphase=current_phase,
            gebruiker=request.user,
            onComment=annotation,
            accept=False,
        )
        current_reply.save()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["current_reply"] = current_reply
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddBijlagePong(request, client_pk, project_pk, item_pk, annotation_pk, type, new, bijlage_id):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()
        
    # create reply only once with GET/POST request
    if annotation_pk == 0 and not CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ):
        reply = CommentReply.objects.create(commentphase=current_phase, onComment=annotation, gebruiker=request.user)
        bijlage_id = reply.id
    else:
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
    
    # seperate forms because we want to create a reply only once (GET)
    if BijlageToReply.objects.filter(id=bijlage_id).exists() and new == 0 and bijlage_id != 0:
        bijlagemodel = BijlageToReply.objects.filter(id=bijlage_id).first()
        form = forms.PongBijlageForm(
            request.POST or None, request.FILES or None, instance=bijlagemodel
        )
    else:
        form = forms.PongBijlageForm(
            request.POST or None, request.FILES or None, initial={"reply": reply}
        )
        
    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if not BijlageToReply.objects.filter(naam=form.cleaned_data["naam"]).exists():
                form.save()
                reply.bijlage = True
                reply.save()
                messages.warning(request, "Bijlage toegevoegd!")
                return redirect(
                    "detailpongreply",
                    client_pk=client_pk,
                    project_pk=project_pk,
                    item_pk=item_pk,
                    type=type,
                )
            else:
                messages.warning(request, "Bijlagenaam bestaat al in dit project. Kies een andere.")
        else:
            messages.warning(request, "Fout met bijlage toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["annotation_pk"] = annotation_pk
    context["new"] = new
    context["item_pk"] = item_pk
    context["bijlage_id"] = bijlage_id
    context["type"] = type
    context["form"] = form
    context["annotation"] = annotation
    return render(request, "partials/form_bijlage_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddStatusPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id,
        onComment__item__id=item_pk,
        commentphase=current_phase,
    ).exists():
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
        form = forms.FirstStatusForm(
            request.POST or None, initial={"status": reply.status}
        )
    else:
        form = forms.FirstStatusForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.status = form.cleaned_data["status"]
                reply.save()
            else:
                reply = CommentReply()
                reply.status = form.cleaned_data["status"]
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.gebruiker = request.user
                reply.save()

            messages.warning(request, "Status toegevoegd!")
            return redirect(
                "detailpongstatus",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
                type=type,
            )

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["type"] = type
    context["form"] = form
    return render(request, "partials/form_status_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddKostenverschilPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id,
        onComment__item__id=item_pk,
        commentphase=current_phase,
    ).exists():
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
        form = forms.FirstKostenverschilForm(
            request.POST or None, initial={"kostenverschil": reply.kostenConsequenties}
        )
    else:
        form = forms.FirstKostenverschilForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.kostenConsequenties = form.cleaned_data["kostenverschil"]
                reply.save()
            else:
                reply = CommentReply()
                reply.kostenConsequenties = form.cleaned_data["kostenverschil"]
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.gebruiker = request.user
                reply.save()

            messages.warning(request, "Kostenverschil toegevoegd!")
            return redirect(
                "detailpongkostenverschil",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
                type=type,
            )

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["form"] = form
    context["type"] = type
    return render(request, "partials/form_kostenverschil_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddReplyPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id,
        onComment__item__id=item_pk,
        commentphase=current_phase,
    ).exists():
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
        form = forms.FirstAnnotationForm(
            request.POST or None, initial={"annotation": reply.comment}
        )
    else:
        form = forms.FirstAnnotationForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.comment = form.cleaned_data["annotation"]
                reply.save()
            else:
                reply = CommentReply()
                reply.comment = form.cleaned_data["annotation"]
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.gebruiker = request.user
                reply.save()

            messages.warning(request, "Opmerking toegevoegd!")
            return redirect(
                "detailpongreply",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
                type=type,
            )

    context["form"] = form
    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["type"] = type
    return render(request, "partials/form_annotation_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteStatusPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)
    
    

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id,
        onComment__item__id=item_pk,
        commentphase=current_phase,
    ).exists():
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
        reply.status = None
        reply.save()
        messages.warning(request, "Status verwijderd.")
        return redirect(
            "detailpongstatus",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
            type=type,
        )

    messages.warning(request, "Fout met status verwijderen.")
    return redirect(
        "detailpongstatus",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
        type=type,
    )


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteReplyPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id,
        onComment__item__id=item_pk,
        commentphase=current_phase,
    ).exists():
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
        reply.comment = None
        reply.save()

        if BijlageToReply.objects.filter(reply__id=reply.id).exists():
            bijlage = BijlageToReply.objects.get(reply__id=reply.id)
            bijlage.delete()

        messages.warning(
            request,
            "Opmerking verwijderd, als u een bijlage had geupload is deze ook verwijderd.",
        )
        return redirect(
            "detailpongreply",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
            type=type,
        )

    messages.warning(request, "Fout met opmerking verwijderen.")
    return redirect(
        "detailpongreply",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
        type=type,
    )


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DeleteKostenverschilPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project=project, item__id=item_pk
        ).first()

    reply = None
    if CommentReply.objects.filter(
        onComment__id=annotation.id,
        onComment__item__id=item_pk,
        commentphase=current_phase,
    ).exists():
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
        reply.kostenConsequenties = None
        reply.save()
        messages.warning(request, "Kostenverschil verwijderd.")
        return redirect(
            "detailpongkostenverschil",
            client_pk=client_pk,
            project_pk=project_pk,
            item_pk=item_pk,
            type=type,
        )

    messages.warning(request, "Fout met kostenverschil verwijderen.")
    return redirect(
        "detailpongkostenverschil",
        client_pk=client_pk,
        project_pk=project_pk,
        item_pk=item_pk,
        type=type,
    )
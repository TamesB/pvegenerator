from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app import models
from project.models import Project, PVEItemAnnotation
from syntrus import forms
from syntrus.forms import BijlageToReplyForm
from syntrus.models import BijlageToReply, CommentReply, FrozenComments


@login_required(login_url="login_syn")
def CheckComments(request, proj_id):
    context = {}

    # get the project
    project = get_object_or_404(Project, pk=proj_id)

    # check first if user is permitted to the project
    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # get the frozencomments and the level
    if not FrozenComments.objects.filter(project__id=proj_id):
        return render(request, "404_syn.html")

    # get the highest ID of the frozencomments phases; the current phase
    frozencomments = (
        FrozenComments.objects.filter(project__id=proj_id).order_by("-level").first()
    )

    # uneven level = turn of SD, even level = turn of SOG
    if (frozencomments.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return render(request, "404_syn.html")
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return render(request, "404_syn.html")

    # the POST method
    if request.method == "POST":
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.CommentReplyForm(
                dict(
                    comment_id=comment_id,
                    annotation=opmrk,
                    status=status,
                    accept=accept,
                    kostenConsequenties=kostenConsequenties,
                )
            )
            for comment_id, opmrk, status, accept, kostenConsequenties in zip(
                request.POST.getlist("comment_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("accept"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]

        for form in ann_forms:
            if (
                form.cleaned_data["status"]
                or form.cleaned_data["accept"] == "True"
                or form.cleaned_data["annotation"]
                or form.cleaned_data["kostenConsequenties"]
            ):
                # get the original comment it was on
                originalComment = PVEItemAnnotation.objects.filter(
                    id=form.cleaned_data["comment_id"]
                ).first()

                if CommentReply.objects.filter(
                    onComment__id=form.cleaned_data["comment_id"],
                    commentphase=frozencomments,
                    gebruiker=request.user,
                ).exists():
                    ann = CommentReply.objects.filter(
                        onComment__id=form.cleaned_data["comment_id"],
                        commentphase=frozencomments,
                        gebruiker=request.user,
                    ).first()
                else:
                    ann = CommentReply()
                    ann.commentphase = frozencomments
                    ann.gebruiker = request.user
                    ann.onComment = originalComment

                if form.cleaned_data["status"]:
                    ann.status = form.cleaned_data["status"]
                if form.cleaned_data["annotation"]:
                    ann.comment = form.cleaned_data["annotation"]
                if form.cleaned_data["kostenConsequenties"]:
                    ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                if form.cleaned_data["accept"] == "True":
                    ann.accept = True
                else:
                    ann.accept = False
                ann.save()

        messages.warning(
            request,
            "Opmerkingen opgeslagen. U kunt later altijd terug naar deze pagina of naar de opmerkingpagina om uw opmerkingen te bewerken voordat u ze opstuurt naar de andere partij.",
        )
        # redirect to project after posting replies for now
        return redirect("myreplies_syn", pk=project.id)

    # the GET method
    non_accepted_comments = (
        frozencomments.comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )
    accepted_comments = (
        frozencomments.accepted_comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )
    todo_comments = (
        frozencomments.todo_comments.select_related("status")
        .select_related("item")
        .select_related("item__hoofdstuk")
        .select_related("item__paragraaf")
        .order_by("item__id")
        .all()
    )

    # create the forms
    ann_forms_accept = make_ann_forms(accepted_comments, frozencomments)
    ann_forms_non_accept = make_ann_forms(non_accepted_comments, frozencomments)
    ann_forms_todo = make_ann_forms(todo_comments, frozencomments)

    # order items for the template
    hoofdstuk_ordered_items_non_accept = order_comments_for_commentcheck(
        non_accepted_comments, proj_id
    )
    hoofdstuk_ordered_items_accept = order_comments_for_commentcheck(
        accepted_comments, proj_id
    )
    hoofdstuk_ordered_items_todo = order_comments_for_commentcheck(
        todo_comments, proj_id
    )

    context["items"] = models.PVEItem.objects.filter(
        projects__id__contains=project.id
    ).order_by("id")
    context["project"] = project
    context["accepted_comments"] = accepted_comments
    context["non_accepted_comments"] = non_accepted_comments
    context["todo_comments"] = todo_comments
    context["forms_accept"] = ann_forms_accept
    context["forms_non_accept"] = ann_forms_non_accept
    context["forms_todo"] = ann_forms_todo
    context["hoofdstuk_ordered_items_non_accept"] = hoofdstuk_ordered_items_non_accept
    context["hoofdstuk_ordered_items_accept"] = hoofdstuk_ordered_items_accept
    context["hoofdstuk_ordered_items_todo"] = hoofdstuk_ordered_items_todo
    context["totale_kosten"] = PVEItemAnnotation.objects.filter(
        project=project
    ).aggregate(Sum("kostenConsequenties"))["kostenConsequenties__sum"]
    return render(request, "CheckComments_syn.html", context)


def order_comments_for_commentcheck(comments_entry, proj_id):
    # loop for reply ordering for the pagedesign
    hoofdstuk_ordered_items_non_accept = {}
    made_on_comments = {}

    # fix this with only showing it for one project, make commentreply model set to a project
    commentreplies = (
        CommentReply.objects.select_related("onComment")
        .filter(onComment__in=comments_entry)
        .all()
    )

    for reply in commentreplies:
        if reply.onComment in made_on_comments.keys():
            made_on_comments[reply.onComment].append([reply])
        else:
            made_on_comments[reply.onComment] = [reply]

    for comment in comments_entry:
        last_accept = False
        # set the PVEItem from the comment
        item = comment.item

        bijlage = None
        #if models.ItemBijlages.objects.get(items__id__contains=item.id).exists():
        #    bijlage = models.ItemBijlages.objects.get(items__id__contains=item.id)
            
        temp_bijlage_list = []
        temp_commentbulk_list_non_accept = []
        string = ""

        if comment.status:
            string = f"{comment.status}"

        # add all replies to this comment
        if comment in made_on_comments.keys():
            commentreplys = CommentReply.objects.filter(Q(onComment=comment)).all()
            last_reply = commentreplys.order_by("-datum").first()

            if last_reply.status is not None:
                string = f"Nieuwe Status: {last_reply.status}"

            if last_reply.accept:
                last_accept = True

            for reply in commentreplys:
                temp_commentbulk_list_non_accept.append(reply.comment)

                if reply.bijlage:
                    temp_bijlage_list.append(reply.id)

            string += ", Opmerkingen: "

            comment_added = False
            for comment_str in temp_commentbulk_list_non_accept:
                if comment_str:
                    string += f""""{ comment_str }", """
                    comment_added = True

            if not comment_added:
                string = string[:-15]
            else:
                string = string[:-2]

        # sort
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items_non_accept.keys():
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items_non_accept[item.hoofdstuk]:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk][
                    item.paragraaf
                ].append(
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        bijlage,
                    ]
                )
            else:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk][item.paragraaf] = [
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        bijlage,
                    ]
                ]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items_non_accept:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk].append(
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        bijlage,
                    ]
                )
            else:
                hoofdstuk_ordered_items_non_accept[item.hoofdstuk] = [
                    [
                        item.inhoud,
                        item.id,
                        comment.id,
                        string,
                        comment.annotation,
                        last_accept,
                        temp_bijlage_list,
                        comment.kostenConsequenties,
                        bijlage,
                    ]
                ]

    return hoofdstuk_ordered_items_non_accept


def make_ann_forms(comments, frozencomments):
    ann_forms = []
    made_on_comments = {}
    commentreplies = CommentReply.objects.select_related("onComment").filter(
        Q(commentphase=frozencomments)
    )

    for reply in commentreplies:
        made_on_comments[reply.onComment] = reply

    for comment in comments:
        # look if the persons reply already exists, for later saving
        if comment not in made_on_comments.keys():
            ann_forms.append(
                forms.CommentReplyForm(
                    initial={
                        "comment_id": comment.id,
                        "accept": "False",
                        "status": comment.status,
                    }
                )
            )
        else:
            reply = made_on_comments[comment]

            if reply.accept:
                ann_forms.append(
                    forms.CommentReplyForm(
                        initial={
                            "comment_id": comment.id,
                            "annotation": reply.comment,
                            "accept": "True",
                            "status": reply.status,
                            "kostenConsequenties": reply.kostenConsequenties,
                        }
                    )
                )
            else:
                ann_forms.append(
                    forms.CommentReplyForm(
                        initial={
                            "comment_id": comment.id,
                            "annotation": reply.comment,
                            "accept": "False",
                            "status": reply.status,
                            "kostenConsequenties": reply.kostenConsequenties,
                        }
                    )
                )
    return ann_forms


@login_required
def MyReplies(request, pk):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # multiple forms
    if request.method == "POST":
        ann_forms = [
            # todo: fix bijlages toevoegen
            forms.CommentReplyForm(
                dict(
                    comment_id=comment_id,
                    annotation=opmrk,
                    status=status,
                    accept=accept,
                    kostenConsequenties=kostenConsequenties,
                )
            )
            for comment_id, opmrk, status, accept, kostenConsequenties in zip(
                request.POST.getlist("comment_id"),
                request.POST.getlist("annotation"),
                request.POST.getlist("status"),
                request.POST.getlist("accept"),
                request.POST.getlist("kostenConsequenties"),
            )
        ]
        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]
        for form in ann_forms:
            if (
                form.cleaned_data["accept"] == "True"
                or form.cleaned_data["status"]
                or form.cleaned_data["annotation"]
                or form.cleaned_data["kostenConsequenties"]
            ):
                # true comment if either comment or voldoet
                original_comment = PVEItemAnnotation.objects.filter(
                    id=form.cleaned_data["comment_id"]
                ).first()
                reply = CommentReply.objects.filter(
                    Q(commentphase=commentphase) & Q(onComment=original_comment)
                ).first()

                if form.cleaned_data["annotation"]:
                    reply.comment = form.cleaned_data["annotation"]

                if form.cleaned_data["status"]:
                    reply.status = form.cleaned_data["status"]

                if form.cleaned_data["kostenConsequenties"]:
                    reply.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                if form.cleaned_data["accept"] == "True":
                    reply.accept = True
                else:
                    reply.accept = False

                reply.save()

        messages.warning(request, f"Opmerking succesvol bewerkt.")
        return redirect("myreplies_syn", pk=project.id)

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    replies = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")
    for reply in replies:
        if reply.accept:
            ann_forms.append(
                forms.CommentReplyForm(
                    initial={
                        "comment_id": reply.onComment.id,
                        "annotation": reply.comment,
                        "status": reply.status,
                        "accept": "True",
                        "kostenConsequenties": reply.kostenConsequenties,
                    }
                )
            )
        else:
            ann_forms.append(
                forms.CommentReplyForm(
                    initial={
                        "comment_id": reply.onComment.id,
                        "annotation": reply.comment,
                        "status": reply.status,
                        "accept": "False",
                        "kostenConsequenties": reply.kostenConsequenties,
                    }
                )
            )
        form_item_ids.append(reply.onComment.id)

    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["replies"] = replies
    context["project"] = project
    context["bijlages"] = bijlages
    context["aantal_opmerkingen_gedaan"] = replies.count()
    return render(request, "MyReplies.html", context)


@login_required
def MyRepliesDelete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )
    replies = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["replies"] = replies
    context["project"] = project
    context["bijlages"] = bijlages
    context["aantal_opmerkingen_gedaan"] = replies.count()
    return render(request, "MyRepliesDelete.html", context)


@login_required
def DeleteReply(request, pk, reply_id):
    # check if project exists
    project = get_object_or_404(Project, id=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(id=reply_id, gebruiker=request.user).exists():
        raise Http404("404")

    reply = CommentReply.objects.filter(id=reply_id).first()
    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )

    if request.method == "POST":
        messages.warning(
            request, f"Opmerking van {reply.onComment.project} verwijderd."
        )
        reply.delete()
        return HttpResponseRedirect(
            reverse("myreplies_syn", args=(project.id,))
        )

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["reply"] = reply
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=pk)
    context["replies"] = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")
    context["project"] = project
    context["bijlages"] = bijlages
    return render(request, "MyRepliesDeleteReply.html", context)


@login_required
def AddReplyAttachment(request, pk, reply_id):
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )
    reply = CommentReply.objects.filter(id=reply_id).first()
    replies = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")

    if reply.gebruiker != request.user:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = forms.BijlageToReplyForm(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["bijlage"]:
                form.save()
                reply.bijlage = True
                reply.save()
                messages.warning(
                    request, f"Bijlage toegevoegd."
                )
                return redirect("myreplies_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    form = BijlageToReplyForm(initial={"reply": reply})
    context["reply"] = reply
    context["form"] = form
    context["project"] = project
    context["replies"] = replies
    return render(request, "MyRepliesAddAttachment.html", context)


@login_required
def DeleteReplyAttachment(request, pk, reply_id):
    # check if project exists
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__contains=request.user.username
        ).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(id=reply_id, gebruiker=request.user).exists():
        raise Http404("404")

    reply = CommentReply.objects.filter(id=reply_id).first()
    attachment = BijlageToReply.objects.filter(reply__id=reply_id).first()
    commentphase = (
        FrozenComments.objects.filter(project__id=pk).order_by("-level").first()
    )

    if request.method == "POST":
        reply.bijlage = False
        reply.save()
        attachment.delete()
        messages.warning(
            request, f"Bijlage verwijderd."
        )
        return HttpResponseRedirect(
            reverse("myreplies_syn", args=(project.id,))
        )

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase, reply__gebruiker=request.user
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["reply"] = reply
    context["items"] = models.PVEItem.objects.filter(projects__id__contains=project.id)
    context["replies"] = CommentReply.objects.filter(
        commentphase=commentphase, gebruiker=request.user
    ).order_by("-datum")
    context["project"] = project
    context["bijlages"] = bijlages
    return render(request, "MyRepliesDeleteAttachment.html", context)

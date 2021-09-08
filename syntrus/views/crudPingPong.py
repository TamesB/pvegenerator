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

from django.core.paginator import Paginator

@login_required(login_url="login_syn")
def CheckComments(request, proj_id):
    context = {}

    # get the project
    project = get_object_or_404(Project, pk=proj_id)

    # check first if user is permitted to the project
    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    # get the current_phase and the level
    if not project.phase.exists():
        return render(request, "404_syn.html")

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return render(request, "404_syn.html")
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return render(request, "404_syn.html")

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

    post_list = None

    if request.method == "POST":
        post_list = {}

        for i in range(len(request.POST.getlist("comment_id"))):
            post_list[int(request.POST.getlist("comment_id")[i])] = [
                request.POST.getlist("annotation")[i],
                None if request.POST.getlist("status")[i] == "" else int(request.POST.getlist("status")[i]),
                request.POST.getlist("accept")[i],
                request.POST.getlist("kostenConsequenties")[i]
            ]

    # create the forms
    ann_forms_accept = make_ann_forms(post_list, accepted_comments, current_phase)
    ann_forms_non_accept = make_ann_forms(post_list, non_accepted_comments, current_phase)
    ann_forms_todo = make_ann_forms(post_list, todo_comments, current_phase)

    # the POST method
    if request.method == "POST":
        ann_forms = ann_forms_todo + ann_forms_non_accept + ann_forms_accept

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]
        for form in ann_forms:
            if form.has_changed():
                print(form.changed_data)
                if form.changed_data != ['status'] or (form.fields['status'].initial != form.cleaned_data['status'].id):
                    # if the reply already exists, edit all fields that aren't the same as in the model.
                    if current_phase.reply.filter(onComment__id=form.cleaned_data["comment_id"]).exists():
                        ann = current_phase.reply.filter(onComment__id=form.cleaned_data["comment_id"]).first()

                        if form.cleaned_data["status"] != ann.status:
                            ann.status = form.cleaned_data["status"]
                        if form.cleaned_data["annotation"] != ann.comment:
                            ann.comment = form.cleaned_data["annotation"]
                        if form.cleaned_data["kostenConsequenties"] != ann.kostenConsequenties:
                            ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                        
                        if form.cleaned_data["accept"] != ann.accept:
                            ann.accept = form.cleaned_data["accept"]
                        
                        ann.save()
                    else:
                        ann = CommentReply()
                        ann.commentphase = current_phase
                        ann.gebruiker = request.user
                        ann.onComment = PVEItemAnnotation.objects.get(
                                            id=form.cleaned_data["comment_id"]
                                        )

                        if form.fields['status'].initial != form.cleaned_data['status'].id:
                            ann.status = form.cleaned_data["status"]
                        if form.cleaned_data["annotation"]:
                            ann.comment = form.cleaned_data["annotation"]
                        if form.cleaned_data["kostenConsequenties"]:
                            ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]
                        if form.cleaned_data["accept"]:
                            ann.accept = form.cleaned_data["accept"]

                        ann.save()

        messages.warning(
            request,
            "Opmerkingen opgeslagen. U kunt later altijd terug naar deze pagina of naar de opmerkingpagina om uw opmerkingen te bewerken voordat u ze opstuurt naar de andere partij.",
        )
        # redirect to project after posting replies for now
        return redirect("myreplies_syn", pk=project.id)

    # order items for the template
    hoofdstuk_ordered_items_non_accept = order_comments_for_commentcheck(
        non_accepted_comments, ann_forms_non_accept, proj_id
    )
    hoofdstuk_ordered_items_accept = order_comments_for_commentcheck(
        accepted_comments, ann_forms_accept, proj_id
    )
    hoofdstuk_ordered_items_todo = order_comments_for_commentcheck(
        todo_comments, ann_forms_todo, proj_id
    )

    context["items"] = project.item.all()
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


def order_comments_for_commentcheck(comments_entry, ann_forms, proj_id):
    # loop for reply ordering for the pagedesign
    hoofdstuk_ordered_items_non_accept = {}
    made_on_comments = {}

    # fix this with only showing it for one project, make commentreply model set to a project
    commentreplies = (
        CommentReply.objects.select_related("onComment")
        .filter(onComment__in=comments_entry)
        .order_by("datum")
        .all()
    )

    # order oncomment to all replies
    for reply in commentreplies:
        if reply.onComment in made_on_comments.keys():
            made_on_comments[reply.onComment].append(reply)
        else:
            made_on_comments[reply.onComment] = [reply]

    for i in range(len(comments_entry)):
        comment = comments_entry[i]
        form = ann_forms[i]
        last_accept = False
        # set the PVEItem from the comment
        item = comment.item

        bijlage = None
        # Fix bijlages later
        #if models.ItemBijlages.objects.get(items__id__contains=item.id).exists():
        #    bijlage = models.ItemBijlages.objects.get(items__id__contains=item.id)
            
        temp_bijlage_list = []
        temp_commentbulk_list_non_accept = []
        string = ""

        if comment.status:
            string = f"{comment.status}"

        # add all replies to this comment
        if comment in made_on_comments.keys():
            last_reply = made_on_comments[comment][0]

            second_to_last_reply = None
            if len(made_on_comments[comment]) > 1:
                second_to_last_reply = made_on_comments[comment][1]

            if last_reply.status is not None:
                string = f"Nieuwe Status: {last_reply.status}"

            if second_to_last_reply:
                if last_reply.accept and second_to_last_reply.accept:
                    last_accept = True

            for reply in made_on_comments[comment]:
                temp_commentbulk_list_non_accept.append([reply.comment, reply.gebruiker])

                if reply.bijlage:
                    temp_bijlage_list.append(reply.id)

            string += ", Opmerkingen: "

            comment_added = False
            for comment_str in temp_commentbulk_list_non_accept:
                if comment_str[0]:
                    string += f""""{ comment_str[0] }" -{comment_str[1]}, """
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
                        form,
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
                        form,
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
                        form,
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
                        form,
                    ]
                ]

    return hoofdstuk_ordered_items_non_accept


def make_ann_forms(post_list, comments, current_phase):
    ann_forms = []
    made_on_comments = {}
    commentreplies = current_phase.reply.select_related("onComment").all()

    for reply in commentreplies:
        made_on_comments[reply.onComment] = reply

    i = 0
    for comment in comments:
        form = forms.CommentReplyForm(
                dict(
                    comment_id=comment.id,
                    annotation=post_list[comment.id][0],
                    status=post_list[comment.id][1],
                    accept=post_list[comment.id][2],
                    kostenConsequenties=post_list[comment.id][3],
                ) if post_list else None, comm_id=comment.id
        )
        form.fields["comment_id"].initial = comment.id

        # look if the persons reply already exists, for later saving
        if comment not in made_on_comments.keys():
            if comment.status:
                form.fields["status"].initial = comment.status.id
            form.fields["accept"].initial = "False"

        else:
            reply = made_on_comments[comment]
            form.fields["annotation"].initial = reply.comment
            form.fields["kostenConsequenties"].initial = reply.kostenConsequenties

            if reply.status:
                form.fields["status"].initial = reply.status.id
            
            if reply.accept:
                form.fields["accept"].initial = "True"
            else:
                form.fields["accept"].initial = "False"

        ann_forms.append(form)
        i += 1

    return ann_forms


@login_required
def MyReplies(request, pk, **kwargs):
    context = {}

    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    commentphase = project.phase.first()

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    ann_forms = []
    form_item_ids = []

    replies = commentphase.reply.select_related("onComment").select_related("onComment__item").all()

    paginator = Paginator(replies, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    comment_id_post = None
    if request.method == "POST":
        comment_id_post = [None if comment_id == "" else int(comment_id) for comment_id in request.POST.getlist("comment_id")]
        annotation_post = request.POST.getlist("annotation")
        status_post = [None if status == "" else int(status) for status in request.POST.getlist("status")]
        accept_post = request.POST.getlist("accept")
        kostenConsequenties_post = request.POST.getlist("kostenConsequenties")

    i = 0
    for reply in page_obj:
        form = forms.CommentReplyForm(
                dict(
                    comment_id=comment_id_post[i],
                    annotation=annotation_post[i],
                    status=status_post[i],
                    accept=accept_post[i],
                    kostenConsequenties=kostenConsequenties_post[i],
                ) if comment_id_post else None,
                initial={
                    "comment_id": reply.onComment.id,
                    "annotation": reply.comment,
                    "kostenConsequenties": reply.kostenConsequenties,
                }, comm_id=comment_id_post[i] if comment_id_post else None
            )

        if reply.accept:
            form.fields["accept"].initial = "True"
        else:
            form.fields["accept"].initial = "False"

        if reply.status:
            form.fields["status"].initial = reply.status.id

        ann_forms.append(form)
        form_item_ids.append(reply.onComment.id)
        i += 1

    # multiple forms
    if request.method == "POST":
        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]
        for form in ann_forms:
            if form.has_changed():
                if form.changed_data != ['status'] or (form.fields['status'].initial != form.cleaned_data['status'].id):
                    # true comment if either comment or voldoet
                    original_comment = PVEItemAnnotation.objects.get(
                        id=form.cleaned_data["comment_id"]
                    )
                    reply = commentphase.reply.filter(onComment__id=original_comment.id).first()

                    if form.cleaned_data["annotation"]:
                        reply.comment = form.cleaned_data["annotation"]

                    if form.fields['status'].initial != form.cleaned_data['status'].id:
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

    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = project.item.all()
    context["replies"] = replies
    context["project"] = project
    context["bijlages"] = bijlages
    context["aantal_opmerkingen_gedaan"] = replies.count()
    context["page_obj"] = page_obj
    return render(request, "MyReplies.html", context)


@login_required
def MyRepliesDelete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.permitted.all():
        return render(request, "404_syn.html")

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")
    
    commentphase = project.phase.first()

    replies = commentphase.replies.all()

    paginator = Paginator(replies, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    bijlages = []

    for bijlage in BijlageToReply.objects.filter(
        reply__commentphase=commentphase
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["page_obj"] = page_obj
    context["items"] = project.items.all()
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
        if not request.user.permittedprojects.filter(id=pk).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(id=reply_id).exists():
        raise Http404("404")

    reply = CommentReply.objects.get(id=reply_id)
    commentphase = project.phase.first()
    
    page_number = request.GET.get('page')

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
        reply__commentphase=commentphase
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["reply"] = reply
    context["items"] = project.item.all()
    context["replies"] = commentphase.reply.all()
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

    commentphase = project.phase.first()

    reply = CommentReply.objects.filter(id=reply_id).first()
    replies = commentphase.reply.all()

    paginator = Paginator(replies, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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
    context["page_obj"] = page_obj
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
        if not request.user.permittedprojects.filter(id=pk):
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(id=reply_id).exists():
        raise Http404("404")

    reply = CommentReply.objects.filter(id=reply_id).first()
    attachment = BijlageToReply.objects.filter(reply__id=reply_id).first()
    commentphase = project.phase.first()

    page_number = request.GET.get('page')

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
        reply__commentphase=commentphase
    ):
        if bijlage.bijlage.url:
            bijlages.append(bijlage.bijlage.url)
        else:
            bijlages.append(None)

    context = {}
    context["reply"] = reply
    context["items"] = project.item.all()
    context["replies"] = commentphase.replies.all()
    context["project"] = project
    context["bijlages"] = bijlages
    return render(request, "MyRepliesDeleteAttachment.html", context)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from app import models
from project.models import Project, PVEItemAnnotation, Beleggers
from syntrus import forms
from syntrus.forms import BijlageToReplyForm
from syntrus.models import BijlageToReply, CommentReply, FrozenComments
from syntrus.views.utils import GetAWSURL

from django.core.paginator import Paginator
import time

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def CheckComments(request, client_pk, proj_id):
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

    start = time.time()
    context = {}
    
    # get the current_phase and the level
    if not Project.objects.filter(pk=proj_id):
        return redirect("logout_syn", client_pk=client_pk)

    # get the project
    project = Project.objects.prefetch_related("phase").get(pk=proj_id)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)
    # check first if user is permitted to the project
    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    # get the current_phase and the level
    if not project.phase.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    clausetime = time.time()
    print(f"Clauses: {clausetime - start}")

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

    todotime = time.time()
    print(f"Get todos: {todotime - clausetime}, total: {todotime - start}")

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


    postform = time.time()
    print(f"Get POSTforms: {postform - todotime}, total: {postform - start}")

    # create the forms
    ann_forms_accept = make_ann_forms(post_list, accepted_comments, current_phase)
    ann_forms_non_accept = make_ann_forms(post_list, non_accepted_comments, current_phase)
    ann_forms_todo = make_ann_forms(post_list, todo_comments, current_phase)

    create_ann = time.time()
    print(f"create all ann_forms: {create_ann - postform}, total: {create_ann - start}")

    # the POST method
    if request.method == "POST":
        ann_forms = ann_forms_todo + ann_forms_non_accept + ann_forms_accept

        # only use valid forms
        ann_forms = [
            ann_forms[i] for i in range(len(ann_forms)) if ann_forms[i].is_valid()
        ]
        for form in ann_forms:
            if form.has_changed():
                if (form.changed_data != ['status'] or (form.cleaned_data["status"] and form.fields['status'].initial != form.cleaned_data['status'].id)) and (form.changed_data != ['item_id']):
                    # if the reply already exists, edit all fields that aren't the same as in the model.
                    if current_phase.reply.filter(onComment__id=form.cleaned_data["comment_id"]).exists():
                        ann = current_phase.reply.filter(onComment__id=form.cleaned_data["comment_id"]).first()

                        if form.cleaned_data["accept"] != ann.accept:
                            ann.accept = form.cleaned_data["accept"]

                        # dont add annotation/extra costs when the rule is accepted.
                        if form.cleaned_data["accept"] == "True":
                            ann.status = None
                            ann.comment = None
                            ann.kostenConsequenties = None
                            ann.accept = True
                        else:
                            if form.cleaned_data["status"] != ann.status:
                                ann.status = form.cleaned_data["status"]
                            if form.cleaned_data["annotation"] != ann.comment:
                                ann.comment = form.cleaned_data["annotation"]
                            if form.cleaned_data["kostenConsequenties"] != ann.kostenConsequenties:
                                ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                            ann.accept = False                        
                        
                        ann.save()
                    else:
                        ann = CommentReply()
                        ann.commentphase = current_phase
                        ann.gebruiker = request.user
                        ann.onComment = PVEItemAnnotation.objects.get(
                                            id=form.cleaned_data["comment_id"]
                                        )

                        # if accepted rule, dont add any status/comment/costs, else add these.
                        if form.cleaned_data["accept"] == "True":
                            ann.accept = True
                        else:
                            if form.cleaned_data["status"] and form.fields['status'].initial != form.cleaned_data['status'].id:
                                ann.status = form.cleaned_data["status"]
                            if form.cleaned_data["annotation"]:
                                ann.comment = form.cleaned_data["annotation"]
                            if form.cleaned_data["kostenConsequenties"]:
                                ann.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                            ann.accept = False

                        ann.save()

        messages.warning(
            request,
            "Opmerkingen opgeslagen. U kunt later altijd terug naar deze pagina of naar de opmerkingpagina om uw opmerkingen te bewerken voordat u ze opstuurt naar de andere partij.",
        )
        # redirect to project after posting replies for now
        return redirect("myreplies_syn", client_pk=client_pk, pk=project.id)

    # order items for the template
    hoofdstuk_ordered_items_non_accept = order_comments_for_commentcheck(
        non_accepted_comments, ann_forms_non_accept, project
    )
    hoofdstuk_ordered_items_accept = order_comments_for_commentcheck(
        accepted_comments, ann_forms_accept, project
    )
    hoofdstuk_ordered_items_todo = order_comments_for_commentcheck(
        todo_comments, ann_forms_todo, project
    )

    orderhfst = time.time()
    print(f"Order hfst: {orderhfst - create_ann}, total: {orderhfst - start}")

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

    contexts = time.time()
    print(f"Create contexts, right before rendering: {contexts - orderhfst}, total: {contexts - start}")

    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "CheckComments_syn.html", context)


def order_comments_for_commentcheck(comments_entry, ann_forms, project):
    # loop for reply ordering for the pagedesign
    hoofdstuk_ordered_items = {}
    made_on_comments = {}

    # fix this with only showing it for one project, make commentreply model set to a project
    commentreplies = (
        CommentReply.objects.select_related("onComment")
        .select_related("gebruiker")
        .select_related("commentphase")
        .select_related("status")
        .filter(onComment__in=comments_entry)
        .exclude(commentphase=project.phase.first())
        .order_by("-datum")
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
        both_accepted = False
        # set the PVEItem from the comment
        item = comment.item

        regel_bijlage = None
        # Fix bijlages later
        #if models.ItemBijlages.objects.get(items__id__contains=item.id).exists():
        #    bijlage = models.ItemBijlages.objects.get(items__id__contains=item.id)
            
        comment_bijlages = []
        temp_commentbulk_list_non_accept = []
        string = ""

        if comment.status:
            string = f"{comment.status}"

        # add all replies to this comment
        if comment in made_on_comments.keys():
            last_reply = None
            if len(made_on_comments[comment]) > 0:
                last_reply = made_on_comments[comment][0]

            second_to_last_reply = None
            if len(made_on_comments[comment]) > 1:
                second_to_last_reply = made_on_comments[comment][1]

            if last_reply:
                if last_reply.status is not None:
                    string = f"Nieuwe Status: {last_reply.status}"

            if second_to_last_reply:
                if last_reply.accept and second_to_last_reply.accept:
                    both_accepted = True

            for reply in made_on_comments[comment]:
                temp_commentbulk_list_non_accept.append([reply.comment, reply.gebruiker])

                if reply.bijlage:
                    comment_bijlages.append(reply.id)

            if len(temp_commentbulk_list_non_accept) != 0:
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
        
        total_item_context = [
                        item,
                        comment,
                        form,
                        string,
                        both_accepted,
                        comment_bijlages,
                        regel_bijlage,
                    ]

        # sort
        if item.paragraaf:
            if item.hoofdstuk not in hoofdstuk_ordered_items.keys():
                hoofdstuk_ordered_items[item.hoofdstuk] = {}

            if item.paragraaf in hoofdstuk_ordered_items[item.hoofdstuk]:
                hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf].append(total_item_context)
            else:
                hoofdstuk_ordered_items[item.hoofdstuk][item.paragraaf] = [total_item_context]
        else:
            if item.hoofdstuk in hoofdstuk_ordered_items:
                hoofdstuk_ordered_items[item.hoofdstuk].append(total_item_context)
            else:
                hoofdstuk_ordered_items[item.hoofdstuk] = [total_item_context]

    return hoofdstuk_ordered_items


def make_ann_forms(post_list, comments, current_phase):
    ann_forms = []
    made_on_comments = {}
    commentreplies = current_phase.reply.select_related("onComment").select_related("status").all()

    for reply in commentreplies.iterator():
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


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def MyReplies(request, client_pk, pk, **kwargs):
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
   
    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    commentphase = project.phase.first()

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

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

    replies = commentphase.reply.select_related("onComment").select_related("onComment__item").select_related("status").all()

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
                }, comm_id=reply.onComment.id
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

                    if form.cleaned_data["accept"] == "True":
                        reply.accept = True
                        reply.annotation = None
                        reply.status = None
                        reply.kostenConsequenties = None
                    else:
                        if form.cleaned_data["annotation"]:
                            reply.comment = form.cleaned_data["annotation"]

                        if form.fields['status'].initial != form.cleaned_data['status'].id:
                            reply.status = form.cleaned_data["status"]

                        if form.cleaned_data["kostenConsequenties"]:
                            reply.kostenConsequenties = form.cleaned_data["kostenConsequenties"]

                        reply.accept = False

                    reply.save()
                
                messages.warning(request, f"Opmerking succesvol bewerkt.")
            else:
                messages.warning(request, f"Opmerking niet veranderd.")
                
        return redirect("myreplies_syn", client_pk=client_pk, pk=project.id)

    context["ann_forms"] = ann_forms
    context["form_item_ids"] = form_item_ids
    context["items"] = project.item.all()
    context["replies"] = replies
    context["project"] = project
    context["bijlages"] = bijlages
    context["aantal_opmerkingen_gedaan"] = replies.count()
    context["page_obj"] = page_obj
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyReplies.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def MyRepliesDelete(request, client_pk, pk):
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

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)
    
    commentphase = project.phase.first()

    replies = commentphase.replies.select_related("onComment").select_related("onComment__item").select_related("status").all()

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
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyRepliesDelete.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DeleteReply(request, client_pk, pk, reply_id):
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
    project = get_object_or_404(Project, id=pk)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not request.user.projectspermitted.filter(id=pk).exists():
            raise Http404("404")

    # check if user placed that annotation
    if not CommentReply.objects.filter(id=reply_id).exists():
        raise Http404("404")

    reply = CommentReply.objects.get(id=reply_id)
    commentphase = project.phase.first()
    replies = commentphase.reply.select_related("onComment").select_related("onComment__item").select_related("status").all()
    paginator = Paginator(replies, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


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
    context["page_obj"] = page_obj
    context["project"] = project
    context["bijlages"] = bijlages
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyRepliesDeleteReply.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddReplyAttachment(request, client_pk, pk, reply_id):
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

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    commentphase = project.phase.first()

    reply = CommentReply.objects.filter(id=reply_id).first()
    replies = commentphase.reply.select_related("onComment").select_related("onComment__item").select_related("status").all()

    paginator = Paginator(replies, 25) # Show 25 replies per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if reply.gebruiker != request.user:
        return redirect("logout_syn", client_pk=client_pk)

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
                return redirect("myreplies_syn", client_pk=client_pk, pk=project.id)
            else:
                messages.warning(request, "Vul de verplichte velden in.")

        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    form = BijlageToReplyForm(initial={"reply": reply})
    context["reply"] = reply
    context["form"] = form
    context["project"] = project
    context["replies"] = replies
    context["page_obj"] = page_obj
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyRepliesAddAttachment.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DeleteReplyAttachment(request, client_pk, pk, reply_id):
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
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not request.user.projectspermitted.filter(id=pk):
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
            reverse("myreplies_syn", args=(client_pk, project.id,))
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
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "MyRepliesDeleteAttachment.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def CheckComments_temp(request, client_pk, proj_id):
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

    project = get_object_or_404(Project, pk=proj_id)
    if project.belegger != client:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.user not in project.permitted.all():
        return redirect("logout_syn", client_pk=client_pk)

    # get the current_phase and the level
    if not project.phase.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

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

    hoofdstukken_non_accept = make_hoofdstukken(
        non_accepted_comments
    )
    hoofdstukken_accept = make_hoofdstukken(
        accepted_comments
    )
    hoofdstukken_todo = make_hoofdstukken(
        todo_comments
    )

    context["hoofdstukken_non_accept"] = hoofdstukken_non_accept
    context["hoofdstukken_accept"] = hoofdstukken_accept
    context["hoofdstukken_todo"] = hoofdstukken_todo
    context["hoofdstukken_todo"] = hoofdstukken_todo
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

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def GetParagravenPingPong(request, client_pk, pk, hoofdstuk_pk, type, accept):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
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

    for item in items:
        if item.paragraaf not in paragraven:
            paragraven.append(item.paragraaf)

    context["comments"] = comments
    context["items"] = items
    context["type"] = type
    context["paragraven"] = paragraven
    context["project"] = project
    context["client_pk"] = client_pk
    context["accept"] = accept
    return render(request, "partials/paragravenpartialpong.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def GetItemsPingPong(request, client_pk, pk, hoofdstuk_pk, paragraaf_id, type, accept):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
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

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    
    item = project.item.filter(id=item_pk).first()

    itembijlage = None
    if models.ItemBijlages.objects.filter(items__id=item.id).exists():
        itembijlage = models.ItemBijlages.objects.filter(items__id=item.id).first()

    replies = None
    bijlagen = {}

    if CommentReply.objects.filter(onComment__item__id=item.id).exists():
        replies = CommentReply.objects.filter(Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase)).order_by("id")

        for reply in replies:
            if reply.bijlagetoreply.exists():
                bijlagen[reply] = reply.bijlagetoreply.first()

    annotation = None
    if PVEItemAnnotation.objects.filter(project__id=project_pk, item__id=item.id).exists():
        annotation = PVEItemAnnotation.objects.filter(project__id=project_pk, item__id=item.id).first()

        annotationbijlage = None
        if annotation.bijlageobject.exists():
            annotationbijlage = annotation.bijlageobject.first()

    context["item"] = item
    context["itembijlage"] = itembijlage
    context["replies"] = replies
    context["bijlagen"] = bijlagen
    context["annotation"] = annotation
    context["annotationbijlage"] = annotationbijlage
    context["client_pk"] = client_pk
    context["type"] = type
    context["project_pk"] = project_pk
    return render(request, "partials/getitempartial.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailStatusPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    # find last changed status
    status_reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id).exists():
        replies = CommentReply.objects.filter(Q(onComment__id=annotation.id) & ~Q(commentphase=current_phase)).order_by("id")

        for reply in replies:
            if reply.status:
                status_reply = reply

    current_reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, commentphase=current_phase).exists():
        current_reply = CommentReply.objects.filter(onComment__id=annotation.id, commentphase=current_phase).first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["current_reply"] = current_reply
    context["status_reply"] = status_reply
    context["type"] = type
    return render(request, "partials/detail_status_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailReplyPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    reply = None
    bijlage = None

    if CommentReply.objects.filter(commentphase=current_phase, onComment__item__id=item_pk).exists():
        reply = CommentReply.objects.filter(commentphase=current_phase, onComment__item__id=item_pk).first()

        if reply.bijlagetoreply.exists():
            bijlage = reply.bijlagetoreply.first()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["reply"] = reply
    context["current_reply"] = reply
    context["bijlage"] = bijlage
    context["type"] = type
    return render(request, "partials/detail_annotation_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailKostenverschilPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    current_reply = None
    if CommentReply.objects.filter(commentphase=current_phase, onComment__id=annotation.id).exists():
        current_reply = CommentReply.objects.filter(commentphase=current_phase, onComment__id=annotation.id).first()

    # find last changed status
    last_reply = None
    if CommentReply.objects.filter(onComment__item__id=item_pk).exists():
        replies = CommentReply.objects.filter(Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase)).order_by("id")

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

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DetailAcceptPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)


    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    current_reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, commentphase=current_phase).exists():
        current_reply = CommentReply.objects.get(onComment__id=annotation.id, commentphase=current_phase)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["current_reply"] = current_reply
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AcceptItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    current_reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, commentphase=current_phase).exists():
        current_reply = CommentReply.objects.get(onComment__id=annotation.id, commentphase=current_phase)
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
        current_reply = CommentReply.objects.create(commentphase=current_phase, gebruiker=request.user, onComment=annotation, accept=True)
        current_reply.save()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["current_reply"] = current_reply
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def NonAcceptItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    current_reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, commentphase=current_phase).exists():
        current_reply = CommentReply.objects.get(onComment__id=annotation.id, commentphase=current_phase)
        current_reply.accept = False
        current_reply.save()
    else:
        current_reply = CommentReply.objects.create(commentphase=current_phase, gebruiker=request.user, onComment=annotation, accept=False)
        current_reply.save()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["current_reply"] = current_reply
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddBijlagePong(request, client_pk, project_pk, item_pk, annotation_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()

    if BijlageToReply.objects.filter(reply__id=annotation_pk).exists():
        bijlagemodel = BijlageToReply.objects.filter(reply__id=annotation_pk).first()
        form = forms.PongBijlageForm(request.POST or None, request.FILES or None, instance=bijlagemodel)
    else:
        form = forms.PongBijlageForm(request.POST or None, request.FILES or None, initial={'reply': reply})

    
    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            print(form.cleaned_data['bijlage'])
            form.save()
            messages.warning(request, "Bijlage toegevoegd!")
            return redirect("detailpongreply", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

        messages.warning(request, "Fout met bijlage toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["annotation_pk"] = annotation_pk
    context["item_pk"] = item_pk
    context["type"] = type
    context["form"] = form
    context["annotation"] = annotation
    return render(request, "partials/form_bijlage_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddStatusPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).exists():
        reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()
        form = forms.FirstStatusForm(request.POST or None, initial={'status': reply.status})
    else:
        form = forms.FirstStatusForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.status = form.cleaned_data['status']
                reply.save()
            else:
                reply = CommentReply()
                reply.status = form.cleaned_data['status']
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.gebruiker = request.user
                reply.save()

            messages.warning(request, "Status toegevoegd!")
            return redirect("detailpongstatus", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["type"] = type
    context["form"] = form
    return render(request, "partials/form_status_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddKostenverschilPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).exists():
        reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()
        form = forms.FirstKostenverschilForm(request.POST or None, initial={'kostenverschil': reply.kostenConsequenties})
    else:
        form = forms.FirstKostenverschilForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.kostenConsequenties = form.cleaned_data['kostenverschil']
                reply.save()
            else:
                reply = CommentReply()
                reply.kostenConsequenties = form.cleaned_data['kostenverschil']
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.gebruiker = request.user
                reply.save()

            messages.warning(request, "Kostenverschil toegevoegd!")
            return redirect("detailpongkostenverschil", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["form"] = form
    context["type"] = type
    return render(request, "partials/form_kostenverschil_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def AddReplyPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).exists():
        reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()
        form = forms.FirstAnnotationForm(request.POST or None, initial={'annotation': reply.comment})
    else:
        form = forms.FirstAnnotationForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.comment = form.cleaned_data['annotation']
                reply.save()
            else:
                reply = CommentReply()
                reply.comment = form.cleaned_data['annotation']
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.gebruiker = request.user
                reply.save()

            messages.warning(request, "Opmerking toegevoegd!")
            return redirect("detailpongreply", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

    context["form"] = form
    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["type"] = type
    return render(request, "partials/form_annotation_pong.html", context)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DeleteStatusPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).exists():
        reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()
        reply.status = None
        reply.save()
        messages.warning(request, "Status verwijderd.")
        return redirect("detailpongstatus", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

    messages.warning(request, "Fout met status verwijderen.")
    return redirect("detailpongstatus", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DeleteReplyPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).exists():
        reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()
        reply.comment = None
        reply.save()

        if BijlageToReply.objects.filter(reply__id=reply.id).exists():
            bijlage = BijlageToReply.objects.get(reply__id=reply.id)
            bijlage.delete()

        messages.warning(request, "Opmerking verwijderd, als u een bijlage had geupload is deze ook verwijderd.")
        return redirect("detailpongreply", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

    messages.warning(request, "Fout met opmerking verwijderen.")
    return redirect("detailpongreply", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

@login_required(login_url=reverse_lazy("login_syn", args={1,}))
def DeleteKostenverschilPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    project = get_object_or_404(Project, pk=project_pk)
    if project.belegger != Beleggers.objects.filter(pk=client_pk).first():
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if not project.item.exists():
        return redirect("logout_syn", client_pk=client_pk)

    # get the highest ID of the frozencomments phases; the current phase
    current_phase = project.phase.first()

    # uneven level = turn of SD, even level = turn of SOG
    if (current_phase.level % 2) != 0:
        # level uneven: make page only visible for SD
        if request.user.type_user == project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)
    else:
        # level even: make page only visible for SOG
        if request.user.type_user != project.first_annotate:
            return redirect("logout_syn", client_pk=client_pk)

    annotation = None
    if PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).exists():
        annotation = PVEItemAnnotation.objects.filter(project=project, item__id=item_pk).first()

    reply = None
    if CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).exists():
        reply = CommentReply.objects.filter(onComment__id=annotation.id, onComment__item__id=item_pk, commentphase=current_phase).first()
        reply.kostenConsequenties = None
        reply.save()
        messages.warning(request, "Kostenverschil verwijderd.")
        return redirect("detailpongkostenverschil", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

    messages.warning(request, "Fout met kostenverschil verwijderen.")
    return redirect("detailpongkostenverschil", client_pk=client_pk, project_pk=project_pk, item_pk=item_pk, type=type)

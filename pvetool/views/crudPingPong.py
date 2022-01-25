from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
import decimal
from app import models
from project.models import Project, PVEItemAnnotation, Beleggers
from pvetool import forms
from pvetool.models import BijlageToReply, CommentReply, FrozenComments, CommentRequirement, CommentStatus
from pvetool.views.utils import GetAWSURL
from pvetool.views import hardcoded_values

# The URL map for specific tabs of comments in the pingpongprocess.
type_map = {
    "TODO_COMMENTS": 0,
    "CHANGED_COMMENTS": 1,
    "ACCEPTED_COMMENTS": 2,
}

# the URL map for whether a chapter has paragraphs or not
has_paragraphs = {
    False: 0
}

# further maps from URLsafe values to boolean values
exists = {
    True: 1,
    False: 0
}

# this function checks if the client exists, whether the user is authenticated to the client, project is of the client,
# the project is not in first annotate stage, the project contains a pve,
# whether the user is permitted to the project,
# and the current phase allows the usertype to see the page.
def passed_commentcheck_guardclauses(request, client_pk, project_pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return False, False

    client = Beleggers.objects.filter(pk=client_pk).first()

    if request.user.client:
        if (
            request.user.client.id != client.id
            and request.user.type_user != "B"
        ):
            return False, False
    else:
        return False, False

    if not Project.objects.filter(pk=project_pk).exists():
        return False, False

    project = Project.objects.get(pk=project_pk)

    if project.client != Beleggers.objects.filter(pk=client_pk).first():
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
        .select_related("item__chapter")
        .select_related("item__paragraph")
        .order_by("item__id")
        .all()
    )

    accepted_comments = (
        current_phase.accepted_comments.select_related("status")
        .select_related("item")
        .select_related("item__chapter")
        .select_related("item__paragraph")
        .order_by("item__id")
        .all()
    )

    todo_comments = (
        current_phase.todo_comments.select_related("status")
        .select_related("item")
        .select_related("item__chapter")
        .select_related("item__paragraph")
        .order_by("item__id")
        .all()
    )

    # accepted comments and todo comments are tabs. Get chapters and replies of these.
    chapters_accept = make_chapters(accepted_comments)
    chapters_todo = make_chapters(todo_comments)

    accepted_hfst_replies = {chapter.id: 0 for chapter in chapters_accept}
    todo_hfst_replies = {chapter.id: 0 for chapter in chapters_todo}

    accepted_replies = current_phase.reply.select_related("onComment__item__chapter").filter(onComment__in=accepted_comments)
    todo_replies = current_phase.reply.select_related("onComment__item__chapter").filter(onComment__in=todo_comments)
    
    # Get all the possible statuses
    status_objs = CommentStatus.objects.all()
    
    status_tabs = []
    
    # reduce some statuses to a single status (preserve tab space on-screen)
    for status in status_objs:
        if status.status in hardcoded_values.later_status_category():
            if hardcoded_values.later_status_category_name() not in status_tabs:
                status_tabs.append(hardcoded_values.later_status_category_name())
        else:
            status_tabs.append(status.status)
    
    # create chapters and replies for each status
    chapters_statuses = {status:None for status in status_tabs}
    replies_statuses = {status:None for status in status_tabs}
    status_hfst_replies = {status:None for status in status_tabs}
    status_hfst_count = {status:None for status in status_tabs}
    
    non_accepted_comments_breakdown = {status:None for status in status_tabs}
    
    # set these comments/make these chapters
    for status in status_objs:
        
        # reduce some statuses to a single status
        status_obj = status
        status = status.status
        
        if status in hardcoded_values.later_status_category():
            status = hardcoded_values.later_status_category_name()
        
        # calculate comments
        if non_accepted_comments_breakdown[status]:
            non_accepted_comments_breakdown[status].union(non_accepted_comments.filter(status=status_obj))
        else:
            non_accepted_comments_breakdown[status] = non_accepted_comments.filter(status=status_obj)
            
        # calculate chapters
        if chapters_statuses[status]:
            chapters_statuses[status] = {**chapters_statuses[status], **make_chapters(non_accepted_comments_breakdown[status])}
        else:
            chapters_statuses[status] = make_chapters(non_accepted_comments_breakdown[status])
        
        # calculate replies to these comments
        if replies_statuses[status]:
            replies_statuses[status].union(current_phase.reply.select_related("onComment__item__chapter").filter(onComment__in=non_accepted_comments_breakdown[status]))
        else:
            replies_statuses[status] = current_phase.reply.select_related("onComment__item__chapter").filter(onComment__in=non_accepted_comments_breakdown[status])
            
        # calculate number of replies replies per chapter
        if status_hfst_replies[status]:
            status_hfst_replies[status] = {**status_hfst_replies[status], **{chapter.id: 0 for chapter in chapters_statuses[status]}}
        else: 
            status_hfst_replies[status] = {chapter.id: 0 for chapter in chapters_statuses[status]}

    # count amount of replies for each statustab and each chapter
    for status in status_tabs:
        for reply in replies_statuses[status]:
            chapter = reply.onComment.item.chapter.id
            if chapter in status_hfst_replies[status].keys():
                status_hfst_replies[status][chapter] += 1
            else:
                status_hfst_replies[status][chapter] = 1
            
    for reply in accepted_replies:
        chapter = reply.onComment.item.chapter.id
        if chapter in accepted_hfst_replies:
            accepted_hfst_replies[chapter] += 1
        else:
            accepted_hfst_replies[chapter] = 1
            
    for reply in todo_replies:
        chapter = reply.onComment.item.chapter.id
        if chapter in todo_hfst_replies:
            todo_hfst_replies[chapter] += 1
        else:
            todo_hfst_replies[chapter] = 1

    # count amount of comments per chapter
    for status in status_tabs:
        status_hfst_count[status] = {chapter.id: 0 for chapter in chapters_statuses[status]}
    
    accepted_hfst_count = {chapter.id: 0 for chapter in chapters_accept}
    todo_hfst_count = {chapter.id: 0 for chapter in chapters_todo}

    for comment in non_accepted_comments:
        status = comment.status.status
        if status in hardcoded_values.later_status_category():
            status = hardcoded_values.later_status_category_name()
        
        try:
            status_hfst_count[status][comment.item.chapter.id] += 1
        except KeyError:
            status_hfst_count[status][comment.item.chapter.id] = 1
        
    for comment in accepted_comments:
        accepted_hfst_count[comment.item.chapter.id] += 1
    for comment in todo_comments:
        todo_hfst_count[comment.item.chapter.id] += 1

    # calculating total costs of whole project, depending if costs are of each VHE or of whole project per rule.
    totale_kosten = 0
    if PVEItemAnnotation.objects.filter(
        project=project
    ):
        cost_qs = PVEItemAnnotation.objects.filter(project=project, consequentCosts__isnull=False)
        
        for obj in cost_qs:
            if obj.costtype:
                if obj.costtype.type == "per VHE":
                    totale_kosten += (obj.consequentCosts * decimal.Decimal(project.vhe))
                else:
                    totale_kosten += obj.consequentCosts
            else:
                totale_kosten += obj.consequentCosts
                
    #counting for each dict
    non_accepted_comments_breakdown_count = {}
    replies_statuses_count = {}
    
    for status in non_accepted_comments_breakdown.keys():
        non_accepted_comments_breakdown_count[status] = len(non_accepted_comments_breakdown[status])
    for status in replies_statuses.keys():
        replies_statuses_count[status] = len(replies_statuses[status])
                
    context["status_objs"] = status_objs
    context["status_tabs"] = status_tabs
    context["status_to_id"] = hardcoded_values.status_to_id()
    context["chapters_statuses"] = chapters_statuses #chapters_non_accept
    context["chapters_accept"] = chapters_accept
    context["chapters_todo"] = chapters_todo
    context["status_hfst_replies"] = status_hfst_replies #non_accepted_hfst_replies
    context["accepted_hfst_replies"] = accepted_hfst_replies
    context["todo_hfst_replies"] = todo_hfst_replies
    context["status_hfst_count"] = status_hfst_count #non_accepted_hfst_count
    context["accepted_hfst_count"] = accepted_hfst_count
    context["todo_hfst_count"] = todo_hfst_count
    context["accepted_comments"] = accepted_comments
    context["todo_comments"] = todo_comments
    context["non_accepted_comments_breakdown"] = non_accepted_comments_breakdown #non_accepted_comments
    context["non_accepted_comments_breakdown_count"] = non_accepted_comments_breakdown_count #non_accepted_comments
    context["replies_statuses"] = replies_statuses #non_accepted_replies
    context["replies_statuses_count"] = replies_statuses_count #non_accepted_replies
    context["accepted_replies"] = accepted_replies
    context["todo_replies"] = todo_replies
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["commentphase"] = current_phase
    context["last_level"] = current_phase.level - 1
    context["logo_url"] = logo_url
    context["totale_kosten"] = totale_kosten
    return render(request, "CheckComments_temp.html", context)


def make_chapters(comments):
    chapter_ordered_items = {}

    for comment in comments:
        item = comment.item
        if item.chapter not in chapter_ordered_items.keys():
            if item.paragraph:
                chapter_ordered_items[item.chapter] = True
            else:
                chapter_ordered_items[item.chapter] = False

    return chapter_ordered_items


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetParagravenPingPong(request, client_pk, pk, chapter_pk, type, accept, status_id):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(request, client_pk, pk)

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    comments = None

    if type == type_map["CHANGED_COMMENTS"]:
        if status_id in hardcoded_values.later_status_category() or status_id == 0:
            query_status = hardcoded_values.status_id_later_status()
        else:
            query_status = [status_id]
        
        comments = (
            current_phase.comments.select_related("status")
            .select_related("item")
            .select_related("item__chapter")
            .select_related("item__paragraph")
            .filter(item__chapter__id=chapter_pk)
            .filter(status__id__in=query_status)
            .order_by("item__id")
            .all()
        )
    if type == type_map["ACCEPTED_COMMENTS"]:
        comments = (
            current_phase.accepted_comments.select_related("status")
            .select_related("item")
            .select_related("item__chapter")
            .select_related("item__paragraph")
            .filter(item__chapter__id=chapter_pk)
            .order_by("item__id")
            .all()
        )
    if type == type_map["TODO_COMMENTS"]:
        comments = (
            current_phase.todo_comments.select_related("status")
            .select_related("item")
            .select_related("item__chapter")
            .select_related("item__paragraph")
            .filter(item__chapter__id=chapter_pk)
            .order_by("item__id")
            .all()
        )

    items = [comment.item for comment in comments]

    paragraphs = []
    paragraphs_ids = []

    for item in items:
        if item.paragraph.id not in paragraphs_ids:
            paragraphs.append(item.paragraph)
            paragraphs_ids.append(item.paragraph.id)
    
    context["comments"] = comments
    context["status_id"] = status_id
    context["items"] = items
    context["type"] = type
    context["paragraphs"] = paragraphs
    context["project"] = project
    context["client_pk"] = client_pk
    context["accept"] = accept
    return render(request, "partials/paragraphspartialpong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def GetItemsPingPong(request, client_pk, pk, chapter_pk, paragraph_id, type, accept, status_id):    
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(request, client_pk, pk)

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    comments = None

    if type == type_map["CHANGED_COMMENTS"]:
        if status_id in hardcoded_values.later_status_category() or status_id == 0:
            query_status = hardcoded_values.status_id_later_status()
        else:
            query_status = [status_id]

        if paragraph_id == has_paragraphs[False]:
            comments = (
                current_phase.comments.select_related("status")
                .select_related("item")
                .select_related("item__chapter")
                .select_related("item__paragraph")
                .filter(item__chapter__id=chapter_pk)
                .filter(status__id__in=query_status)
                .order_by("item__id")
                .all()
            )
        else:
            comments = (
                current_phase.comments.select_related("status")
                .select_related("item")
                .select_related("item__chapter")
                .select_related("item__paragraph")
                .filter(item__chapter__id=chapter_pk)
                .filter(item__paragraph__id=paragraph_id)
                .filter(status__id__in=query_status)
                .order_by("item__id")
                .all()
            )
    if type == type_map["ACCEPTED_COMMENTS"]:
        if paragraph_id == has_paragraphs[False]:
            comments = (
                current_phase.accepted_comments.select_related("status")
                .select_related("item")
                .select_related("item__chapter")
                .select_related("item__paragraph")
                .filter(item__chapter__id=chapter_pk)
                .order_by("item__id")
                .all()
            )
        else:
            comments = (
                current_phase.accepted_comments.select_related("status")
                .select_related("item")
                .select_related("item__chapter")
                .select_related("item__paragraph")
                .filter(item__chapter__id=chapter_pk)
                .filter(item__paragraph__id=paragraph_id)
                .order_by("item__id")
                .all()
            )
    if type == type_map["TODO_COMMENTS"]:
        if paragraph_id == has_paragraphs[False]:
            comments = (
                current_phase.todo_comments.select_related("status")
                .select_related("item")
                .select_related("item__chapter")
                .select_related("item__paragraph")
                .filter(item__chapter__id=chapter_pk)
                .order_by("item__id")
                .all()
            )
        else:
            comments = (
                current_phase.todo_comments.select_related("status")
                .select_related("item")
                .select_related("item__chapter")
                .select_related("item__paragraph")
                .filter(item__chapter__id=chapter_pk)
                .filter(item__paragraph__id=paragraph_id)
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
def FirstAcceptStepPong(request, client_pk, project_pk, item_pk, type):
    # guard clauses to check if user is allowerd to comment
    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )
    
    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    # check last replier to see if user is allowed to accept the last reply 
    # (can't accept their own replies, the other party has to do that. You can however change your mind and disagree with your own comment)
    # here we fetch either the last reply or the last annotation if no replies exist
    if CommentReply.objects.filter(Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)).exists():
        last_reply = CommentReply.objects.filter(
            Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)
        ).order_by("-id").first()
    elif PVEItemAnnotation.objects.filter(
        project__id=project_pk, item__id=item_pk
    ).exists():
        last_reply = PVEItemAnnotation.objects.filter(
            project__id=project_pk, item__id=item_pk
        ).first()
        
    # check last reply for either client or stakeholder
    if last_reply.user.stakeholder:
        last_reply_organisation = last_reply.user.stakeholder
    elif last_reply.user.client:
        last_reply_organisation = last_reply.user.client
        
    # same with browsing user
    if request.user.stakeholder:
        current_reply_organisation = request.user.stakeholder
    elif request.user.client:
        current_reply_organisation = request.user.client
        
    context = {}
    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["type"] = type
    context["item_pk"] = item_pk
    context["last_reply_organisation"] = last_reply_organisation
    context["current_reply_organisation"] = current_reply_organisation
    return render(request, "partials/firstacceptsteppong.html", context)

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def DetailItemPong(request, client_pk, project_pk, item_pk, type):
    context = {}

    project, current_phase = passed_commentcheck_guardclauses(
        request, client_pk, project_pk
    )

    if not project:
        return redirect("logout_syn", client_pk=client_pk)

    item = project.item.filter(id=item_pk).first()

    itemAttachment = None
    if models.ItemBijlages.objects.filter(items__id=item.id).exists():
        itemAttachment = models.ItemBijlages.objects.filter(items__id=item.id).first()

    replies = None
    attachments = {}
    current_reply = None
    
    if CommentReply.objects.filter(onComment__item__id=item.id, commentphase__project__id=current_phase.project.id).exists():
        replies = CommentReply.objects.filter(
            Q(onComment__item__id=item_pk) & ~Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)
        ).order_by("id")

        current_reply = CommentReply.objects.filter(
            Q(onComment__item__id=item_pk) & Q(commentphase=current_phase) & Q(commentphase__project__id=current_phase.project.id)
        ).first()
        
        for reply in replies:
            if reply.attachmenttoreply.exists():
                attachments[reply.id] = reply.attachmenttoreply.all()
                                
    annotation = None
    if PVEItemAnnotation.objects.filter(
        project__id=project_pk, item__id=item.id
    ).exists():
        annotation = PVEItemAnnotation.objects.filter(
            project__id=project_pk, item__id=item.id
        ).first()

        annotationattachments = None
        if annotation.attachmentobject.exists():
            annotationattachments = annotation.attachmentobject.all()

    context["item"] = item
    context["itemAttachment"] = itemAttachment
    context["replies"] = replies
    context["current_reply"] = current_reply
    context["attachments"] = attachments
    context["annotation"] = annotation
    context["annotationattachments"] = annotationattachments
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
    attachments = None
    annotation = None
    if CommentReply.objects.filter(
        commentphase=current_phase, onComment__item__id=item_pk
    ).exists():
        reply = CommentReply.objects.filter(
            commentphase=current_phase, onComment__item__id=item_pk
        ).first()
        annotation = reply.onComment
        if reply.attachmenttoreply.exists():
            attachments = reply.attachmenttoreply.all()
    
    context["comment_allowed"] = False
    context["attachment_allowed"] = False
    
    # manual input as to what statuses allow comments / attachments    
    if reply:
        if reply.status:
            requirement_obj = CommentRequirement.objects.get(version__pk=project.pve_versie.pk)
            comment_allowed = [obj.status for obj in requirement_obj.comment_allowed.all()]
            attachment_allowed = [obj.status for obj in requirement_obj.attachment_allowed.all()]

            if reply.status.status in comment_allowed:
                context["comment_allowed"] = True
            if reply.status.status in attachment_allowed:
                context["attachment_allowed"] = True
        elif not reply.accept:
            context["comment_allowed"] = True
            context["attachment_allowed"] = True

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["reply"] = reply
    context["annotation"] = annotation
    context["current_reply"] = reply
    context["attachments"] = attachments
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

        if current_reply.attachment:
            current_reply.attachment = None
            attachmentobject = current_reply.attachmenttoreply.first()
            attachmentobject.delete()
        if current_reply.consequentCosts:
            current_reply.consequentCosts = None
        if current_reply.status:
            current_reply.status = None

        current_reply.save()
    else:
        current_reply = CommentReply.objects.create(
            commentphase=current_phase,
            user=request.user,
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
            user=request.user,
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

@login_required(login_url=reverse_lazy("login_syn", args={1,},))
def RedoCommentDetail(request, client_pk, project_pk, item_pk, type):
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
    context["annotation"] = annotation
    context["current_reply"] = current_reply
    context["type"] = type
    return render(request, "partials/firstacceptstepredo.html", context)


@login_required(login_url=reverse_lazy("login_syn", args={1,},))
def RedoCommentPong(request, client_pk, project_pk, item_pk, type):
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
        
    if current_reply.attachment:
        for attachment in current_reply.attachmenttoreply.all():
            attachment.delete()
    
    current_reply.delete()

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["item_pk"] = item_pk
    context["annotation"] = annotation
    context["type"] = type
    return render(request, "partials/detail_accept_pong.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def AddBijlagePong(request, client_pk, project_pk, item_pk, annotation_pk, type, new, attachment_id):
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
    if annotation_pk == exists[False] and not CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ):
        reply = CommentReply.objects.create(commentphase=current_phase, onComment=annotation, user=request.user)
        attachment_id = reply.id
    else:
        reply = CommentReply.objects.filter(
            onComment__id=annotation.id,
            onComment__item__id=item_pk,
            commentphase=current_phase,
        ).first()
    
    # seperate forms because we want to create a reply only once (GET)
    if BijlageToReply.objects.filter(id=attachment_id).exists() and new == exists[False] and attachment_id != exists[False]:
        attachmentmodel = BijlageToReply.objects.filter(id=attachment_id).first()
        form = forms.PongBijlageForm(
            request.POST or None, request.FILES or None, instance=attachmentmodel
        )
    else:
        form = forms.PongBijlageForm(
            request.POST or None, request.FILES or None, initial={"reply": reply}
        )
        
    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if form.cleaned_data["name"]: 
                if not BijlageToReply.objects.filter(name=form.cleaned_data["name"], reply__onComment__project=project).exists(): 
                    form.save()
                    reply.attachment = True
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
                    messages.warning(request, "Naam bestaat al voor een attachment in dit project. Kies een andere.")
            else:
                # else save and the attachment ID is the attachment name.
                form.save()
                reply.attachment = True
                reply.save()
                attachment = reply.attachmenttoreply.all().order_by("-id").first()
                attachment.name = attachment.id
                attachment.save()
                messages.warning(request, "Bijlage toegevoegd!")
                return redirect(
                    "detailpongreply",
                    client_pk=client_pk,
                    project_pk=project_pk,
                    item_pk=item_pk,
                    type=type,
                )
        else:
            messages.warning(request, "Fout met attachment toevoegen. Probeer het opnieuw.")

    context["client_pk"] = client_pk
    context["project_pk"] = project_pk
    context["annotation_pk"] = annotation_pk
    context["new"] = new
    context["item_pk"] = item_pk
    context["attachment_id"] = attachment_id
    context["type"] = type
    context["form"] = form
    context["annotation"] = annotation
    return render(request, "partials/form_attachment_pong.html", context)


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
    print(form)
    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if form.cleaned_data["status"] == annotation.status:
                messages.warning(request, "Kan niet veranderen naar dezelfde status.")
                return redirect(
                    "detailpongaccept",
                    client_pk=client_pk,
                    project_pk=project_pk,
                    item_pk=item_pk,
                    type=type,
                )

            if reply:
                requirement_obj = CommentRequirement.objects.get(version__pk=project.pve_versie.pk)
                comment_allowed = [obj.status for obj in requirement_obj.comment_allowed.all()]
                attachment_allowed = [obj.status for obj in requirement_obj.attachment_allowed.all()]

                if form.cleaned_data["status"] not in comment_allowed:
                    reply.comment = None
                if form.cleaned_data["status"] not in attachment_allowed:
                    reply.attachment = False
                    reply.attachmenttoreply.all().delete()
                    
                reply.status = form.cleaned_data["status"]
                
                reply.save()
            else:
                reply = CommentReply()
                reply.status = form.cleaned_data["status"]
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.user = request.user
                reply.save()

            messages.warning(request, "Status toegevoegd!")
            return redirect(
                "detailpongaccept",
                client_pk=client_pk,
                project_pk=project_pk,
                item_pk=item_pk,
                type=type,
            )
        else:
            messages.warning(request, "Vul een geldige status in.")
            return redirect(
                "detailpongaccept",
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
            request.POST or None, initial={"kostenverschil": reply.consequentCosts, "costtype": reply.costtype}
        )
    else:
        form = forms.FirstKostenverschilForm(request.POST or None)

    if request.method == "POST" or request.method == "PUT":
        if form.is_valid():
            if reply:
                reply.consequentCosts = form.cleaned_data["kostenverschil"]
                reply.costtype = form.cleaned_data["costtype"]
                reply.save()
            else:
                reply = CommentReply()
                reply.consequentCosts = form.cleaned_data["kostenverschil"]
                reply.costtype = form.cleaned_data["costtype"]
                reply.onComment = annotation
                reply.commentphase = current_phase
                reply.user = request.user
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
                reply.user = request.user
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
        
        # if reply is in tab 0
        if not reply.accept:
            if BijlageToReply.objects.filter(reply=reply):
                attachments = BijlageToReply.objects.filter(reply=reply)
                for attachment in attachments:
                    attachment.delete()
            
            reply.delete()
        else:
            reply.save()
            
        messages.warning(request, "Status verwijderd.")
        return redirect(
            "detailpongaccept",
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

        messages.warning(
            request,
            "Opmerking verwijderd.",
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
        reply.consequentCosts = None
        reply.costtype = None
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
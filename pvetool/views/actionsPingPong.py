from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from project.models import Project, PVEItemAnnotation, Beleggers
from pvetool.forms import FirstFreezeForm
from pvetool.models import CommentReply, FrozenComments, CommentRequirement
from pvetool.views.utils import GetAWSURL
from pvetool.views import hardcoded_values

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def FirstFreeze(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
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

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            if form.cleaned_data["confirm"]:
                requirement_obj = CommentRequirement.objects.get(version__pk=project.pve_versie.pk)
                
                changed_comments = project.annotation.select_related("item").all()

                # check if accepted comments have no attachments/comments
                # check if some statuses that require comments/attachments, have no comments/attachments yet
                false_comments = []
                
                for comment in changed_comments:
                    if comment.status:
                        # if new status and reply has no attachments/comment
                        if comment.status in requirement_obj.comment_allowed.all():
                            if not comment.annotation and not comment.attachmentobject.all():
                                false_comments.append(comment)
                    # if not accepted, no statuschange and no comments/attachments/cost change
                    else:
                        if not comment.annotation and not comment.attachment and not comment.consequentCosts:
                            false_comments.append(comment)
                
                # create a string of all false comment items
                if false_comments:

                    string_list = []
                    for comment in false_comments:
                        string = f"{comment.item.chapter.chapter}: "
                        
                        if comment.item.paragraph:
                            string += f"{comment.item.paragraph.paragraph}: "
                        
                        string += f"{comment.item.inhoud} "
                        string_list.append(string)

                    
                    messages.warning(request, f"""Een aantal regels met een opmerkingsplicht hebben nog geen opmerkingen. Check de volgende regels:
                                   {" / ".join([string for string in string_list])}.
                                   """)
                    
                    return redirect("plusopmerking_syn", client_pk=client_pk, pk=pk)

                # freeze opmerkingen op niveau 1
                project.frozenLevel = 1
                project.save()

                # create new frozen comments and the level to 1
                frozencomments = FrozenComments()
                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()
                
                changed_items_ids = [comment.item.id for comment in changed_comments]
                unchanged_items = project.item.exclude(id__in=changed_items_ids)
                # add all initially changed comments to it
                frozencomments.comments.add(*changed_comments)

                comment_list = [
                    PVEItemAnnotation(
                        project=project,
                        item=item,
                        user=request.user,
                        init_accepted=True,
                    )
                    for item in unchanged_items
                ]

                PVEItemAnnotation.objects.bulk_create(comment_list)
                frozencomments.todo_comments.add(*comment_list)

                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()

                if project.first_annotate == "SOG":
                    allprojectusers = project.permitted.all()
                    filteredDerden = [
                        user.email for user in allprojectusers if user.type_user == "SD"
                    ]
                    send_mail(
                        f"{ project.client.name } Projecten - Uitnodiging opmerkingscheck voor project {project}",
                        f"""{ request.user } heeft de initiele statussen van de PvE-regels ingevuld en nodigt u uit deze te checken voor het project { project } van { project.client.name }.
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/pvetool/{project.client.id}/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        filteredDerden,
                        fail_silently=False,
                    )

                    messages.warning(
                        request,
                        f"Uitnodiging voor opmerkingen checken verstuurd naar de derden {', '.join(filteredDerden)} via email.",
                    )
                else:
                    projectmanager = project.projectmanager
                    send_mail(
                        f"{ project.client.name } Projecten - Uitnodiging opmerkingscheck voor project {project}",
                        f"""{ request.user } heeft de initiele statussen van de PvE-regels ingevuld en nodigt u uit deze te checken voor het project { project } van { project.client.name }.
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/pvetool/{project.client.id}/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        [f"{projectmanager.email}"],
                        fail_silently=False,
                    )

                    messages.warning(
                        request,
                        f"Uitnodiging voor opmerkingen checken verstuurd naar de projectmanager {projectmanager.username} via email.",
                    )

                return redirect("viewproject_syn", client_pk=client_pk, pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = FirstFreezeForm()
    context["pk"] = pk
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "FirstFreeze.html", context)
    

@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def SendReplies(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
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

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__iregex=r"\y{0}\y".format(request.user.username)
        ).exists():
            raise Http404("404")

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            if form.cleaned_data["confirm"]:
                commentphase = (
                    FrozenComments.objects.filter(project=project)
                    .prefetch_related("accepted_comments")
                    .order_by("-level")
                    .first()
                )
                
                comments = (
                    CommentReply.objects.select_related("onComment").select_related("onComment__item").select_related("onComment__item__chapter").select_related("onComment__item__paragraph")
                    .select_related("status")
                    .filter(commentphase=commentphase)
                )
                # check if accepted comments have no attachments/comments
                # check if some statuses that require comments/attachments, have no comments/attachments yet
                false_comments = []
                
                for comment in comments:
                    if not comment.accept:
                        if comment.status:
                            # if new status and reply has no attachments/comment
                            if comment.status.status in hardcoded_values.allowed_comments():
                                if not comment.comment and not comment.attachmenttoreply.all():
                                    false_comments.append(comment)
                        # if not accepted, no statuschange and no comments/attachments/cost change
                        else:
                            if not comment.comment and not comment.attachment and not comment.consequentCosts:
                                false_comments.append(comment)
                    # if accepted, and reply has comment/attachment/changedstatus (for the hackers out there)
                    else:
                        if comment.comment or comment.attachment or comment.status:
                            false_comments.append(comment)
                            
                if false_comments:

                    string_list = []
                    for comment in false_comments:
                        string = f"{comment.onComment.item.chapter.chapter}: "
                        
                        if comment.onComment.item.paragraph:
                            string += f"{comment.onComment.item.paragraph.paragraph}: "
                        
                        string += f"{comment.onComment.item.inhoud} "
                        string_list.append(string)

                    
                    messages.warning(request, f"""Een aantal regels met een opmerkingsplicht hebben nog geen opmerkingen. Check de volgende regels:
                                   {" / ".join([string for string in string_list])}.
                                   """)
                    
                    return redirect("commentscheck_syn", client_pk=client_pk, proj_id=pk)

                project.frozenLevel = project.frozenLevel + 1
                project.save()

                current_accepted_comments_ids = [
                    comment.id for comment in commentphase.accepted_comments.all()
                ]
                # create a new phase with 1 higher level
                new_phase = FrozenComments()
                new_phase.level = commentphase.level + 1
                new_phase.project = project
                new_phase.save()

                # split comments in previously accepted and non accepted
                non_accepted_comments_ids = []
                accepted_comment_ids = []
                todo_comment_ids = []
                total_comments_ids = []

                comments = (
                    CommentReply.objects.select_related("onComment")
                    .select_related("status")
                    .filter(commentphase=commentphase)
                )

                for comment in comments:
                    if comment.accept == True:
                        accepted_comment_ids.append(comment.onComment.id)
                    if comment.accept == False:
                        non_accepted_comments_ids.append(comment.onComment.id)

                    # change original comments status if reply has it
                    if comment.status:
                        original_comment = comment.onComment
                        original_comment.status = comment.status
                        original_comment.save()

                    # add costs to original comment if reply has it.
                    if comment.consequentCosts:
                        original_comment = comment.onComment
                        original_comment.consequentCosts = (
                            comment.consequentCosts
                        )
                        original_comment.save()

                    total_comments_ids.append(comment.onComment.id)

                # for the rest of the items without reply, if no status it is todo, if it has a status it doesnt change tabs
                non_reacted_comments = project.annotation.select_related(
                    "status"
                ).exclude(id__in=total_comments_ids)

                for comment in non_reacted_comments:
                    if comment.id not in current_accepted_comments_ids:
                        if not comment.status:
                            todo_comment_ids.append(comment.id)
                        else:
                            non_accepted_comments_ids.append(comment.id)
                    else:
                        accepted_comment_ids.append(comment.id)

                # add all the comments and divide up into accepted or non accepted or todo
                new_phase.comments.add(*non_accepted_comments_ids)
                new_phase.accepted_comments.add(*accepted_comment_ids)
                new_phase.todo_comments.add(*todo_comment_ids)

                if request.user.type_user == "SOG":
                    allprojectusers = project.permitted.all()
                    filteredDerden = [
                        user.email for user in allprojectusers if user.type_user == "SD"
                    ]
                    send_mail(
                        f"{ project.client.name } Projecten - Reactie van opmerkingen op PvE ontvangen voor project {project}",
                        f"""U heeft reactie ontvangen van de opmerkingen van de projectmanager voor project {project}
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/pvetool/{project.client.id}/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        filteredDerden,
                        fail_silently=False,
                    )
                    messages.warning(
                        request,
                        f"Opmerkingen doorgestuurd naar de derden. De ontvangers {', '.join(filteredDerden)}, hebben een e-mail ontvangen om uw opmerkingen te checken.",
                    )
                elif request.user.type_user == "SD":
                    projectmanager = project.projectmanager

                    send_mail(
                        f"{ project.client.name } Projecten - Reactie van opmerkingen op PvE ontvangen voor project {project}",
                        f"""U heeft reactie ontvangen van de opmerkingen van de derde partijen voor project {project}
                        
                        Klik op de link om rechtstreeks de opmerkingen te checken.
                        Link: https://pvegenerator.net/pvetool/{project.client.id}/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        [f"{projectmanager.email}"],
                        fail_silently=False,
                    )

                    messages.warning(
                        request,
                        f"Opmerkingen doorgestuurd naar de projectmanager {projectmanager.username}. De ontvanger heeft een e-mail ontvangen om uw opmerkingen te checken.",
                    )
                return redirect("viewproject_syn", client_pk=client_pk, pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = FirstFreezeForm(request.POST)
    context["pk"] = pk
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    # set Nieuwe Statussen as the status of PVEItemannotations
    return render(request, "SendReplies.html", context)


@login_required(login_url=reverse_lazy("login_syn",  args={1,},))
def FinalFreeze(request, client_pk, pk):
    if not Beleggers.objects.filter(pk=client_pk).exists():
        return redirect("logout_syn", client_pk=client_pk)

    client = Beleggers.objects.filter(pk=client_pk).first()
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

    project = get_object_or_404(Project, id=pk)

    if project.client != client:
        return redirect("logout_syn", client_pk=client_pk)

    if project.frozenLevel == 0:
        return redirect("logout_syn", client_pk=client_pk)

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__iregex=r"\y{0}\y".format(request.user.username)
        ).exists():
            raise Http404("404")

    commentphase = project.phase.all()

    # test if all comments accepted
    frozencomments_accepted = commentphase.first().accepted_comments.count()
    frozencomments_todo = commentphase.first().todo_comments.count()
    frozencomments_total = (
        frozencomments_todo
        + frozencomments_accepted
        + commentphase.first().comments.count()
    )
    
    if frozencomments_accepted != frozencomments_total and frozencomments_todo == 0:
        return redirect("logout_syn", client_pk=client_pk)

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            project.fullyFrozen = True
            project.save()

            allprojectusers = project.permitted.all()
            filteredDerden = [
                user.email for user in allprojectusers if user.type_user == "SD"
            ]
            send_mail(
                f"{ project.client.name } Projecten - Project {project} is bevroren, download het PvE",
                f"""Alle regels in het project {project} zijn akkoord mee gegaan en de projectmanager heeft het project afgesloten.
                
                Klik op de link om het PvE met alle opmerkingen en attachments te downloaden.
                Link: https://pvegenerator.net/pvetool/{project.client.id}/project/{project.id}/pve
                """,
                "admin@pvegenerator.net",
                filteredDerden,
                fail_silently=False,
            )
            projectmanager = project.projectmanager

            send_mail(
                f"{ project.client.name } Projecten - Project {project} is bevroren, download het PvE",
                f"""Beste { projectmanager.username },
                
                Alle regels in het project {project} zijn akkoord mee gegaan en de projectmanager heeft het project afgesloten.
                
                Klik op de link om het PvE met alle opmerkingen en attachments te downloaden.
                Link: https://pvegenerator.net/pvetool/{project.client.id}/project/{project.id}/pve
                """,
                "admin@pvegenerator.net",
                [f"{projectmanager.email}"],
                fail_silently=False,
            )

            messages.warning(
                request,
                f"Het project {project.name} is succesvol bevroren. Er kunnen geen opmerkingen worden geplaatst en het uiteindelijke PvE is te downloaden via de projectpagina. Alle medewerkers van dit project hebben een E-Mail ontvangen van de downloadlink van het PvE.",
            )
        else:
            messages.warning(request, "Vul de verplichte velden in.")

        return redirect("viewproject_syn", client_pk=client_pk, pk=pk)

    context = {}
    context["form"] = FirstFreezeForm()
    context["pk"] = project.id
    context["project"] = project
    context["client_pk"] = client_pk
    context["client"] = client
    context["logo_url"] = logo_url
    return render(request, "FinalFreeze.html", context)

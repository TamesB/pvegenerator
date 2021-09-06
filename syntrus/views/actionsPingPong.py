from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from app import models
from project.models import Project, PVEItemAnnotation
from syntrus.forms import FirstFreezeForm
from syntrus.models import CommentReply, FrozenComments

@login_required(login_url="login_syn")
def FirstFreeze(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user.type_user != project.first_annotate:
        return render(request, "404_syn.html")

    if request.method == "POST":
        form = FirstFreezeForm(request.POST)

        if form.is_valid():
            if form.cleaned_data["confirm"]:
                # freeze opmerkingen op niveau 1
                project.frozenLevel = 1
                project.save()

                # create new frozen comments and the level to 1
                frozencomments = FrozenComments()
                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()
                changed_comments = project.annotation.select_related("item").all()


                changed_items_ids = [comment.item.id for comment in changed_comments]
                unchanged_items = project.item.exclude(id__in=changed_items_ids)
                # add all initially changed comments to it
                for comment in changed_comments:
                    frozencomments.comments.add(comment)

                # create todo pveannotations for ignored items, change to bulk_create for optimization
                for item in unchanged_items:
                    comment = PVEItemAnnotation()
                    comment.project = project
                    comment.item = item
                    comment.gebruiker = request.user
                    comment.init_accepted = True
                    comment.save()

                    frozencomments.todo_comments.add(comment)

                frozencomments.project = project
                frozencomments.level = 1
                frozencomments.save()
                if project.first_annotate == "SOG":
                    allprojectusers = project.permitted.all()
                    filteredDerden = [
                        user.email for user in allprojectusers if user.type_user == "SD"
                    ]
                    send_mail(
                        f"Syntrus Projecten - Uitnodiging opmerkingscheck voor project {project}",
                        f"""{ request.user } heeft de initiele statussen van de PvE-regels ingevuld en nodigt u uit deze te checken voor het project { project } van Syntrus.
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}/check
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
                        f"Syntrus Projecten - Uitnodiging opmerkingscheck voor project {project}",
                        f"""{ request.user } heeft de initiele statussen van de PvE-regels ingevuld en nodigt u uit deze te checken voor het project { project } van Syntrus.
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        [f"{projectmanager.email}"],
                        fail_silently=False,
                    )

                    messages.warning(
                        request,
                        f"Uitnodiging voor opmerkingen checken verstuurd naar de projectmanager {projectmanager.naam} via email.",
                    )

                return redirect("viewproject_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = FirstFreezeForm(request.POST)
    context["pk"] = pk
    context["project"] = project
    return render(request, "FirstFreeze.html", context)


@login_required
def SendReplies(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

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
                project.frozenLevel = project.frozenLevel + 1
                project.save()

                commentphase = (
                    FrozenComments.objects.filter(project=project)
                    .order_by("-level")
                    .first()
                )

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
                    if comment.accept:
                        accepted_comment_ids.append(comment.onComment.id)
                    else:
                        non_accepted_comments_ids.append(comment.onComment.id)

                    # change original comments status if reply has it
                    if comment.status:
                        original_comment = comment.onComment
                        original_comment.status = comment.status
                        original_comment.save()

                    # add costs to original comment if reply has it.
                    if comment.kostenConsequenties:
                        original_comment = comment.onComment
                        original_comment.kostenConsequenties = (
                            comment.kostenConsequenties
                        )
                        original_comment.save()

                    total_comments_ids.append(comment.onComment.id)

                # for the rest of the items without reply, if no status it is todo, if it has a status its automatically accepted
                non_reacted_comments = project.annotation.select_related("status").exclude(id__in=total_comments_ids)

                for comment in non_reacted_comments:
                    if not comment.status:
                        todo_comment_ids.append(comment.id)
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
                        f"Syntrus Projecten - Reactie van opmerkingen op PvE ontvangen voor project {project}",
                        f"""U heeft reactie ontvangen van de opmerkingen van de projectmanager voor project {project}
                        
                        Klik op de link om rechtstreeks de statussen langs te gaan.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}/check
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
                        f"Syntrus Projecten - Reactie van opmerkingen op PvE ontvangen voor project {project}",
                        f"""U heeft reactie ontvangen van de opmerkingen van de derde partijen voor project {project}
                        
                        Klik op de link om rechtstreeks de opmerkingen te checken.
                        Link: https://pvegenerator.net/syntrus/project/{project.id}/check
                        """,
                        "admin@pvegenerator.net",
                        [f"{projectmanager.email}"],
                        fail_silently=False,
                    )

                    messages.warning(
                        request,
                        f"Opmerkingen doorgestuurd naar de projectmanager {projectmanager.username}. De ontvanger heeft een e-mail ontvangen om uw opmerkingen te checken.",
                    )
                return redirect("viewproject_syn", pk=project.id)
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = {}
    context["form"] = FirstFreezeForm(request.POST)
    context["pk"] = pk
    context["project"] = project
    # set Nieuwe Statussen as the status of PVEItemannotations
    return render(request, "SendReplies.html", context)


@login_required
def FinalFreeze(request, pk):
    project = get_object_or_404(Project, id=pk)

    if project.frozenLevel == 0:
        return render(request, "404_syn.html")

    # check if user is authorized to project
    if request.user.type_user != "B":
        if not Project.objects.filter(
            id=pk, permitted__username__iregex=r"\y{0}\y".format(request.user.username)
        ).exists():
            raise Http404("404")

    commentphase = project.phase.all()

    # check if the current commentphase has everything accepted
    if commentphase.comments or commentphase.todo_comments:
        raise Http404("404")

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
                f"Syntrus Projecten - Project {project} is bevroren, download het PvE",
                f"""Alle regels in het project {project} zijn akkoord mee gegaan en de projectmanager heeft het project afgesloten.
                
                Klik op de link om het PvE met alle opmerkingen en bijlages te downloaden.
                Link: https://pvegenerator.net/syntrus/project/{project.id}/pve
                """,
                "admin@pvegenerator.net",
                filteredDerden,
                fail_silently=False,
            )
            projectmanager = project.projectmanager

            send_mail(
                f"Syntrus Projecten - Project {project} is bevroren, download het PvE",
                f"""Alle regels in het project {project} zijn akkoord mee gegaan en de projectmanager heeft het project afgesloten.
                
                Klik op de link om het PvE met alle opmerkingen en bijlages te downloaden.
                Link: https://pvegenerator.net/syntrus/project/{project.id}/pve
                """,
                "admin@pvegenerator.net",
                [f"{projectmanager.email}"],
                fail_silently=False,
            )

            messages.warning(
                request,
                f"Het project {project.naam} is succesvol bevroren. Er kunnen geen opmerkingen worden geplaatst en het uiteindelijke PvE is te downloaden via de projectpagina. Alle medewerkers van dit project hebben een E-Mail ontvangen van de downloadlink van het PvE.",
            )
        else:
            messages.warning(request, "Vul de verplichte velden in.")

    context = []
    context["form"] = FirstFreezeForm()
    context["pk"] = project.id
    context["project"] = project
    return render(request, "FinalFreeze.html", context)

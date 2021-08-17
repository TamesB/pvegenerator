
from django.db import models

from project.models import Project, PVEItemAnnotation
from users.models import CustomUser


class Room(models.Model):
    """Represents chat rooms that users can join"""

    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)

    def __str__(self):
        """Returns human-readable representation of the model instance."""
        return self.name


class CommentStatus(models.Model):
    status = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.status}"


class FAQ(models.Model):
    type_choices = (
        ("B", "Beheerder"),
        ("SB", "Syntrus Beheerder"),
        ("SOG", "Syntrus Projectmanager"),
        ("SD", "Syntrus Derden"),
    )

    gebruikersrang = models.CharField(max_length=3, choices=type_choices, default="SD")

    vraag = models.CharField(max_length=500)
    antwoord = models.TextField(max_length=5000)

    def __str__(self):
        return f"{self.vraag}"


# Sets the phase of the frozencomments with which comments still need to be accepted
class FrozenComments(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    level = models.IntegerField(default=1, blank=True, null=True)
    comments = models.ManyToManyField(PVEItemAnnotation)
    accepted_comments = models.ManyToManyField(
        PVEItemAnnotation, related_name="accepted_comments"
    )
    todo_comments = models.ManyToManyField(
        PVEItemAnnotation, related_name="todo_comments"
    )

    def __str__(self):
        return f"Level: {self.level}, Project: {self.project}"


# places a comment on the comment, allocates it to a specific commentphase (records it all)
class CommentReply(models.Model):
    commentphase = models.ForeignKey(
        FrozenComments, on_delete=models.CASCADE, null=True
    )
    onComment = models.ForeignKey(
        PVEItemAnnotation, on_delete=models.CASCADE, null=True
    )
    comment = models.TextField(max_length=1000, default=None, null=True)
    accept = models.BooleanField(default=False, blank=True, null=True)
    bijlage = models.BooleanField(default=False, blank=True, null=True)
    kostenConsequenties = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=None
    )
    status = models.ForeignKey(
        CommentStatus, on_delete=models.CASCADE, null=True, blank=True
    )
    gebruiker = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=True, blank=True
    )
    datum = models.DateTimeField(auto_now=True)

class BijlageToReply(models.Model):
    reply = models.ForeignKey(CommentReply, on_delete=models.CASCADE, default=None)
    bijlage = models.FileField(blank=True, null=True, upload_to="OpmerkingBijlages/")
    naam = models.CharField(max_length=100, blank=True, null=True)

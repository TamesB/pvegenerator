
from django.db import models

from project.models import Project, PVEItemAnnotation, CostType
from users.models import CustomUser
from app.models import PVEVersie

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
        ("SB", "PVETool Beheerder"),
        ("SOG", "PVETool Projectmanager"),
        ("SD", "PVETool Derden"),
    )

    usersrank = models.CharField(max_length=3, choices=type_choices, default="SD")

    vraag = models.CharField(max_length=500)
    antwoord = models.TextField(max_length=5000)

    def __str__(self):
        return f"{self.vraag}"


# Sets the phase of the frozencomments with which comments still need to be accepted
class FrozenComments(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, related_name='phase')
    level = models.IntegerField(default=1, blank=True, null=True)
    comments = models.ManyToManyField(PVEItemAnnotation, related_name='phase_comments')
    accepted_comments = models.ManyToManyField(
        PVEItemAnnotation, related_name="phase_accept"
    )
    todo_comments = models.ManyToManyField(
        PVEItemAnnotation, related_name="phase_todo"
    )

    def __str__(self):
        return f"Level: {self.level}, Project: {self.project}"

    class Meta:
        ordering = ['-level']

# places a comment on the comment, allocates it to a specific commentphase (records it all)
class CommentReply(models.Model):
    commentphase = models.ForeignKey(
        FrozenComments, on_delete=models.CASCADE, null=True, related_name='reply'
    )
    onComment = models.ForeignKey(
        PVEItemAnnotation, on_delete=models.CASCADE, null=True, related_name='reply'
    )
    comment = models.TextField(max_length=1000, default=None, null=True)
    accept = models.BooleanField(default=False, blank=True, null=True)
    attachment = models.BooleanField(default=False, blank=True, null=True)
    consequentCosts = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=None
    )
    costtype = models.ForeignKey(CostType, on_delete=models.SET_NULL, blank=True, null=True, related_name='reply')
    status = models.ForeignKey(
        CommentStatus, on_delete=models.SET_NULL, null=True, blank=True, related_name='reply'
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name="reply"
    )
    date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

class BijlageToReply(models.Model):
    reply = models.ForeignKey(CommentReply, on_delete=models.CASCADE, default=None, related_name="attachmenttoreply")
    attachment = models.FileField(blank=True, null=True, upload_to="OpmerkingBijlages/")
    name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    
class CommentRequirement(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.SET_NULL, null=True)
    comment_allowed = models.ManyToManyField(CommentStatus, related_name="comment_allowed")
    comment_required = models.ManyToManyField(CommentStatus, related_name="comment_required")
    attachment_allowed = models.ManyToManyField(CommentStatus, related_name="attachment_allowed")
    attachment_required = models.ManyToManyField(CommentStatus, related_name="attachment_required", blank=True)
    costs_allowed = models.ManyToManyField(CommentStatus, related_name="costs_allowed")
    costs_required = models.ManyToManyField(CommentStatus, related_name="costs_required")
    
    def __str__(self):
        return f"CommentRequirements: {self.version}"
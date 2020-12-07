from django.db import models
from users.models import CustomUser
from project.models import Project, PVEItemAnnotation
import datetime

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
        ('B', 'Beheerder'),
        ('SB', 'Syntrus Beheerder'),
        ('SOG', 'Syntrus Projectmanager'),
        ('SD', 'Syntrus Derden'),
    )

    gebruikersrang = models.CharField(max_length=3,
                                 choices=type_choices,
                                 default='SD')

    vraag = models.CharField(max_length=500)
    antwoord = models.TextField(max_length=5000)

    def __str__(self):
        return f"{self.vraag}"    


# Sets the phase of the frozencomments with which comments still need to be accepted
class FrozenComments(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    level = models.IntegerField(default=1, blank=True, null=True)
    comments = models.ManyToManyField(PVEItemAnnotation)

    def __str__(self):
        return f"{self.level}, {self.project}: {self.comments}"

# places a comment on the comment, allocates it to a specific commentphase (records it all)
class CommentReply(models.Model):
    commentphase = models.ForeignKey(FrozenComments, on_delete=models.CASCADE, null=True)
    onComment = models.ForeignKey(PVEItemAnnotation, on_delete=models.CASCADE, null=True)
    comment = models.TextField(max_length=1000, default=None, null=True)
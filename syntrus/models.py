from django.db import models
from users.models import CustomUser
from project.models import Project
import datetime

class Room(models.Model):
    """Represents chat rooms that users can join"""
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)

    def __str__(self):
        """Returns human-readable representation of the model instance."""
        return self.name


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
# Author: Tames Boon

from django.db import models

from project.models import Beleggers
from django.db.models.signals import pre_save
from django.dispatch import receiver
import inspect

from users.models import CustomUser
class PVEVersie(models.Model):
    client = models.ForeignKey(Beleggers, on_delete=models.SET_NULL, null=True, related_name='version')
    version = models.CharField(max_length=50, null=True, blank=True)
    public = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"{self.client}: Versie {self.version}"
    class Meta:
        ordering = ['id']


class ActieveVersie(models.Model):
    client = models.ForeignKey(Beleggers, on_delete=models.SET_NULL, null=True, related_name='actieve_versie')
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, related_name='actieve_versie')

    def __str__(self):
        return f"{self.client}: Versie {self.version.version}"
    class Meta:
        ordering = ['id']


class Bouwsoort(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name='bouwsoort')
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter
    class Meta:
        ordering = ['id']


class TypeObject(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="typeobject")
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter
    class Meta:
        ordering = ['id']


class Doelgroep(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="doelgroep")
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter
    class Meta:
        ordering = ['id']

class PVEOnderdeel(models.Model):
    # ALG/TO
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']

class PVEHoofdstuk(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="chapter")

    onderdeel = models.ForeignKey(
        PVEOnderdeel, on_delete=models.CASCADE, default=1, null=True, related_name="chapter"
    )
    chapter = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.chapter}"
    class Meta:
        ordering = ["id"]

class PVEParagraaf(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="paragraph")

    chapter = models.ForeignKey(PVEHoofdstuk, on_delete=models.CASCADE, default=1, related_name="paragraph")
    paragraph = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        if self.paragraph:
            return f"{self.paragraph}"
        else:
            return f"{self.chapter.chapter}"

    class Meta:
        ordering = ['id']

class PVEItem(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="item")

    chapter = models.ForeignKey(PVEHoofdstuk, on_delete=models.CASCADE, default=1, related_name="item")
    paragraph = models.ForeignKey(
        PVEParagraaf, on_delete=models.CASCADE, blank=True, null=True, related_name="item"
    )
    inhoud = models.TextField(max_length=5000)

    basisregel = models.BooleanField(default=False)
    Bouwsoort = models.ManyToManyField(Bouwsoort, blank=True, related_name="item")
    TypeObject = models.ManyToManyField(TypeObject, blank=True, related_name="item")
    Doelgroep = models.ManyToManyField(Doelgroep, blank=True, related_name="item")

    Smarthome = models.BooleanField(default=False)
    AED = models.BooleanField(default=False)
    EntreeUpgrade = models.BooleanField(default=False)
    Pakketdient = models.BooleanField(default=False)
    JamesConcept = models.BooleanField(default=False)

    projects = models.ManyToManyField("project.Project", blank=True, related_name="item")

    def __str__(self):
        return f"{self.inhoud}"
    class Meta:
        ordering = ['id']

class ItemBijlages(models.Model):
    version = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="itemAttachment")
    items = models.ManyToManyField(PVEItem, blank=True, related_name="itemAttachment")
    attachment = models.FileField(blank=True, null=True, upload_to="BasisBijlages")
    name = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    class Meta:
        ordering = ['id']

class Activity(models.Model):
    types = (
        ("P", "Project"), 
        ("K", "Klant"), 
        ("PvE", "PvE"),
    )

    activity_type = models.CharField(max_length=5, choices=types, blank=True, null=True)
    update = models.CharField(max_length=500, blank=True, null=True)
    date = models.DateTimeField(auto_now=True)
    schuldige = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.activity_type}: {self.update}. date: {self.date}"

    class Meta:
        ordering = ['-date']

@receiver(pre_save, sender=PVEVersie)
def on_change(sender, instance: PVEVersie, **kwargs):

    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break
        else:
            request = None

    # sender is the object being saved
    activity = Activity()
    activity.activity_type = "PvE"
    if not request.user.is_anonymous:
        activity.schuldige = request.user
    activity.save()
    
    if instance.id is None: # new object will be created
        activity.update = f"Nieuwe PvE version { instance.version } van client { instance.client }."
    else:
        previous = PVEVersie.objects.get(id=instance.id)
        if previous.version != instance.version: # field will be updated
            activity.update = f"{ previous.version } name veranderd naar { instance.version } van client { instance.client }."
        if previous.public != instance.public: # field will be updated
            if instance.public == True:
                activatie = "geactiveerd"
            else:
                activatie = "gedeactiveerd"

            activity.update = f"{ instance.version } van client { instance.client } { activatie }."
    
    activity.save()
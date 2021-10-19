# Author: Tames Boon

from django.db import models

from project.models import Beleggers


class PVEVersie(models.Model):
    belegger = models.ForeignKey(Beleggers, on_delete=models.SET_NULL, null=True, related_name='versie')
    versie = models.CharField(max_length=50, null=True, blank=True)
    public = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"{self.belegger}: Versie {self.versie}"
    class Meta:
        ordering = ['id']


class ActieveVersie(models.Model):
    belegger = models.ForeignKey(Beleggers, on_delete=models.SET_NULL, null=True, related_name='actieve_versie')
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, related_name='actieve_versie')

    def __str__(self):
        return f"{self.belegger}: Versie {self.versie.versie}"
    class Meta:
        ordering = ['id']


class Bouwsoort(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name='bouwsoort')
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter
    class Meta:
        ordering = ['id']


class TypeObject(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="typeobject")
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter
    class Meta:
        ordering = ['id']


class Doelgroep(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="doelgroep")
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter
    class Meta:
        ordering = ['id']


class PVEOnderdeel(models.Model):
    # ALG/TO
    naam = models.CharField(max_length=256)

    def __str__(self):
        return self.naam

    class Meta:
        ordering = ['id']

class PVEHoofdstuk(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="hoofdstuk")

    onderdeel = models.ForeignKey(
        PVEOnderdeel, on_delete=models.CASCADE, default=1, null=True, related_name="hoofdstuk"
    )
    hoofdstuk = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.hoofdstuk}"
    class Meta:
        ordering = ["id"]

class PVEParagraaf(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="paragraaf")

    hoofdstuk = models.ForeignKey(PVEHoofdstuk, on_delete=models.CASCADE, default=1, related_name="paragraaf")
    paragraaf = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        if self.paragraaf:
            return f"{self.paragraaf}"
        else:
            return f"{self.hoofdstuk.hoofdstuk}"

    class Meta:
        ordering = ['id']

class PVEItem(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="item")

    hoofdstuk = models.ForeignKey(PVEHoofdstuk, on_delete=models.CASCADE, default=1, related_name="item")
    paragraaf = models.ForeignKey(
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
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True, related_name="itembijlage")
    items = models.ManyToManyField(PVEItem, blank=True, related_name="itembijlage")
    bijlage = models.FileField(blank=True, null=True, upload_to="BasisBijlages")
    naam = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.naam}"
    class Meta:
        ordering = ['id']

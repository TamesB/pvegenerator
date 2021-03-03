# Author: Tames Boon

from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.upload_rename import upload_to
from project.models import Beleggers

class PVEVersie(models.Model):
    belegger = models.ForeignKey(Beleggers, on_delete=models.CASCADE)
    versie = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.belegger}: Versie {self.versie}"
    
class ActieveVersie(models.Model):
    belegger = models.ForeignKey(Beleggers, on_delete=models.CASCADE)
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.belegger}: Versie {self.versie.versie}"
    

class Bouwsoort(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True)
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter

class TypeObject(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True)
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter

class Doelgroep(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True)
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter

class PVEOnderdeel(models.Model):
    # ALG/TO
    naam = models.CharField(max_length=256)

    def __str__(self):
        return self.naam

class PVEHoofdstuk(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True)

    onderdeel = models.ForeignKey(
                        PVEOnderdeel, on_delete=models.CASCADE, default=1, null=True
                        )
    hoofdstuk = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.hoofdstuk}"

class PVEParagraaf(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True)

    hoofdstuk = models.ForeignKey(
                        PVEHoofdstuk, on_delete=models.CASCADE, default=1
                        )
    paragraaf = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        if self.paragraaf:
            return f"{self.paragraaf}"
        else:
            return f"{self.hoofdstuk.hoofdstuk}"

class PVEItem(models.Model):
    versie = models.ForeignKey(PVEVersie, on_delete=models.CASCADE, null=True)

    hoofdstuk = models.ForeignKey(PVEHoofdstuk, on_delete=models.CASCADE, default=1)
    paragraaf = models.ForeignKey(PVEParagraaf, on_delete=models.CASCADE, blank=True, null=True)
    inhoud = models.TextField(max_length=5000)
    bijlage = models.FileField(blank=True, null=True, upload_to='BasisBijlages')

    basisregel = models.BooleanField(default=False)
    Bouwsoort = models.ManyToManyField(Bouwsoort, blank=True)
    TypeObject = models.ManyToManyField(TypeObject, blank=True)
    Doelgroep = models.ManyToManyField(Doelgroep, blank=True)

    Smarthome = models.BooleanField(default=False)
    AED = models.BooleanField(default=False)
    EntreeUpgrade = models.BooleanField(default=False)
    Pakketdient = models.BooleanField(default=False)
    JamesConcept = models.BooleanField(default=False)
    
    projects = models.ManyToManyField('project.Project', blank=True)

    def __str__(self):
        return f"{self.inhoud}"
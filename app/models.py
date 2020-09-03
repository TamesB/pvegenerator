# Author: Tames Boon

from django.db import models
from django.contrib.auth.models import AbstractUser

class Bouwsoort(models.Model):
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter

class TypeObject(models.Model):
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter

class Doelgroep(models.Model):
    parameter = models.CharField(max_length=256)

    def __str__(self):
        return self.parameter

class PVEOnderdeel(models.Model):
    # ALG/TO
    naam = models.CharField(max_length=256)

    def __str__(self):
        return self.naam

class PVEHoofdstuk(models.Model):
    onderdeel = models.ForeignKey(
                        PVEOnderdeel, on_delete=models.CASCADE, default=1
                        )
    hoofdstuk = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.hoofdstuk}"

class PVEParagraaf(models.Model):
    hoofdstuk = models.ForeignKey(
                        PVEHoofdstuk, on_delete=models.CASCADE, default=1
                        )
    paragraaf = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        if self.paragraaf:
            return f"{self.paragraaf}"
        else:
            return f"{self.hoofdstuk.hoofdstuk}"

class PVESubparagraaf(models.Model):
    sectie = models.ForeignKey(
                        PVEParagraaf, on_delete=models.CASCADE, default=1
                        )

    subparagraaf = models.CharField(max_length=256, blank=True, null=True)
    bijlage = models.FileField(blank=True, null=True)

    def __str__(self):
        return self.subparagraaf

class PVEItem(models.Model):
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
        if self.paragraaf:
            return f"Item: {self.id}, Paragraaf: {self.paragraaf}"
        
        return f"Item: {self.id}, Hoofdstuk: {self.hoofdstuk}"
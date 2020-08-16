from django.db import models
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis import forms
        
class ContractStatus(models.Model):
    contrstatus = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.contrstatus}"

# Create your models here.
class Project(models.Model):
    nummer = models.FloatField(max_length=100, default=None)
    naam = models.CharField(max_length=500, default=None)
    plaats = models.PointField()
    plaatsnamen = models.CharField(max_length=250, default=None, null=True)
    vhe = models.FloatField(max_length=100, default=None)
    pensioenfonds = models.CharField(max_length=100, default=None)
    statuscontract = models.ForeignKey(ContractStatus, on_delete=models.CASCADE)
    datum = models.DateTimeField(auto_now=True)

    permitted = models.ManyToManyField('users.CustomUser', default=None)
    pveconnected = models.BooleanField(blank=True, null=True, default=False)

    bouwsoort1 = models.ForeignKey('app.Bouwsoort', on_delete=models.CASCADE, default=None, null=True)
    typeObject1 = models.ForeignKey('app.TypeObject', on_delete=models.CASCADE, default=None, null=True)
    doelgroep1 = models.ForeignKey('app.Doelgroep', on_delete=models.CASCADE, default=None, null=True)
    bouwsoort2 = models.ForeignKey('app.Bouwsoort', on_delete=models.CASCADE, default=None, null=True, related_name='SubBouwsoort')
    typeObject2 = models.ForeignKey('app.TypeObject', on_delete=models.CASCADE, default=None, null=True, related_name='SubTypeObject')
    doelgroep2 = models.ForeignKey('app.Doelgroep', on_delete=models.CASCADE, default=None, null=True, related_name='SubDoelgroep')

    Smarthome = models.BooleanField(default=False)
    AED = models.BooleanField(default=False)
    EntreeUpgrade = models.BooleanField(default=False)
    Pakketdient = models.BooleanField(default=False)
    JamesConcept = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.naam}"

class PVEItemAnnotation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    item = models.ForeignKey('app.PVEItem', on_delete=models.CASCADE, default=None)
    annotation = models.TextField(max_length=1000, default=None)
    gebruiker = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, default=None)
    
    def __str__(self):
        return f"{self.annotation} | {self.project.naam}"
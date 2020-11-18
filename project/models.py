from django.db import models
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis import forms
from utils.upload_rename import upload_to

class Beleggers(models.Model):
    naam = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.naam}"

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
    belegger = models.ForeignKey(Beleggers, on_delete=models.CASCADE, null=True)

    projectmanager = models.ForeignKey('users.CustomUser', default=None, on_delete=models.CASCADE, null=True)
    permitted = models.ManyToManyField('users.CustomUser', default=None, related_name="permitted")
    pveconnected = models.BooleanField(blank=True, null=True, default=False)

    # frozen level 0: all derde kunnen +opmerking doen. Frozen level 1: alleen aangegeven derde door projectmanager kan
    # de statussen accepteren of een opmerking maken. De volgende even frozens zijn dan projectmanager behandelbaar,
    # en de oneven is behandelbaar door de derde. Zo trechteren alle regels naar uiteindelijke acceptatie van alle
    # statussen. Opmerkingen moeten wellicht bijgehouden worden.
    frozenLevel = models.IntegerField(default=0, null=True)
    fullyFrozen = models.BooleanField(default=False)

    bouwsoort1 = models.ForeignKey('app.Bouwsoort', on_delete=models.CASCADE, default=None, null=True)
    typeObject1 = models.ForeignKey('app.TypeObject', on_delete=models.CASCADE, default=None, null=True)
    doelgroep1 = models.ForeignKey('app.Doelgroep', on_delete=models.CASCADE, default=None, null=True)
    bouwsoort2 = models.ForeignKey('app.Bouwsoort', on_delete=models.CASCADE, default=None, null=True, related_name='SubBouwsoort')
    typeObject2 = models.ForeignKey('app.TypeObject', on_delete=models.CASCADE, default=None, null=True, related_name='SubTypeObject')
    doelgroep2 = models.ForeignKey('app.Doelgroep', on_delete=models.CASCADE, default=None, null=True, related_name='SubDoelgroep')
    bouwsoort3 = models.ForeignKey('app.Bouwsoort', on_delete=models.CASCADE, default=None, null=True, related_name='SubSubBouwsoort')
    typeObject3 = models.ForeignKey('app.TypeObject', on_delete=models.CASCADE, default=None, null=True, related_name='SubSubTypeObject')
    doelgroep3 = models.ForeignKey('app.Doelgroep', on_delete=models.CASCADE, default=None, null=True, related_name='SubSubDoelgroep')

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
    annotation = models.TextField(max_length=1000, default=None, null=True)
    status = models.ForeignKey('syntrus.CommentStatus', on_delete=models.CASCADE, default=None)
    gebruiker = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, default=None, null=True)
    datum = models.DateTimeField(auto_now=True)
    kostenConsequenties = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=None)
    bijlage = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return f"{self.annotation}"

class BijlageToAnnotation(models.Model):
    ann = models.ForeignKey(PVEItemAnnotation, on_delete=models.CASCADE, default=None)
    bijlage = models.FileField(blank=True, null=True, upload_to='OpmerkingBijlages/')
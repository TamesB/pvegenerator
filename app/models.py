# Author: Tames Boon

from django.db import models

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

class ProjectStatus(models.Model):
    projstatus = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.status}"
        
class ContractStatus(models.Model):
    contrstatus = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.status}"

class ProjectFase(models.Model):
    fase = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.fase}"

class Project(models.Model):
    projectnaam = models.CharField(max_length=500)
    versienummer = models.CharField(max_length=100, blank=True)
    datum = models.DateField(blank=True)
    printdatum = models.DateField(blank=True)
    acquisiteur = models.CharField(max_length=500, blank=True)
    ontwikkelaar = models.CharField(max_length=500, blank=True)
    statusproject = models.ForeignKey(ProjectStatus, on_delete=models.CASCADE)
    statuscontract = models.ForeignKey(ContractStatus, on_delete=models.CASCADE)
    leeswijze = models.TextField(max_length=5000, blank=True)
    projectfase = models.ForeignKey(ProjectFase, on_delete=models.CASCADE) #?
    opmerkingenAqcuisiteur = models.TextField(max_length=5000, blank=True)
    illustratie = models.ImageField(blank=True, null=True, upload_to='images/%Y/%m/%d/')
    
    def __str__(self):
        return f"{self.projectnaam}"

class PVEItem(models.Model):
    hoofdstuk = models.ForeignKey(PVEHoofdstuk, on_delete=models.CASCADE, default=1)
    paragraaf = models.ForeignKey(PVEParagraaf, on_delete=models.CASCADE, blank=True, null=True)
    inhoud = models.TextField(max_length=5000)
    bijlage = models.FileField(blank=True, null=True, upload_to='attachments/%Y/%m/%d/')

    Bouwsoort = models.ManyToManyField(Bouwsoort, blank=True)
    TypeObject = models.ManyToManyField(TypeObject, blank=True)
    Doelgroep = models.ManyToManyField(Doelgroep, blank=True)

    Smarthome = models.BooleanField(default=False)
    AED = models.BooleanField(default=False)
    EntreeUpgrade = models.BooleanField(default=False)
    Pakketdient = models.BooleanField(default=False)
    JamesConcept = models.BooleanField(default=False)
    
    projects = models.ManyToManyField(Project, blank=True)

    def __str__(self):
        if self.paragraaf:
            return f"Item: {self.id}, Paragraaf: {self.paragraaf}"
        
        return f"Item: {self.id}, Hoofdstuk: {self.hoofdstuk}"
        
class PVEItemAnnotation(models.Model):
    item = models.ForeignKey(PVEItem, on_delete=models.CASCADE)
    annotation = models.TextField(max_length=1000)
    
    def __str__(self):
        return f"{self.item}"
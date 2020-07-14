from django.db import models
from django.conf import settings

class ProjectStatus(models.Model):
    projstatus = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.projstatus}"
        
class ContractStatus(models.Model):
    contrstatus = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.contrstatus}"

class ProjectFase(models.Model):
    fase = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.fase}"

# Create your models here.
class Project(models.Model):
    projectnaam = models.CharField(max_length=500)
    versienummer = models.CharField(max_length=100, blank=True)
    datum = models.DateTimeField(blank=True)
    printdatum = models.DateField(blank=True)
    acquisiteur = models.CharField(max_length=500, blank=True)
    ontwikkelaar = models.CharField(max_length=500, blank=True)
    statusproject = models.ForeignKey(ProjectStatus, on_delete=models.CASCADE)
    statuscontract = models.ForeignKey(ContractStatus, on_delete=models.CASCADE)
    leeswijze = models.TextField(max_length=5000, blank=True)
    projectfase = models.ForeignKey(ProjectFase, on_delete=models.CASCADE) #?
    opmerkingenAqcuisiteur = models.TextField(max_length=5000, blank=True)
    illustratie = models.ImageField(blank=True, null=True, upload_to='images/%Y/%m/%d/')
    
    # each project has just users that can access it, change it maybe to just a code that they can enter in
    # instead of each user having to completely create an account?
    userspermitted = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.projectnaam}"

class PVEItemAnnotation(models.Model):
    item = models.ForeignKey('app.PVEItem', on_delete=models.CASCADE)
    annotation = models.TextField(max_length=1000)
    
    def __str__(self):
        return f"{self.item}"
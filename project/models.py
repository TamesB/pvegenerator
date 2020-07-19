from django.db import models
from django.conf import settings
from django.contrib.gis.db import models
        
class ContractStatus(models.Model):
    contrstatus = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.contrstatus}"

# Create your models here.
class Project(models.Model):
    nummer = models.FloatField(max_length=100, default=None)
    naam = models.CharField(max_length=500, default=None)
    plaats = models.PointField()
    vhe = models.FloatField(max_length=100, default=None)
    pensioenfonds = models.CharField(max_length=100, default=None)
    statuscontract = models.ForeignKey(ContractStatus, on_delete=models.CASCADE)
    datum = models.DateTimeField(auto_now=True)

    permitted = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"{self.naam}"

class PVEItemAnnotation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    item = models.ForeignKey('app.PVEItem', on_delete=models.CASCADE, default=None)
    annotation = models.TextField(max_length=1000, default=None)
    
    def __str__(self):
        return f"{self.annotation} | {self.project.naam}"
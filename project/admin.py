from django.contrib import admin
from .models import Project, ContractStatus, PVEItemAnnotation
# Register your models here.
admin.site.register(Project)
admin.site.register(ContractStatus)
admin.site.register(PVEItemAnnotation)
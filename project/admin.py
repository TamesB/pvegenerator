from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import (
    Client,
    BeheerdersUitnodiging,
    BijlageToAnnotation,
    ContractStatus,
    Project,
    PVEItemAnnotation,
    Abbonement,
    CostType
)


# Register your models here.
class CustomGeoAdmin(ModelAdmin):
    options = {
        "layers": ["google.hybrid"],
        "overlayStyle": {
            "fillColor": "#ffff00",
            "strokeWidth": 5,
        },
        "defaultLon": 4.89,
        "defaultLat": 52,
        "defaultZoom": 4,
    }

admin.site.register(Abbonement)
admin.site.register(BeheerdersUitnodiging)
admin.site.register(Project, CustomGeoAdmin)
admin.site.register(ContractStatus)
admin.site.register(Client)
admin.site.register(PVEItemAnnotation)
admin.site.register(BijlageToAnnotation)
admin.site.register(CostType)

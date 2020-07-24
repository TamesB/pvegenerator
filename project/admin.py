from django.contrib import admin
from django.contrib.gis.admin import GeoModelAdmin
from .models import Project, ContractStatus, PVEItemAnnotation
# Register your models here.
class CustomGeoAdmin(GeoModelAdmin):
    options = {
        'layers': ['google.hybrid'],
        'overlayStyle': {
            'fillColor': '#ffff00',
            'strokeWidth': 5,
        },
        'defaultLon': 4.89,
        'defaultLat': 52,
        'defaultZoom': 4,
    }

admin.site.register(Project, CustomGeoAdmin)
admin.site.register(ContractStatus)
admin.site.register(PVEItemAnnotation)
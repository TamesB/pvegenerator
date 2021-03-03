# Author: Tames Boon

from django.contrib import admin
from .models import PVEVersie, Bouwsoort, TypeObject, Doelgroep, PVEHoofdstuk, PVEParagraaf, PVEItem

# Register your models here.
admin.site.register(PVEVersie)
admin.site.register(Bouwsoort)
admin.site.register(TypeObject)
admin.site.register(Doelgroep)
admin.site.register(PVEHoofdstuk)
admin.site.register(PVEParagraaf)
admin.site.register(PVEItem)
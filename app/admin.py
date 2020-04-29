# Author: Tames Boon

from django.contrib import admin
from .models import Bouwsoort, TypeObject, Doelgroep, PVEOnderdeel, PVEHoofdstuk, PVEParagraaf, PVESubparagraaf, PVEItem

# Register your models here.
admin.site.register(Bouwsoort)
admin.site.register(TypeObject)
admin.site.register(Doelgroep)
admin.site.register(PVEOnderdeel)
admin.site.register(PVEHoofdstuk)
admin.site.register(PVEParagraaf)
admin.site.register(PVESubparagraaf)
admin.site.register(PVEItem)

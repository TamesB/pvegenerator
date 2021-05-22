# Author: Tames Boon

from django.contrib import admin

from .models import (
    ActieveVersie,
    Bouwsoort,
    Doelgroep,
    PVEHoofdstuk,
    PVEItem,
    PVEParagraaf,
    PVEVersie,
    TypeObject,
    ItemBijlages
)

# Register your models here.
admin.site.register(PVEVersie)
admin.site.register(ActieveVersie)
admin.site.register(Bouwsoort)
admin.site.register(TypeObject)
admin.site.register(Doelgroep)
admin.site.register(PVEHoofdstuk)
admin.site.register(PVEParagraaf)
admin.site.register(PVEItem)
admin.site.register(ItemBijlages)

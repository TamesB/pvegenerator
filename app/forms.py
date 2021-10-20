# Author: Tames Boon

from django import forms
from django.forms import ModelForm

from project.models import Beleggers
from users.models import CustomUser

from .models import (
    ActieveVersie,
    Bouwsoort,
    Doelgroep,
    PVEHoofdstuk,
    PVEItem,
    PVEOnderdeel,
    PVEParagraaf,
    PVEVersie,
    TypeObject,
    ItemBijlages
)


class LoginForm(forms.Form):
    attrs = {"type": "password"}

    username = forms.CharField(label="Gebruikersnaam", max_length=100)
    password = forms.CharField(
        label="Wachtwoord", max_length=100, widget=forms.TextInput(attrs=attrs)
    )

    widgets = {
        "password": forms.PasswordInput(),
    }


class KiesParameterForm(forms.Form):
    parameter = forms.CharField(label="Naam", max_length=100)

class LogoKlantForm(ModelForm):
    class Meta: 
        model = Beleggers
        fields = ("logo",)
        labels = {"logo": ""}

class BeheerderKlantForm(ModelForm):
    beheerder = forms.ModelChoiceField(queryset=CustomUser.objects.none(), required=True)
    email = forms.EmailField(required=False, label="Of E-mail")
    class Meta: 
        model = Beleggers
        fields = ("beheerder",)
        labels = {"beheerder": ""}

        widgets = {
            "beheerder": forms.Select(attrs={"class": "ui dropdown"})
        }
class BeleggerForm(ModelForm):
    email = forms.EmailField(required=False)
    beheerder = forms.ModelChoiceField(queryset=CustomUser.objects.none(), required=False)

    widgets = {
        "beheerder": forms.Select(
            attrs={"class": "ui dropdown"}
        ),
    }

    class Meta:
        model = Beleggers
        fields = ("naam", "abbonement", "logo")
        labels = {
            "naam": "Naam:",
            "abbonement": "Abbonement Type:",
            "beheerder": "Beheerder:",
            "logo": "Upload Logo:",
            "email": "E-mail beheerder (optioneel):"
        }

        layout = [
            ("Text", '<h2 class="ui dividing header">Basisinformatie</h2>'),
            ("Field", "naam"),
            ("Field", "abbonement"),
            ("Text", '<h2 class="ui dividing header">Beheerder</h2>'),
            (
                "Text",
                "<i>Kies een bestaande beheerder of vul de e-mail van de beheerder van de klant in. Een e-mail wordt naar hen gestuurd voor toegang naar de gegenereerde sub-website.</i>",
            ),
            ("Field", "beheerder"),
            ("Field", "email"),
            ("Text", '<h2 class="ui dividing header">Klantenlogo</h2>'),
            (
                "Text",
                "<i>Upload hier de logo van de klant. Deze logo wordt gebruikt voor hun subwebsite en PvE's.</i><br>",
            ),
            ("Field", "logo"),
        ]

class PVEVersieForm(ModelForm):
    kopie_versie = forms.ModelChoiceField(
        queryset=PVEVersie.objects.all(), label="Kopie (optioneel):", required=False
    )

    class Meta:
        model = PVEVersie
        fields = ("versie", "belegger")
        labels = {
            "versie": "Versie Naam:",
            "kopie_versie": "Kopie (optioneel):"
        }
        widgets = {"belegger": forms.HiddenInput()}


class bijlageEditForm(forms.Form):
    bijlage = forms.FileField(required=False, label="Bijlage")
    items = forms.ModelMultipleChoiceField(
        queryset=PVEItem.objects.all(), label="Behoort tot regel(s)", required=False
    )
    naam = forms.CharField(label="", required=False, max_length=100)

    widgets = {
        "items": forms.SelectMultiple(
            attrs={"class": "ui search dropdown", "multiple": ""}
        ),
    }

    class Meta:
        layout = [
            (
                "Text",
                "<i>Upload het bestand hier.</i><br>",
            ),
            ("Field", "bijlage"),
            ("Text", '<h2 class="ui dividing header">Items</h2>'),
            (
                "Text",
                "<i>Voeg hier een of meerdere regels toe waar de bijlage tot behoort</i>",
            ),
            ("Field", "items"),
            ("Text", '<h2 class="ui dividing header">Bijnaam (optioneel)</h2>'),
            (
                "Text",
                "<i>Voeg hier de bijnaam toe van de bijlage. Deze naam wordt gebruikt in het PvE en als bestandsnaam bij het downloaden van het PvE.</i><br>",
            ),
            ("Field", "naam"),
        ]


class SectionForm(ModelForm):
    class Meta:
        model = PVEOnderdeel
        fields = ("naam",)
        labels = {
            "naam": "Naam:",
        }


class ActieveVersieEditForm(ModelForm):
    class Meta:
        model = ActieveVersie
        fields = ("versie",)
        labels = {
            "versie": "Versie:",
        }


class ChapterForm(ModelForm):
    class Meta:
        model = PVEHoofdstuk
        fields = ("hoofdstuk",)
        labels = {
            "hoofdstuk": "Naam:",
        }


class ParagraafForm(ModelForm):
    class Meta:
        model = PVEParagraaf
        fields = ("paragraaf",)
        labels = {
            "paragraaf": "Naam:",
        }


class PVEItemEditForm(ModelForm):
    bijlage = forms.FileField(required=False)
    BestaandeBijlage = forms.ModelChoiceField(
        queryset=ItemBijlages.objects.none(), label="Bestaande Bijlage(s)", required=False
    )
    Bouwsoort = forms.ModelMultipleChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort", required=False
    )
    TypeObject = forms.ModelMultipleChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object", required=False
    )
    Doelgroep = forms.ModelMultipleChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep", required=False
    )

    widgets = {
        "Bouwsoort": forms.SelectMultiple(
            attrs={"class": "ui dropdown", "multiple": ""}
        ),
        "BestaandeBijlage": forms.SelectMultiple(
            attrs={"class": "ui dropdown", "multiple": ""}
        ),
        "TypeObject": forms.SelectMultiple(
            attrs={"class": "ui dropdown", "multiple": ""}
        ),
        "Doelgroep": forms.SelectMultiple(
            attrs={"class": "ui dropdown", "multiple": ""}
        ),
    }

    class Meta:
        model = PVEItem
        fields = (
            "inhoud",
            "basisregel",
            "Bouwsoort",
            "TypeObject",
            "Doelgroep",
            "Smarthome",
            "AED",
            "EntreeUpgrade",
            "Pakketdient",
            "JamesConcept",
        )
        labels = {
            "inhoud": "Inhoud",
            "bijlage": "Bijlage",
            "basisregel": "BASIS-regel",
            "Bouwsoort": "Bouwsoort",
            "TypeObject": "Type Object",
            "Doelgroep": "Doelgroep",
            "Smarthome": "Smarthome",
            "AED": "AED",
            "EntreeUpgrade": "Entree Upgrade",
            "Pakketdient": "Pakketdient",
            "JamesConcept": "James Concept",
        }

        layout = [
            ("Text", '<h2 class="ui dividing header">Regel</h2>'),
            (
                "Text",
                "<i>De inhoud van de regel is wat te zien is in het uiteindelijke Programma van Eisen. Bijlages worden met referentie toegevoegd in het eindproduct.</i><br>",
            ),
            ("Field", "inhoud"),
            (
                "Text",
                "<i>Upload een nieuwe bijlage, of kies een bestaande bijlage.</i><br>",
            ),
            ("Field", "bijlage"),
            ("Field", "BestaandeBijlage"),
            ("Text", '<h2 class="ui dividing header">Parameters</h2>'),
            (
                "Text",
                "<i>Keuzeparameters die aangeven waar de regel tot behoort. De regel komt alleen in het PvE als het tot de overeenkomende parameter behoort die bij het genereren gekozen is.</i>",
            ),
            ("Text", '<h4 class="ui dividing header">BASIS-Regel</h4>'),
            (
                "Text",
                "<i>Vink aan als de regel tot de Basis PvE hoort. Deze regel komt altijd in het gegenereerde PvE.</i><br>",
            ),
            ("Field", "basisregel"),
            ("Text", '<h4 class="ui dividing header">Keuzematrix</h4>'),
            (
                "Text",
                "<i>Mits de regel geen basisregel is; kies de parameters waartoe deze regel behoort. Een regel kan tot meerdere bouwsoorten, objecten, en doelgroepen behoren.</i><br>",
            ),
            (
                "Three Fields",
                ("Field", "Bouwsoort"),
                ("Field", "TypeObject"),
                ("Field", "Doelgroep"),
            ),
            ("Text", "<b>Specifieke regels</b><br>"),
            (
                "Five Fields",
                ("Field", "Smarthome"),
                ("Field", "AED"),
                ("Field", "EntreeUpgrade"),
                ("Field", "Pakketdient"),
                ("Field", "JamesConcept"),
            ),
        ]

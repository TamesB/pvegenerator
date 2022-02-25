# Author: Tames Boon

from django import forms
from django.forms import ModelForm

from project.models import Client
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
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Gebruikersnaam",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Wachtwoord",
                "class": "form-control"
            }
        ))

class KiesParameterForm(forms.Form):
    parameter = forms.CharField(label="Parameter:", max_length=100)

class ClientLogoForm(ModelForm):
    class Meta: 
        model = Client
        fields = ("logo",)
        labels = {"logo": ""}

class ClientAdminForm(forms.Form):
    email = forms.EmailField(label="E-mail Beheerder")
class BeleggerForm(ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = Client
        fields = ("name", "subscription", "logo")
        labels = {
            "name": "Naam:",
            "subscription": "Abbonement Type:",
            "logo": "Upload Logo:",
            "email": "E-mail beheerder (optioneel):"
        }

        layout = [
            ("Text", '<h2 class="ui dividing header">Basisinformatie</h2>'),
            ("Field", "name"),
            ("Field", "subscription"),
            ("Text", '<h2 class="ui dividing header">Beheerder</h2>'),
            (
                "Text",
                "<i>Vul de e-mail van de beheerder van de klant in. Een e-mail wordt naar hen gestuurd voor toegang naar de gegenereerde sub-website.</i>",
            ),
            ("Field", "email"),
            ("Text", '<h2 class="ui dividing header">Klantenlogo</h2>'),
            (
                "Text",
                "<i>Upload hier de logo van de klant. Deze logo wordt gebruikt voor hun subwebsite en PvE's.</i><br>",
            ),
            ("Field", "logo"),
        ]

class PVEVersieForm(ModelForm):
    version_copy = forms.ModelChoiceField(
        queryset=PVEVersie.objects.all(), label="Kopie (optioneel):", required=False
    )

    class Meta:
        model = PVEVersie
        fields = ("version", "client")
        labels = {
            "version": "Versie Naam:",
            "version_copy": "Kopie (optioneel):"
        }
        widgets = {"client": forms.HiddenInput()}

class PVEVersieNameForm(ModelForm):
    class Meta:
        model = PVEVersie
        fields = ("version",)
        labels = {
            "version": "",
        }

class attachmentEditForm(forms.Form):
    attachment = forms.FileField(required=False, label="Bijlage")
    items = forms.ModelMultipleChoiceField(
        queryset=PVEItem.objects.all(), label="Behoort tot regel(s)", required=False
    )
    name = forms.CharField(label="", required=False, max_length=100)

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
            ("Field", "attachment"),
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
            ("Field", "name"),
        ]


class SectionForm(ModelForm):
    class Meta:
        model = PVEOnderdeel
        fields = ("name",)
        labels = {
            "name": "Naam:",
        }


class ActieveVersieEditForm(ModelForm):
    class Meta:
        model = ActieveVersie
        fields = ("version",)
        labels = {
            "version": "Versie:",
        }


class ChapterForm(ModelForm):
    class Meta:
        model = PVEHoofdstuk
        fields = ("chapter",)
        labels = {
            "chapter": "Naam:",
        }


class ParagraafForm(ModelForm):
    class Meta:
        model = PVEParagraaf
        fields = ("paragraph",)
        labels = {
            "paragraph": "Naam:",
        }


class PVEItemEditForm(ModelForm):
    attachment = forms.FileField(required=False)
    existing_attachment = forms.ModelChoiceField(
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
        "existing_attachment": forms.SelectMultiple(
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
            "attachment": "Bijlage",
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
            ("Field", "attachment"),
            ("Field", "existing_attachment"),
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

    def __init__(self, *args, **kwargs):
        super(PVEItemEditForm, self).__init__(*args, **kwargs)
        self.fields['attachment'].required = False
        self.fields['existing_attachment'].required = False


class GeneralAccountAdd(forms.Form):
    # for adding non-admin accounts, all types (add to client,
    # projectmanager checkbox, add to stakeholder)
    # see GeneralAccountAdd in views
    pass

class AdminUserForm(forms.Form):
    username = forms.CharField(label="Nieuw gebruikersnaam:", required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    
    class Meta:
        labels = {
            "username": "Nieuw gebruikersnaam:",
        }
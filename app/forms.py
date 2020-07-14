# Author: Tames Boon

from django import forms
from .models import PVEItem, Bouwsoort, TypeObject, Doelgroep, PVEHoofdstuk, PVEParagraaf
from django.forms import ModelForm

class LoginForm(forms.Form):
    attrs = {
        "type": "password"
    }

    username = forms.CharField(label='Gebruikersnaam', max_length=100)
    password = forms.CharField(label='Wachtwoord', max_length=100, widget=forms.TextInput(attrs=attrs))

    widgets = {
                'password': forms.PasswordInput(),
            }

class KiesParameterForm(forms.Form):
    parameter = forms.CharField(label='Naam', max_length=100)

class SectionForm(forms.Form):
    naam = forms.CharField(label='Naam', max_length=100)
    
class ChapterForm(ModelForm):
    class Meta:
        model = PVEHoofdstuk
        fields = ('hoofdstuk',)
        labels = {
            'hoofdstuk':'Naam:',
        }
        
class ParagraafForm(ModelForm):
    class Meta:
        model = PVEParagraaf
        fields = ('paragraaf',)
        labels = {
            'paragraaf':'Naam:',
        }
        
class PVEItemEditForm(ModelForm):
    bijlage = forms.FileField(required=False)
    Bouwsoort = forms.ModelMultipleChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort', required=False)
    TypeObject = forms.ModelMultipleChoiceField(queryset=TypeObject.objects.all(), label='Type Object', required=False)
    Doelgroep = forms.ModelMultipleChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep', required=False)

    widgets = {
        'Bouwsoort': forms.SelectMultiple(attrs={'class': 'ui dropdown', 'multiple': ""}),
        'TypeObject': forms.SelectMultiple(attrs={'class': 'ui dropdown', 'multiple': ""}),
        'Doelgroep': forms.SelectMultiple(attrs={'class': 'ui dropdown', 'multiple': ""}),
    }
    
    class Meta:
        model = PVEItem
        fields = ('inhoud', 'bijlage', 'basisregel', 'Bouwsoort', 'TypeObject', 'Doelgroep', 'Smarthome', 'AED', 'EntreeUpgrade', 'Pakketdient', 'JamesConcept')
        labels = {
            'inhoud':'Inhoud',
            'bijlage':'Bijlage',
            'basisregel':'BASIS-regel',
            'Bouwsoort':'Bouwsoort',
            'TypeObject':'Type Object',
            'Doelgroep':'Doelgroep',
            'Smarthome':'Smarthome',
            'AED':'AED',
            'EntreeUpgrade':'Entree Upgrade',
            'Pakketdient':'Pakketdient',
            'JamesConcept':'James Concept',
        }

        layout = [
            ("Text", "<h2 class=\"ui dividing header\">Regel</h2>"),
            ("Text", "<i>De inhoud van de regel is wat te zien is in het uiteindelijke Programma van Eisen. Bijlages worden met referentie toegevoegd in het eindproduct.</i><br>"),
        
            ("Three Fields",
                ("Field", "inhoud"),
                ("Field", "bijlage"),
            ),

            ("Text", "<h2 class=\"ui dividing header\">Parameters</h2>"),
            ("Text", "<i>Keuzeparameters die aangeven waar de regel tot behoort. De regel komt alleen in het PvE mits bij het genereren de overeenkomende parameter is gekozen waar de regel hier tot toegewezen is.</i>"),

            ("Text", "<h4 class=\"ui dividing header\">BASIS-Regel</h4>"),
            ("Text", "<i>BASIS-Regels behoren altijd tot de uitkomende PvE, ongeacht de gekozen keuzeparameters. Vink de box aan als deze regel altijd tot het PvE behoort.</i><br>"),
            ("Field", "basisregel"),

            ("Text", "<h4 class=\"ui dividing header\">Keuzematrix</h4>"),
            ("Text", "<i>Mits de regel geen basisregel is; kies de parameters waartoe deze regel behoort. Een regel kan tot meerdere bouwsoorten, objecten, en doelgroepen behoren.</i><br>"),

            ("Four Fields",
                ("Field", "Bouwsoort"),
                ("Field", "TypeObject"),
                ("Field", "Doelgroep"),
                ("Five Fields",
                    ("Field", "Smarthome"),
                    ("Field", "AED"),
                    ("Field", "EntreeUpgrade"),
                    ("Field", "Pakketdient"),
                    ("Field", "JamesConcept"),
                ),
            ),
        ]

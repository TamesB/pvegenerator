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

class PVEParameterForm(ModelForm):
    Bouwsoort = forms.ModelChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort')
    TypeObject = forms.ModelChoiceField(queryset=TypeObject.objects.all(), label='Type Object')
    Doelgroep = forms.ModelChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep')

    widgets = {
        'Bouwsoort': forms.Select(attrs={'class': 'ui dropdown'}),
        'TypeObject': forms.Select(attrs={'class': 'ui dropdown'}),
        'Doelgroep': forms.Select(attrs={'class': 'ui dropdown'}),
    }

    class Meta:
        model = PVEItem
        fields = ('Bouwsoort', 'TypeObject', 'Doelgroep', 'Smarthome', 'AED', 'EntreeUpgrade', 'Pakketdient', 'JamesConcept')
        labels = {
            'Smarthome':'Smarthome',
            'AED':'AED',
            'EntreeUpgrade':'Entree Upgrade',
            'Pakketdient':'Pakketdient',
            'JamesConcept':'James Concept',
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
        fields = ('inhoud', 'bijlage', 'Bouwsoort', 'TypeObject', 'Doelgroep', 'Smarthome', 'AED', 'EntreeUpgrade', 'Pakketdient', 'JamesConcept')
        labels = {
            'inhoud':'Inhoud',
            'bijlage':'Bijlage',
            'Bouwsoort':'Bouwsoort',
            'TypeObject':'Type Object',
            'Doelgroep':'Doelgroep',
            'Smarthome':'Smarthome',
            'AED':'AED',
            'EntreeUpgrade':'Entree Upgrade',
            'Pakketdient':'Pakketdient',
            'JamesConcept':'James Concept',
        }

from django import forms
from app.models import PVEItem, Bouwsoort, TypeObject, Doelgroep
from django.forms import ModelForm


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
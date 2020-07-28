from django import forms
from app.models import PVEItem, Bouwsoort, TypeObject, Doelgroep
from django.forms import ModelForm


class PVEParameterForm(ModelForm):
    Bouwsoort1 = forms.ModelChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort (Hoofd)')
    Bouwsoort2 = forms.ModelChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort (Sub)')

    TypeObject1 = forms.ModelChoiceField(queryset=TypeObject.objects.all(), label='Type Object (Hoofd)')
    TypeObject2 = forms.ModelChoiceField(queryset=TypeObject.objects.all(), label='Type Object (Sub)')

    Doelgroep1 = forms.ModelChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep (Hoofd)')
    Doelgroep2 = forms.ModelChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep (Sub)')

    widgets = {
        'Bouwsoort1': forms.Select(attrs={'class': 'ui dropdown'}),
        'Bouwsoort2': forms.Select(attrs={'class': 'ui dropdown'},),
        'TypeObject1': forms.Select(attrs={'class': 'ui dropdown'},),
        'TypeObject2': forms.Select(attrs={'class': 'ui dropdown'},),
        'Doelgroep1': forms.Select(attrs={'class': 'ui dropdown'},),
        'Doelgroep2': forms.Select(attrs={'class': 'ui dropdown'},),
    }

    class Meta:
        model = PVEItem
        fields = ('Bouwsoort1','Bouwsoort2', 'TypeObject1','TypeObject2', 'Doelgroep1','Doelgroep2', 'Smarthome', 'AED', 'EntreeUpgrade', 'Pakketdient', 'JamesConcept')
        labels = {
            'Bouwsoort1':'Bouwsoort (Hoofd)',
            'Bouwsoort2':'Bouwsoort (Sub)',
            'TypeObject1':'Type Object (Hoofd)',
            'TypeObject2':'Type Object (Sub)',
            'Doelgroep1':'Doelgroep (Hoofd)',
            'Doelgroep2':'Doelgroep (Sub)',

            'Smarthome':'Smarthome',
            'AED':'AED',
            'EntreeUpgrade':'Entree Upgrade',
            'Pakketdient':'Pakketdient',
            'JamesConcept':'James Concept',
        }

        layout = [
            ("Text", "<h2 class=\"ui dividing header\">Genereer proef PvE</h2>"),

            ("Two Fields",
                ("Field", "Bouwsoort1"),
                ("Field", "Bouwsoort2"),
            ),

            ("Two Fields",
                ("Field", "TypeObject1"),
                ("Field", "TypeObject2"),
            ),

            ("Two Fields",
                ("Field", "Doelgroep1"),
                ("Field", "Doelgroep2"),
            ),

            ("Text", "<b>Specifieke regels</b><br>"),

            ("Five Fields",
                ("Field", "Smarthome"),
                ("Field", "AED"),
                ("Field", "EntreeUpgrade"),
                ("Field", "Pakketdient"),
                ("Field", "JamesConcept"),
            ),
        ]

    def __init__(self, *args, **kwargs):
        super(PVEParameterForm, self).__init__(*args, **kwargs)
        self.fields['Bouwsoort2'].required = False
        self.fields['TypeObject1'].required = False
        self.fields['TypeObject2'].required = False
        self.fields['Doelgroep1'].required = False
        self.fields['Doelgroep2'].required = False

class SpecificPVEParameterForm(ModelForm):
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

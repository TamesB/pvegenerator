# Author: Tames Boon

from django import forms
from django.forms import ModelForm
from app.models import Bouwsoort, TypeObject, Doelgroep, PVEItem
from project.models import Project, PVEItemAnnotation, BijlageToAnnotation
from users.models import Invitation
from syntrus.models import CommentStatus
from django.contrib.gis import forms

class LoginForm(forms.Form):
    attrs = {
        "type": "password"
    }

    username = forms.CharField(label='Gebruikersnaam', max_length=100)
    password = forms.CharField(label='Wachtwoord', max_length=100, widget=forms.TextInput(attrs=attrs))

    widgets = {
                'password': forms.PasswordInput(),
            }

class PVEParameterForm(ModelForm):
    Bouwsoort1 = forms.ModelChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort')
    Bouwsoort2 = forms.ModelChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort')
    Bouwsoort3 = forms.ModelChoiceField(queryset=Bouwsoort.objects.all(), label='Bouwsoort')

    TypeObject1 = forms.ModelChoiceField(queryset=TypeObject.objects.all(), label='Type Object')
    TypeObject2 = forms.ModelChoiceField(queryset=TypeObject.objects.all(), label='Type Object')
    TypeObject3 = forms.ModelChoiceField(queryset=TypeObject.objects.all(), label='Type Object')

    Doelgroep1 = forms.ModelChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep')
    Doelgroep2 = forms.ModelChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep')
    Doelgroep3 = forms.ModelChoiceField(queryset=Doelgroep.objects.all(), label='Doelgroep')

    widgets = {
        'Bouwsoort1': forms.Select(attrs={'class': 'ui dropdown'}),
        'Bouwsoort2': forms.Select(attrs={'class': 'ui dropdown'},),
        'Bouwsoort3': forms.Select(attrs={'class': 'ui dropdown'},),
        'TypeObject1': forms.Select(attrs={'class': 'ui dropdown'},),
        'TypeObject2': forms.Select(attrs={'class': 'ui dropdown'},),
        'TypeObject3': forms.Select(attrs={'class': 'ui dropdown'},),
        'Doelgroep1': forms.Select(attrs={'class': 'ui dropdown'},),
        'Doelgroep2': forms.Select(attrs={'class': 'ui dropdown'},),
        'Doelgroep3': forms.Select(attrs={'class': 'ui dropdown'},),
    }

    class Meta:
        model = PVEItem
        fields = ('Bouwsoort1','Bouwsoort2', 'Bouwsoort3',  'TypeObject1','TypeObject2','TypeObject3', 'Doelgroep1','Doelgroep2','Doelgroep3','Smarthome', 'AED', 'EntreeUpgrade', 'Pakketdient', 'JamesConcept')
        labels = {
            'Bouwsoort1':'Bouwsoort',
            'Bouwsoort2':'Bouwsoort',
            'Bouwsoort3':'Bouwsoort',
            'TypeObject1':'Type Object',
            'TypeObject2':'Type Object',
            'TypeObject3':'Type Object',
            'Doelgroep1':'Doelgroep',
            'Doelgroep2':'Doelgroep',
            'Doelgroep3':'Doelgroep',

            'Smarthome':'Smarthome',
            'AED':'AED',
            'EntreeUpgrade':'Entree Upgrade',
            'Pakketdient':'Pakketdient',
            'JamesConcept':'James Concept',
        }
    def __init__(self, *args, **kwargs):
        super(PVEParameterForm, self).__init__(*args, **kwargs)
        self.fields['Bouwsoort2'].required = False
        self.fields['Bouwsoort3'].required = False
        self.fields['TypeObject1'].required = False
        self.fields['TypeObject2'].required = False
        self.fields['TypeObject3'].required = False
        self.fields['Doelgroep1'].required = False
        self.fields['Doelgroep2'].required = False
        self.fields['Doelgroep3'].required = False

class KoppelDerdeUserForm(ModelForm):
    class Meta:
        model = Invitation
        fields = {
            'project', 'invitee', 'user_functie', 'user_afdeling',
        }
        labels = {
            'project':'Project:',
            'invitee':'E-Mail:',
            'user_functie':'Functie:',
            'user_afdeling':'Afdeling:'
        }

class PlusAccountForm(ModelForm):
    type_choices = (
        ('SOG', 'Syntrus Projectmanager'),
        ('SD', 'Derde'),
    )    
    
    rang = forms.ChoiceField(choices=type_choices)

    class Meta:
        model = Invitation
        fields = {
            'project', 'invitee', 'user_functie', 'user_afdeling',
        }
        labels = {
            'rang':'Rang gebruiker:',
            'project':'Project:',
            'invitee':'E-Mail:',
            'user_functie':'Functie:',
            'user_afdeling':'Afdeling:'
        }

class CheckboxInput(forms.CheckboxInput):
    def __init__(self, default=False, *args, **kwargs):
        super(CheckboxInput, self).__init__(*args, **kwargs)
        self.default = default

    def value_from_datadict(self, data, files, name):
        if name not in data:
            return self.default
        return super(CheckboxInput, self).value_from_datadict(data, files, name)


class PVEItemAnnotationForm(forms.Form):
    item_id = forms.IntegerField(label='item_id')
    status = forms.ModelChoiceField(queryset=CommentStatus.objects.all(), required=False)
    annotation = forms.CharField(label='annotation', max_length=1000, widget=forms.Textarea, required=False)
    kostenConsequenties = forms.DecimalField(label='(Optioneel) Kosten Consequenties', required=False)

class BijlageToAnnotationForm(ModelForm):
    class Meta:
        model = BijlageToAnnotation
        fields = ('ann', 'annbijlage')
        labels = {
            'ann':'Opmerking:', 'annbijlage':'Bijlage:',
        }
        widgets = {'ann': forms.HiddenInput()}

class StartProjectForm(ModelForm):
    plaats = forms.PointField(widget=forms.OSMWidget(attrs={'default_lat': 52.37, 'default_lon': 4.895,}))

    class Meta:
        model = Project
        fields = ('naam', 'nummer', 'vhe', 'pensioenfonds', 'statuscontract', 'plaats')
        geom = forms.PointField()
        labels = {
            'naam':'Projectnaam:', 'nummer':'Projectnummer:', 'plaats':'Plaats:', 'vhe':'Aantal verhuureenheden:', 
            'pensioenfonds':'Pensioenfonds:', 'statuscontract':"Contractstatus:",
        }
        widgets = {
            'point': forms.OSMWidget(
                attrs={
                    'default_lat': 52.37,
                    'default_lon': 4.895,
                })
        }

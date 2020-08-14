from django import forms
from project.models import Project, ContractStatus
from django.forms import ModelForm
from django.contrib.gis import forms

class StartProjectForm(ModelForm):
    plaats = forms.PointField(widget=forms.OSMWidget(attrs={'default_lat': 52.37, 'default_lon': 4.895,}))

    class Meta:
        model = Project
        fields = ('naam', 'nummer', 'vhe', 'pensioenfonds', 'plaats')
        geom = forms.PointField()
        labels = {
            'naam':'Projectnaam:', 'nummer':'Projectnummer:', 'plaats':'Plaats:', 'vhe':'Aantal verhuureenheden:', 
            'pensioenfonds':'Pensioenfonds:',
        }
        widgets = {
            'point': forms.OSMWidget(
                attrs={
                    'default_lat': 52.37,
                    'default_lon': 4.895,
                })
        }

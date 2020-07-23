from django import forms
from project.models import Project, ContractStatus
from django.forms import ModelForm
from django.contrib.gis import forms

class StartProjectForm(ModelForm):
    plaats = forms.PointField(widget=forms.OSMWidget(attrs={'map_width': 800, 'map_height': 500}))

    class Meta:
        model = Project
        fields = ('naam', 'nummer', 'plaats', 'vhe', 'pensioenfonds')
        labels = {
            'naam':'Projectnaam:', 'nummer':'Projectnummer:', 'plaats':'Plaats:', 'vhe':'Aantal verhuureenheden:', 
            'pensioenfonds':'Pensioenfonds:',
        }
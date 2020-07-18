from django import forms
from project.models import Project, ProjectStatus, ContractStatus, ProjectFase
from django.forms import ModelForm

class StartProjectForm(ModelForm):

    class Meta:
        model = Project
        fields = ('naam', 'nummer', 'plaats', 'vhe', 'pensioenfonds')
        labels = {
            'naam':'Projectnaam:', 'nummer':'Projectnummer:', 'plaats':'Plaats:', 'vhe':'Aantal verhuureenheden:', 
            'pensioenfonds':'Pensioenfonds:',
        }
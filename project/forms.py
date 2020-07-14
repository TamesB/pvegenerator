from django import forms
from project.models import Project, ProjectStatus, ContractStatus, ProjectFase
from django.forms import ModelForm

class StartProjectForm(ModelForm):
    statusproject = forms.ModelChoiceField(queryset=ProjectStatus.objects.all(), label='Projectstatus')
    statuscontract = forms.ModelChoiceField(queryset=ContractStatus.objects.all(), label='Contractstatus')
    projectfase = forms.ModelChoiceField(queryset=ProjectFase.objects.all(), label='Projectfase')

    widgets = {
        'ProjectStatus': forms.Select(attrs={'class': 'ui dropdown'}),
        'ContractStatus': forms.Select(attrs={'class': 'ui dropdown'}),
        'ProjectFase': forms.Select(attrs={'class': 'ui dropdown'}),
    }

    class Meta:
        model = Project
        fields = ('projectnaam', 'versienummer', 'datum', 'printdatum', 'acquisiteur', 'ontwikkelaar', 'statusproject', 
        'statuscontract', 'leeswijze', 'projectfase', 'illustratie')
        labels = {
            'projectnaam':'Projectnaam:', 'versienummer':'Versienummer:', 'datum':'Datum:', 'printdatum':'Printdatum:', 
            'acquisiteur':'Acquisiteur:', 'ontwikkelaar':'Ontwikkelaar:', 'statusproject':'Status project:', 
            'statuscontract':'Status contract:', 'leeswijze':'Leeswijze:', 'projectfase':'Projectfase:', 'illustratie':'Illustratie:'
        }
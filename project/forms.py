from django import forms
from django.contrib.gis import forms
from django.forms import ModelForm

from project.models import Project


class StartProjectForm(ModelForm):
    plaats = forms.PointField(
        widget=forms.OSMWidget(
            attrs={
                "default_lat": 52.37,
                "default_lon": 4.895,
            }
        )
    )

    class Meta:
        model = Project
        fields = (
            "client",
            "projectmanager",
            "name",
            "nummer",
            "vhe",
            "pensioenfonds",
            "first_annotate",
            "plaats",
        )
        geom = forms.PointField()
        labels = {
            "client": "Belegger:",
            "projectmanager": "Projectmanager:",
            "name": "Projectnaam:",
            "nummer": "Projectnummer:",
            "plaats": "Plaats:",
            "vhe": "Aantal verhuureenheden:",
            "pensioenfonds": "Pensioenfonds:",
            "first_annotate": "Eerste statusaanwijzing naar:"
        }
        widgets = {
            "point": forms.OSMWidget(
                attrs={
                    "default_lat": 52.37,
                    "default_lon": 4.895,
                }
            )
        }


class SearchPVEItemForm(forms.Form):
    inhoud = forms.CharField(label="(Deel)inhoud", max_length=1000)


class PVEItemAnnotationForm(forms.Form):
    annotation = forms.CharField(
        label="Opmerking", max_length=1000, widget=forms.Textarea
    )
    consequentCosts = forms.DecimalField(
        label="(Optioneel) Kosten Consequenties", required=False, min_value=0
    )

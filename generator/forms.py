from django import forms
from django.forms import ModelForm

from app.models import Bouwsoort, Doelgroep, PVEItem, TypeObject


class PVEParameterForm(ModelForm):
    Bouwsoort1 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort (Hoofd)"
    )
    Bouwsoort2 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort (Sub)"
    )
    Bouwsoort3 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort (Sub)"
    )

    TypeObject1 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object (Hoofd)"
    )
    TypeObject2 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object (Sub)"
    )
    TypeObject3 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object (Sub)"
    )

    Doelgroep1 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep (Hoofd)"
    )
    Doelgroep2 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep (Sub)"
    )
    Doelgroep3 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep (Sub)"
    )

    widgets = {
        "Bouwsoort1": forms.Select(attrs={"class": "ui dropdown"}),
        "Bouwsoort2": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "Bouwsoort3": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "TypeObject1": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "TypeObject2": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "TypeObject3": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "Doelgroep1": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "Doelgroep2": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
        "Doelgroep3": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
    }

    class Meta:
        model = PVEItem
        fields = (
            "Bouwsoort1",
            "Bouwsoort2",
            "Bouwsoort3",
            "TypeObject1",
            "TypeObject2",
            "TypeObject3",
            "Doelgroep1",
            "Doelgroep2",
            "Doelgroep3",
            "Smarthome",
            "AED",
            "EntreeUpgrade",
            "Pakketdient",
            "JamesConcept",
        )
        labels = {
            "Bouwsoort1": "Bouwsoort (Hoofd)",
            "Bouwsoort2": "Bouwsoort (Sub)",
            "Bouwsoort3": "Bouwsoort (Sub)",
            "TypeObject1": "Type Object (Hoofd)",
            "TypeObject2": "Type Object (Sub)",
            "TypeObject3": "Type Object (Sub)",
            "Doelgroep1": "Doelgroep (Hoofd)",
            "Doelgroep2": "Doelgroep (Sub)",
            "Doelgroep3": "Doelgroep (Sub)",
            "Smarthome": "Smarthome",
            "AED": "AED",
            "EntreeUpgrade": "Entree Upgrade",
            "Pakketdient": "Pakketdient",
            "JamesConcept": "James Concept",
        }

        layout = [
            (
                "Two Fields",
                ("Field", "Bouwsoort1"),
                ("Field", "Bouwsoort2"),
                ("Field", "Bouwsoort3"),
            ),
            (
                "Two Fields",
                ("Field", "TypeObject1"),
                ("Field", "TypeObject2"),
                ("Field", "TypeObject3"),
            ),
            (
                "Two Fields",
                ("Field", "Doelgroep1"),
                ("Field", "Doelgroep2"),
                ("Field", "Doelgroep3"),
            ),
            ("Text", "<b>Specifieke regels</b><br>"),
            (
                "Five Fields",
                ("Field", "Smarthome"),
                ("Field", "AED"),
                ("Field", "EntreeUpgrade"),
                ("Field", "Pakketdient"),
                ("Field", "JamesConcept"),
            ),
        ]

    def __init__(self, *args, **kwargs):
        super(PVEParameterForm, self).__init__(*args, **kwargs)
        self.fields["Bouwsoort2"].required = False
        self.fields["Bouwsoort3"].required = False
        self.fields["TypeObject1"].required = False
        self.fields["TypeObject2"].required = False
        self.fields["TypeObject3"].required = False
        self.fields["Doelgroep1"].required = False
        self.fields["Doelgroep2"].required = False
        self.fields["Doelgroep3"].required = False


class SpecificPVEParameterForm(ModelForm):
    class Meta:
        model = PVEItem
        fields = (
            "Bouwsoort",
            "TypeObject",
            "Doelgroep",
            "Smarthome",
            "AED",
            "EntreeUpgrade",
            "Pakketdient",
            "JamesConcept",
        )
        labels = {
            "Smarthome": "Smarthome",
            "AED": "AED",
            "EntreeUpgrade": "Entree Upgrade",
            "Pakketdient": "Pakketdient",
            "JamesConcept": "James Concept",
        }


class CompareFormBouwsoort(forms.Form):
    Bouwsoort1 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort"
    )
    Bouwsoort2 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort"
    )

    class Meta:
        model = PVEItem
        fields = ("Bouwsoort1", "Bouwsoort2")
        labels = {
            "Bouwsoort1": "Bouwsoort 1",
            "Bouwsoort2": "Bouwsoort 2",
        }

        layout = [
            ("Text", '<h2 class="ui dividing header">Afwijkingenlijst twee bouwsoorten</h2>'),
            ("Text", '<i>Let op het verschil tussen de volgorde van de parameters. Appartement 0-50 m2 t.o.v. Grondgebonden Woning geeft een ander resultaat dan Grondgebonden Woning t.o.v. Appartement 0-50 m2. Namelijk, welke wel in de eerste parameter voorkomt maar niet in de tweede.</i>'),
            (
                "Two Fields",
                ("Field", "Bouwsoort1"),
                ("Field", "Bouwsoort2"),
            ),
        ]


class CompareFormTypeObject(forms.Form):
    TypeObject1 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object"
    )
    TypeObject2 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object"
    )

    class Meta:
        model = PVEItem
        fields = ("TypeObject1", "TypeObject2")
        labels = {
            "TypeObject1": "Type Object 1",
            "TypeObject2": "Type Object 2",
        }

        layout = [
            (
                "Text",
                '<h2 class="ui dividing header">Afwijkingenlijst twee type objecten</h2>',
            ),
            ("Text", '<i>Let op het verschil tussen de volgorde van de parameters. Appartement 0-50 m2 t.o.v. Grondgebonden Woning geeft een ander resultaat dan Grondgebonden Woning t.o.v. Appartement 0-50 m2. Namelijk, welke wel in de eerste parameter voorkomt maar niet in de tweede.</i>'),

            (
                "Two Fields",
                ("Field", "TypeObject1"),
                ("Field", "TypeObject2"),
            ),
        ]


class CompareFormDoelgroep(forms.Form):
    Doelgroep1 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep"
    )
    Doelgroep2 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep"
    )

    class Meta:
        model = PVEItem
        fields = ("Doelgroep1", "Doelgroep2")
        labels = {
            "Doelgroep1": "Doelgroep 1",
            "Doelgroep2": "Doelgroep 2",
        }

        layout = [
            ("Text", '<h2 class="ui dividing header">Afwijkingenlijst twee doelgroepen</h2>'),
            ("Text", '<i>Let op het verschil tussen de volgorde van de parameters. Appartement 0-50 m2 t.o.v. Grondgebonden Woning geeft een ander resultaat dan Grondgebonden Woning t.o.v. Appartement 0-50 m2. Namelijk, welke wel in de eerste parameter voorkomt maar niet in de tweede.</i>'),

            (
                "Two Fields",
                ("Field", "Doelgroep1"),
                ("Field", "Doelgroep2"),
            ),
        ]

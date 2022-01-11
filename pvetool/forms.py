# Author: Tames Boon
from django import forms
from django.contrib.gis import forms
from django.forms import ModelForm

from app.models import Bouwsoort, Doelgroep, PVEItem, TypeObject, PVEVersie
from project.models import BijlageToAnnotation, Project, CostType
from pvetool.models import BijlageToReply, CommentStatus
from users.models import CustomUser, Invitation, Organisatie


class LoginForm(forms.Form):
    attrs = {"type": "password"}

    username = forms.CharField(label="Gebruikersnaam of e-mail", max_length=100)
    password = forms.CharField(
        label="Wachtwoord", max_length=100, widget=forms.TextInput(attrs=attrs)
    )

    widgets = {
        "password": forms.PasswordInput(),
    }


class PVEVersieKeuzeForm(forms.Form):
    pve_versie = forms.ModelChoiceField(queryset=PVEVersie.objects.none(), label="PvE Versie")

    widgets = {
        "pve_versie": forms.Select(attrs={"class": "ui dropdown"}),
    }


class PVEParameterForm(ModelForm):
    Bouwsoort1 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort"
    )
    Bouwsoort2 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort"
    )
    Bouwsoort3 = forms.ModelChoiceField(
        queryset=Bouwsoort.objects.none(), label="Bouwsoort"
    )

    TypeObject1 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object"
    )
    TypeObject2 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object"
    )
    TypeObject3 = forms.ModelChoiceField(
        queryset=TypeObject.objects.none(), label="Type Object"
    )

    Doelgroep1 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep"
    )
    Doelgroep2 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep"
    )
    Doelgroep3 = forms.ModelChoiceField(
        queryset=Doelgroep.objects.none(), label="Doelgroep"
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
            "Bouwsoort1": "Bouwsoort",
            "Bouwsoort2": "Bouwsoort",
            "Bouwsoort3": "Bouwsoort",
            "TypeObject1": "Type Object",
            "TypeObject2": "Type Object",
            "TypeObject3": "Type Object",
            "Doelgroep1": "Doelgroep",
            "Doelgroep2": "Doelgroep",
            "Doelgroep3": "Doelgroep",
            "Smarthome": "Smarthome",
            "AED": "AED",
            "EntreeUpgrade": "Entree Upgrade",
            "Pakketdient": "Pakketdient",
            "JamesConcept": "James Concept",
        }

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


class KoppelDerdeUserForm(ModelForm):
    stakeholder = forms.ModelChoiceField(
        queryset=Organisatie.objects.none(), label="Stakeholder:"
    )
    
    widgets = {
        "stakeholder": forms.Select(
            attrs={"class": "ui dropdown"},
        ),
    }
    class Meta:
        model = Invitation
        fields = {
            "invitee",
        }
        labels = {
            "invitee": "E-Mail:",
        }
class PlusAccountForm(ModelForm):
    type_choices = (
        ("SOG", "Projectmanager"),
        ("SD", "Derde"),
    )

    rang = forms.ChoiceField(choices=type_choices)
    stakeholder = forms.ModelChoiceField(
        queryset=Organisatie.objects.none(), label="Stakeholder (optioneel):", required=False
    )
    class Meta:
        model = Invitation
        fields = {
            "invitee",
        }
        labels = {
            "rang": "Rang user:",
            "invitee": "E-Mail:",
        }
        
    def __init__(self, *args, **kwargs):
        super(PlusAccountForm, self).__init__(*args, **kwargs)
        self.fields["stakeholder"].required = False

class PlusDerdeToProjectForm(ModelForm):
    stakeholder = forms.ModelChoiceField(
        queryset=Organisatie.objects.none(), label="Stakeholder (optioneel):", required=False
    )

    class Meta:
        model = Invitation
        fields = {
            "project",
        }
        labels = {
            "invitee": "E-Mail:",
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
    item_id = forms.IntegerField(label="item_id")
    status = CachedModelChoiceField(
        objects=lambda: CommentStatus.objects.all()
    )
    annotation = forms.CharField(
        label="annotation", max_length=1000, widget=forms.Textarea, required=False
    )
    consequentCosts = forms.DecimalField(
        label="(Optioneel) Kosten", required=False
    )

    def __init__(self, *args, **kwargs):
        super(PVEItemAnnotationForm, self).__init__(*args, **kwargs)
        self.fields["status"].required = False


class BijlageToAnnotationForm(ModelForm):    
    class Meta:
        model = BijlageToAnnotation
        fields = ("ann", "attachment", "name")
        labels = {
            "ann": "Opmerking:",
            "attachment": "Bijlage:",
            "name": "Bijlagenaam (optioneel):"
        }
        widgets = {"ann": forms.HiddenInput()}
        
    def __init__(self, *args, **kwargs):
        super(BijlageToAnnotationForm, self).__init__(*args, **kwargs)
        self.fields["name"].required = True

class FirstAnnotationForm(forms.Form):
    annotation = forms.CharField(label="annotation", required=True, widget=forms.Textarea(attrs={'rows':3, 'cols':10}))

class FirstKostenverschilForm(forms.Form):
    kostenverschil = forms.DecimalField(
        label="Kosten", required=True
    )
    
    costtype = forms.ModelChoiceField(
        queryset=CostType.objects.all(), label=""
    )
    class Meta:
        layout = [
            (
                "Two Fields",
                ("Field", "kostenverschil"),
                ("Field", "costtype"),
            ),
        ]
class FirstStatusForm(forms.Form):
    status = CachedModelChoiceField(
        objects=lambda: CommentStatus.objects.all()
    )

class FirstBijlageForm(ModelForm):
    class Meta:
        model = BijlageToAnnotation
        fields = ("attachment", "ann", "name")
        labels = {"attachment": "", "ann": "", "name": "Bijlagenaam (optioneel):"}
        widgets = {"ann": forms.HiddenInput()}
        
    def __init__(self, *args, **kwargs):
        super(FirstBijlageForm, self).__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["attachment"].required = True

class PongBijlageForm(ModelForm):
    class Meta:
        model = BijlageToReply
        fields = ("attachment", "reply", "name")
        labels = {"attachment": "", "reply": "", "name": "Bijlagenaam (optioneel):"}
        widgets = {"reply": forms.HiddenInput()}
        
    def __init__(self, *args, **kwargs):
        super(PongBijlageForm, self).__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["attachment"].required = True


class AddOrganisatieForm(forms.Form):
    name = forms.CharField(max_length=100)

    class Meta:
        labels = {
            "name": "Stakeholder naam:",
        }


class AddUserToOrganisatieForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(), label=""
    )

    class Meta:
        labels = {
            "employee": "",
        }


class AddProjectmanagerToProjectForm(forms.Form):
    projectmanager = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(), label=""
    )

    class Meta:
        labels = {
            "projectmanager": "",
        }


class AddOrganisatieToProjectForm(forms.Form):
    stakeholder = forms.ModelChoiceField(
        queryset=Organisatie.objects.none(), label=""
    )

    class Meta:
        labels = {
            "stakeholder": "",
        }


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
            "name",
            "nummer",
            "organisaties",
            "vhe",
            "pensioenfonds",
            "statuscontract",
            "plaats",
            "first_annotate",
        )
        geom = forms.PointField()
        labels = {
            "name": "Projectnaam:",
            "nummer": "Projectnummer:",
            "plaats": "Plaats:",
            "vhe": "Aantal verhuureenheden:",
            "pensioenfonds": "Pensioenfonds:",
            "statuscontract": "Contractstatus:",
            "first_annotate": "Eerste statusaanwijzing naar:",
        }

        widgets = {
            "point": forms.OSMWidget(
                attrs={
                    "default_lat": 52.37,
                    "default_lon": 4.895,
                }
            ),
        }


class InviteProjectStartForm(forms.Form):
    projectmanager = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(), label="Projectmanager:"
    )
    organisaties = forms.ModelMultipleChoiceField(
        queryset=Organisatie.objects.none(), label="Organisaties (Voegt alle derden toe van een stakeholder):"
    )
    permitted = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(), label="Handmatig Derden:"
    )
    class Meta:
        widgets = {
            "permitted": forms.SelectMultiple(
                attrs={"class": "ui dropdown"},
            ),
            "organisaties": forms.SelectMultiple(
                attrs={"class": "ui dropdown"},
            ),
        }

class SOGAddDerdenForm(forms.Form):
    stakeholder = forms.ModelMultipleChoiceField(
        queryset=Organisatie.objects.none(), label="Stakeholders:"
    )
    
    class Meta:
        widgets = {
            "stakeholder": forms.SelectMultiple(
                attrs={"class": "ui dropdown"},
            ),
        }
            
    def __init__(self, *args, **kwargs):
        super(SOGAddDerdenForm, self).__init__(*args, **kwargs)
        self.fields["stakeholder"].required = True

class FirstFreezeForm(forms.Form):
    confirm = forms.BooleanField()

    class Meta:
        labels = {
            "confirm": "Vink aan als je alle statussen wil bevriezen en door wil sturen naar de derden om de opmerkingen te checken."
        }


class CommentReplyForm(forms.Form):
    CHOICES = [("True", "Ja"), ("False", "Nee")]

    comment_id = forms.IntegerField(label="comment_id")
    status = CachedModelChoiceField(
        objects=lambda: CommentStatus.objects.all()
    )
    annotation = forms.CharField(
        label="annotation", max_length=1000, widget=forms.Textarea, required=False
    )
    consequentCosts = forms.DecimalField(
        label="(Optioneel) Kosten Consequenties", required=False
    )
    accept = forms.ChoiceField(choices=CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        comm_id = kwargs.pop('comm_id', None)
        self.CHOICES = [("True", "Ja"), ("False", "Nee")]
        super(CommentReplyForm, self).__init__(*args, **kwargs)
        self.fields["status"].required = False
        self.fields["accept"].widget = forms.Select(attrs = {'onChange' : f"toggleShowInput({comm_id}, this);", "class":"select_accept", "id": f"id_accept_{comm_id}"})
        self.fields["accept"].choices = self.CHOICES


class BijlageToReplyForm(ModelForm):
    class Meta:
        model = BijlageToReply
        fields = ("reply", "attachment")
        labels = {
            "reply": "Reactie:",
            "attachment": "Bijlage:",
        }
        widgets = {"reply": forms.HiddenInput()}

class FinalPvEDownloadChoices(forms.Form):
    statuses = forms.ModelMultipleChoiceField(
        queryset=CommentStatus.objects.none(), label="Status(sen):"
    )
    
    class Meta:
        widgets = {
            "statuses": forms.SelectMultiple(
                attrs={"class": "ui dropdown"},
            ),
        }
            
    def __init__(self, *args, **kwargs):
        super(FinalPvEDownloadChoices, self).__init__(*args, **kwargs)
        self.fields["statuses"].required = True

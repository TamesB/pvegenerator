from django.contrib.gis.db import models as gismodels
from django.db import models

from users.models import CustomUser
from django.db.models.signals import pre_save
from django.dispatch import receiver
import inspect
import app.models as appmodels

class Abbonement(models.Model):
    soort = models.CharField(max_length=255, blank=True, null=True)

    # alles per maand
    kosten = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    projectlimiet = models.IntegerField(null=True, blank=True)
    werknemerlimiet = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.soort} - €{self.kosten} p/m - Projecten: {self.projectlimiet} - Werknemers: {self.werknemerlimiet}"

class Client(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    beheerder = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="owner_to_client")
    subscription = models.ForeignKey(Abbonement, on_delete=models.SET_NULL, null=True, blank=True)
    logo = models.FileField(blank=True, null=True, upload_to="KlantLogos")

    def __str__(self):
        return f"{self.name}"

class BeheerdersUitnodiging(models.Model):
    invitee = models.EmailField()
    client = models.ForeignKey(
        "project.Client", on_delete=models.CASCADE, null=True, blank=True, related_name="pending_invitation"
         )
    expires = models.DateTimeField(auto_now=False)
    key = models.CharField(max_length=100)

    def __str__(self):
        return f"Invitee: { self.invitee }. Expires { self.expires }"

class ContractStatus(models.Model):
    contrstatus = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.contrstatus}"


# Create your models here.
class Project(models.Model):
    nummer = models.FloatField(max_length=100, default=None)
    name = models.CharField(max_length=500, default=None)
    plaats = gismodels.PointField()
    plaatsnamen = models.CharField(max_length=250, default=None, null=True)
    vhe = models.FloatField(max_length=100, default=None)
    pensioenfonds = models.CharField(max_length=100, default=None)
    statuscontract = models.ForeignKey(ContractStatus, on_delete=models.SET_NULL, null=True, related_name="project")
    date_aangemaakt = models.DateTimeField(auto_now=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name="project")

    date_recent_verandering = models.DateTimeField(
        "recente_verandering", auto_now=True
    )

    PROJMANAGER = "SOG"
    DERDEN = "SD"

    FIRST_ANNOTATE_CHOICES = [
        (PROJMANAGER, 'Projectmanager'),
        (DERDEN, 'Stakeholder'),
    ]
    first_annotate = models.CharField(
        max_length=3,
        choices=FIRST_ANNOTATE_CHOICES,
        default=PROJMANAGER,
    )

    pve_versie = models.ForeignKey("app.PVEVersie", on_delete=models.SET_NULL, null=True, related_name="project")

    organisaties = models.ManyToManyField(
        "users.Organisatie",
        default=None,
        related_name="project",
        blank=True,
    )
    projectmanager = models.ForeignKey(
        "users.CustomUser",
        default=None,
        on_delete=models.SET_NULL,
        related_name="projectmanager",
        blank=True,
        null=True,
    )
    permitted = models.ManyToManyField(
        "users.CustomUser", default=None, related_name="projectspermitted"
    )
    pveconnected = models.BooleanField(blank=True, null=True, default=False)

    # frozen level 0: all derde kunnen +opmerking doen. Frozen level 1: alleen aangegeven derde door projectmanager kan
    # de statussen accepteren of een opmerking maken. De volgende even frozens zijn dan projectmanager behandelbaar,
    # en de oneven is behandelbaar door de derde. Zo trechteren alle regels naar uiteindelijke acceptatie van alle
    # statussen. Opmerkingen moeten wellicht bijgehouden worden.
    frozenLevel = models.IntegerField(default=0, null=True)
    fullyFrozen = models.BooleanField(default=False)
    commentchecker = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="commentchecker",
    )

    bouwsoort1 = models.ForeignKey(
        "app.Bouwsoort", on_delete=models.SET_NULL, blank=True, null=True
    )
    typeObject1 = models.ForeignKey(
        "app.TypeObject", on_delete=models.SET_NULL, blank=True, null=True
    )
    doelgroep1 = models.ForeignKey(
        "app.Doelgroep", on_delete=models.SET_NULL, blank=True, null=True
    )
    bouwsoort2 = models.ForeignKey(
        "app.Bouwsoort",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="SubBouwsoort",
    )
    typeObject2 = models.ForeignKey(
        "app.TypeObject",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="SubTypeObject",
    )
    doelgroep2 = models.ForeignKey(
        "app.Doelgroep",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="SubDoelgroep",
    )
    bouwsoort3 = models.ForeignKey(
        "app.Bouwsoort",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="SubSubBouwsoort",
    )
    typeObject3 = models.ForeignKey(
        "app.TypeObject",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="SubSubTypeObject",
    )
    doelgroep3 = models.ForeignKey(
        "app.Doelgroep",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="SubSubDoelgroep",
    )

    Smarthome = models.BooleanField(default=False)
    AED = models.BooleanField(default=False)
    EntreeUpgrade = models.BooleanField(default=False)
    Pakketdient = models.BooleanField(default=False)
    JamesConcept = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

class CostType(models.Model):
    type = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.type

class PVEItemAnnotation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None, related_name="annotation")
    item = models.ForeignKey("app.PVEItem", on_delete=models.CASCADE, default=None, related_name="annotation")
    annotation = models.TextField(max_length=1000, default=None, null=True)
    status = models.ForeignKey(
        "pvetool.CommentStatus", on_delete=models.CASCADE, default=None, null=True, related_name="annotation"
    )
    firststatus = models.ForeignKey(
        "pvetool.CommentStatus", on_delete=models.CASCADE, default=None, null=True, related_name="first_annotation"
    )
    user = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, default=None, null=True, related_name="annotation"
    )
    date = models.DateTimeField(auto_now=True)
    consequentCosts = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=None
    )
    costtype = models.ForeignKey(CostType, blank=True, null=True, on_delete=models.SET_NULL)
    attachment = models.BooleanField(default=False, blank=True, null=True)
    init_accepted = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return f"{self.annotation}"

    class Meta:
        ordering = ["-date"]


class BijlageToAnnotation(models.Model):
    ann = models.ForeignKey(PVEItemAnnotation, on_delete=models.CASCADE, default=None, related_name="attachmentobject")
    attachment = models.FileField(blank=True, null=True, upload_to="OpmerkingBijlages/")
    name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    
@receiver(pre_save, sender=Client)
def on_change(sender, instance: Client, **kwargs):

    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break
        else:
            request = None

    # sender is the object being saved
    activity = appmodels.Activity()
    activity.activity_type = "K"
    if not request.user.is_anonymous:
        activity.schuldige = request.user
    activity.save()
    
    if instance.id is None: # new object will be created
        activity.update = f"Nieuwe klant aangemaakt: '{ instance.client }'."
    else:
        previous = Client.objects.get(id=instance.id)
        if previous.name != instance.name: # field will be updatedssssssssssss
            activity.update = f"Klantnaam '{ previous.name }' veranderd naar '{ instance.client }'."
        if previous.beheerder != instance.beheerder: # field will be updated
            activity.update = f"Beheerder van '{ instance.client }' veranderd naar '{ instance.beheerder }'."
        if previous.logo != instance.logo: # field will be updated
            activity.update = f"Logo veranderd van klant '{ instance.client }'."
        if previous.subscription != instance.subscription: # field will be updated
            activity.update = f"Abonnement veranderd van klant '{ instance.client }'."
    
    activity.save()

@receiver(pre_save, sender=Project)
def on_change(sender, instance: Project, **kwargs):

    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break
        else:
            request = None

    # sender is the object being saved
    activity = appmodels.Activity()
    activity.activity_type = "P"
    if not request.user.is_anonymous:
        activity.schuldige = request.user
    activity.save()
    
    if instance.id is None: # new object will be created
        activity.update = f"Nieuw project van klant '{ request.user.client }': '{ instance.client }'."
    else:
        previous = Project.objects.get(id=instance.id)
        if previous.name != instance.name: # field will be updated
            activity.update = f"Projectnaam '{ previous.name }' van klant '{ instance.client }' veranderd naar '{ instance.client }'."
        if previous.pveconnected != instance.pveconnected: # field will be updated
            activity.update = f"Project '{ instance.name }' van klant '{ instance.client }': PvE verbonden (PvE Versie: '{ instance.pve_versie }')."
        if previous.fullyFrozen != instance.fullyFrozen: # field will be updated
            activity.update = f"Project '{ instance.name }' van klant '{ instance.client }': Opmerkingen bevroren."
        if previous.frozenLevel < instance.frozenLevel: # field will be updated
            activity.update = f"Project '{ instance.name }' van klant '{ instance.client }': Opmerkingen doorgestuurd (naar opmerkingsniveau '{instance.frozenLevel}')."
        if previous.projectmanager != instance.projectmanager: # field will be updated
            activity.update = f"Project '{ instance.name }' van klant '{ instance.client }': Projectmanager veranderd naar '{ instance.projectmanager }'."
            
        if list(previous.organisaties.all()) != list(instance.organisaties.all()): # field will be updated
            huidige_orgas = list(instance.organisaties.all())
            previous_orgas = list(previous.organisaties.all())
            verschil = list(set(huidige_orgas) - set(previous_orgas))
            if not verschil:
                negatief_verschil = list(set(previous_orgas) - set(huidige_orgas))
                activity.update = f"Project '{ instance.name }' van klant '{ instance.client }': Organisatie(s) verwijderd; '{ ', '.join(negatief_verschil) }'."
            else:
                activity.update = f"Project '{ instance.name }' van klant '{ instance.client }': Organisatie(s) toegevoegd; '{ ', '.join(verschil) }'."

    activity.save()
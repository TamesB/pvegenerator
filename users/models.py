from django.db import models
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.managers import CustomUserManager
from project.models import Beleggers

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=254, unique=True)
    email = models.EmailField(_('email field'), max_length=254)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    type_choices = (
        ('B', 'Beheerder'),
        ('SB', 'Syntrus Beheerder'),
        ('SOG', 'Syntrus Projectmanager'),
        ('SD', 'Syntrus Derden'),
    )

    type_user = models.CharField(max_length=3,
                                 choices=type_choices,
                                 default='SD')

    omschrijving = models.TextField(max_length=1000, default=None, blank=True, null=True)

    functie = models.CharField(max_length=500, default=None, blank=True, null=True)
    afdeling = models.CharField(max_length=500, default=None, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['type_user']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

# Create your models here.
class Invitation(models.Model):
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    invitee = models.EmailField()
    user_functie = models.CharField(max_length=500, default=None, blank=True, null=True)
    user_afdeling = models.CharField(max_length=500, default=None, blank=True, null=True)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    expires = models.DateTimeField(auto_now=False)
    key = models.CharField(max_length=100)

    def __str__(self):
        return f"{ self.inviter } invited { self.invitee }. Expires { self.expires }"
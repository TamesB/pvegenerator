from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(_('Gebruikersnaam'), unique=True, max_length=100)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    type_choices = (
        ('B', 'Beheerder'),
        ('OG', 'Opdrachtgever'),
        ('D', 'Derden'),
    )

    user_type = models.CharField(max_length=2,
                                 choices=type_choices,
                                 default='D')

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['user_type']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.name}: Type: {self.user_type}"

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from users.models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """

    def __init__(self, *args, **kargs):
        super(CustomUserCreationForm, self).__init__(*args, **kargs)

    class Meta:
        model = CustomUser
        fields = ("type_user", "omschrijving", "username", "password1")

class KoppelDerdeUser(forms.Form):
    email = forms.EmailField()

class AcceptInvitationForm(UserCreationForm):        
    class Meta:
        model = CustomUser
        fields = ("username", "password1", "password2")
        labels = {
            'username':'Gebruikersnaam:', 'password1':'Wachtwoord:', 'password2':'Herhaal wachtwoord:'
        }


class CustomUserChangeForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    def __init__(self, *args, **kargs):
        super(CustomUserChangeForm, self).__init__(*args, **kargs)

    class Meta:
        model = CustomUser
        fields = ("username",)

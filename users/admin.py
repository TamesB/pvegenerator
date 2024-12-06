from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.forms import CustomUserChangeForm, CustomUserCreationForm
from users.models import (
    CommentCheckInvitation,
    CustomUser,
    ForgotPassInvite,
    Invitation,
    Organisatie,
    LoginDetails
)


class CustomUserAdmin(UserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (("Personal info"), {"fields": ("first_name", "last_name")}),
        (("Permissions"), {"fields": ("type_user", "is_staff", "is_superuser")}),
        (("Important dates"), {"fields": ("last_login", "date_joined")}),
        (("Klantenorganisatie"), {"fields": ("client", "stakeholder")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("username", "password1", "password2")},
        ),
    )
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ("username", "first_name", "last_name", "is_staff")
    search_fields = ("username", "first_name", "last_name")
    ordering = ("username",)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CommentCheckInvitation)
admin.site.register(Invitation)
admin.site.register(Organisatie)
admin.site.register(ForgotPassInvite)
admin.site.register(LoginDetails)

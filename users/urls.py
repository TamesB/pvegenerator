# Author: Tames Boon

from django.urls import path

from . import views

# Urls for the specific app
urlpatterns = [
    path("<int:client_pk>/create", views.signup, name="acccreate"),
    path("<int:client_pk>/overview", views.accountOverview, name="accoverview"),
    path("<int:client_pk>/profile/<int:pk>", views.accountProfile, name="accprofile"),
    path("<int:client_pk>/forgotpass", views.ForgotPassword, name="forgotpass"),
    path("<int:client_pk>/passreset/<str:key>", views.ResetPassword, name="changepass"),
]

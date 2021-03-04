# Author: Tames Boon

from django.urls import path

from . import views

# Urls for the specific app
urlpatterns = [
    path('create', views.signup, name="acccreate"),
    path('overview', views.accountOverview, name="accoverview"),
    path('profile/<int:pk>', views.accountProfile, name="accprofile"),

    path('forgotpass', views.ForgotPassword, name="forgotpass"),
    path('passreset/<str:key>', views.ResetPassword, name="changepass"),

]

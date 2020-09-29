# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('', views.LoginView, name="login_syn"),
    path('logout', views.LogoutView, name="logout_syn"),
    path('dashboard', views.DashboardView, name="dashboard_syn"),
    path('generate', views.GeneratePVEView, name="generate_syn"),

    path('project/<int:id>', views.ViewProject, name="viewproject_syn"),
    path('project/pve', views.download_pve_overview, name="downloadPveOverview_syn"),
    path('project/<int:pk>/pve', views.download_pve, name="download_pve_syn"),
    path('comment', views.AddCommentOverview, name="plusopmerkingOverview_syn"),
    path('project/<int:pk>/comment/add', views.AddComment, name="plusopmerking_syn"),
    path('project/add', views.AddProject, name="plusproject_syn"),
    path('account/add', views.AddDerde, name="plusaccount_syn"),

    path('invite', views.AddDerde, name="invite_syn"),
    path('invite/<str:key>', views.AcceptInvite, name="acceptinvite_syn"),
]

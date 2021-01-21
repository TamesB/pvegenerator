# Author: Tames Boon

from django.urls import path
from django.conf.urls import include, url
from . import views

# Urls for the specific app
urlpatterns = [
    path('', views.LoginView, name="login_syn"),
    path('logout', views.LogoutView, name="logout_syn"),
    path('dashboard', views.DashboardView, name="dashboard_syn"),
    path('faq', views.FAQView, name="faq_syn"),
    path('generate', views.GeneratePVEView, name="generate_syn"),

    # organisaties (fondsen)
    path('organisaties', views.ManageOrganisaties, name="manageorganisaties_syn"),
    path('organisaties/add', views.AddOrganisatie, name="addorganisatie_syn"),
    path('organisaties/<int:pk>/delete', views.DeleteOrganisatie, name="deleteorganisatie_syn"),

    # project things
    path('projects', views.ViewProjectOverview, name="viewprojectoverview_syn"),
    path('project/<int:pk>', views.ViewProject, name="viewproject_syn"),
    path('project/pve', views.download_pve_overview, name="downloadPveOverview_syn"),
    path('project/<int:pk>/pve', views.download_pve, name="download_pve_syn"),
    path('comment', views.AddCommentOverview, name="plusopmerkingOverview_syn"),
    path('project/<int:pk>/comment/add', views.AddComment, name="plusopmerking_syn"),
    path('project/<int:pk>/comment/all', views.AllComments, name="alleopmerkingen_syn"),
    path('project/<int:pk>/comment/my', views.MyComments, name="mijnopmerkingen_syn"),
    path('project/<int:pk>/comment/my/deleteoverview', views.MyCommentsDelete, name="mijnopmerkingendelete_syn"),
    path('project/<int:project_id>/comment/<int:ann_id>/delete', views.deleteAnnotationPve, name="deleteAnnotationPve_syn"),
    path('project/<int:projid>/comment/my/<int:annid>', views.AddAnnotationAttachment, name="bijlageaanopmerking_syn"),
    path('project/<int:projid>/comment/my/<int:annid>/dl', views.DownloadAnnotationAttachment, name="downloadbijlageaanopmerking_syn"),
    path('project/<int:projid>/comment/my/<int:annid>/delete', views.VerwijderAnnotationAttachment, name="verwijderbijlageopmerking_syn"),

    path('project/add', views.AddProject, name="plusproject_syn"),
    path('project/<int:pk>/addusers', views.InviteUsersToProject, name="addusersproject_syn"),
    path('project/<int:pk>/addpve', views.ConnectPVE, name="connectpve_syn"),
    path('account/add', views.AddAccount, name="plusaccount_syn"),

    path('invite', views.AddAccount, name="invite_syn"),
    path('invite/<str:key>', views.AcceptInvite, name="acceptinvite_syn"),

    # firstfreezing
    path('project/<int:pk>/firstfreeze', views.FirstFreeze, name="firstfreeze_syn"),

    # check comments after freeze
    path('project/<int:proj_id>/check', views.CheckComments, name="commentscheck_syn"),
    path('project/<int:proj_id>/frozenopmerkingen', views.FrozenProgressView, name="frozenprogress_syn"),

]

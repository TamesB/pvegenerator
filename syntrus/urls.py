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

    # organisatie beheer (groep van derden) CRUD
    path('organisaties', views.ManageOrganisaties, name="manageorganisaties_syn"),
    path('organisaties/add', views.AddOrganisatie, name="addorganisatie_syn"),
    path('organisaties/<int:pk>/users/add', views.AddUserOrganisatie, name="addusersorganisatie_syn"),
    path('organisaties/<int:pk>/delete', views.DeleteOrganisatie, name="deleteorganisatie_syn"),

    # projectbeheer CRUD
    path('projectbeheer', views.ManageProjects, name="manageprojecten_syn"),
    path('projectbeheer/<int:pk>/addprojmanager', views.AddProjectManager, name="projectenaddprojmanager_syn"),
    path('projectbeheer/<int:pk>/addorganisatie', views.AddOrganisatieToProject, name="projectenaddorganisatie_syn"),

    # werknemers beheer
    path('werknemers', views.ManageWerknemers, name="managewerknemers_syn"),

    # adding users and user accepting invitation
    path('invite', views.AddAccount, name="invite_syn"),
    path('invite/<str:key>', views.AcceptInvite, name="acceptinvite_syn"),
    path('account/add', views.AddAccount, name="plusaccount_syn"),
    path('project/<int:pk>/addusers', views.InviteUsersToProject, name="addusersproject_syn"),

    # project things
    path('projects', views.ViewProjectOverview, name="viewprojectoverview_syn"),
    path('project/<int:pk>', views.ViewProject, name="viewproject_syn"),
    path('project/pve', views.download_pve_overview, name="downloadPveOverview_syn"),
    path('project/<int:pk>/pve', views.download_pve, name="download_pve_syn"),
    path('comment', views.AddCommentOverview, name="plusopmerkingOverview_syn"),
    path('project/<int:pk>/comment/add', views.AddComment, name="plusopmerking_syn"),
    path('project/<int:pk>/comment/all', views.AllComments, name="alleopmerkingen_syn"),
    path('project/add', views.AddProject, name="plusproject_syn"),
    path('project/<int:pk>/addpve', views.ConnectPVE, name="connectpve_syn"),

    # every first annotation action (from projectmanagers side) CRUD
    path('project/<int:pk>/comment/my', views.MyComments, name="mijnopmerkingen_syn"),
    path('project/<int:pk>/comment/my/deleteoverview', views.MyCommentsDelete, name="mijnopmerkingendelete_syn"),
    path('project/<int:project_id>/comment/<int:ann_id>/delete', views.deleteAnnotationPve, name="deleteAnnotationPve_syn"),
    path('project/<int:projid>/comment/my/<int:annid>', views.AddAnnotationAttachment, name="bijlageaanopmerking_syn"),
    path('project/<int:projid>/comment/my/<int:annid>/dl', views.DownloadAnnotationAttachment, name="downloadbijlageaanopmerking_syn"),
    path('project/<int:projid>/comment/my/<int:annid>/delete', views.VerwijderAnnotationAttachment, name="verwijderbijlageopmerking_syn"),

    # eerste verzending naar derde partijen voor reactie
    path('project/<int:pk>/firstfreeze', views.FirstFreeze, name="firstfreeze_syn"),

    # check comments after freeze
    path('project/<int:proj_id>/check', views.CheckComments, name="commentscheck_syn"),

    # CRUD of replies and attachments to replies
    path('project/<int:pk>/replies/my', views.MyReplies, name="myreplies_syn"),
    path('project/<int:pk>/replies/my/deleteoverview', views.MyRepliesDelete, name="replydeleteoverview_syn"),
    path('project/<int:pk>/replies/<int:reply_id>/delete', views.DeleteReply, name="deletereply_syn"),
    path('project/<int:pk>/replies/my/<int:reply_id>', views.AddReplyAttachment, name="addreplyattachment_syn"),
    path('project/<int:pk>/replies/my/<int:reply_id>/dl', views.DownloadReplyAttachment, name="downloadreplyattachment_syn"),
    path('project/<int:pk>/replies/my/<int:reply_id>/delete', views.DeleteReplyAttachment, name="deletereplyattachment_syn"),

    # send back to projectmanager (and back to third parties)
    path('project/<int:pk>/sendreplies', views.SendReplies, name="sendreplies_syn"),

    # final freeze after every comment is accepted.
    path('project/<int:pk>/finalfreeze', views.FinalFreeze, name="finalfreeze_syn"),

]

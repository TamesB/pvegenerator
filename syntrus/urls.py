# Author: Tames Boon

from django.urls import path

from .views import (
    actionsPingPong,
    actionsProject,
    base,
    crudFirstAnnotate,
    crudPartijen,
    crudPingPong,
    crudProjects,
    crudWerknemers,
    utils
)

# Urls for the specific app
urlpatterns = [
    # base functions
    path("<int:client_pk>", base.LoginView, name="login_syn"),
    path("<int:client_pk>/logout", base.LogoutView, name="logout_syn"),
    path("<int:client_pk>/dashboard", base.DashboardView, name="dashboard_syn"),
    path("<int:client_pk>/faq", base.FAQView, name="faq_syn"),
    path("<int:client_pk>/generate/kiespve", base.KiesPVEGenerate, name="kiespvegenerate"),
    path("<int:client_pk>/generate/<int:versie_pk>", base.GeneratePVEView, name="generate_syn"),

    # organisatie beheer (groep van derden) CRUD
    path("<int:client_pk>/organisaties", crudPartijen.ManageOrganisaties, name="manageorganisaties_syn"),
    path("<int:client_pk>/organisaties/add", crudPartijen.AddOrganisatie, name="addorganisatie_syn"),
    path(
        "<int:client_pk>/organisaties/<int:pk>/users/add",
        crudPartijen.AddUserOrganisatie,
        name="addusersorganisatie",
    ),
    path(
        "<int:client_pk>/organisaties/<int:pk>/users/get",
        crudPartijen.GetUsersInOrganisatie,
        name="getusersorganisatie",
    ),
    path(
        "<int:client_pk>/organisaties/<int:pk>/delete",
        crudPartijen.DeleteOrganisatie,
        name="deleteorganisatie_syn",
    ),

    # projectbeheer CRUD
    path("<int:client_pk>/projectbeheer", crudProjects.ManageProjects, name="manageprojecten_syn"),
    path("<int:client_pk>/project/add", crudProjects.AddProject, name="plusproject_syn"),
    path("<int:client_pk>/project/projectbeheer/<int:pk>/projectmanager", crudProjects.GetProjectManagerOfProject, name="getprojectmanager_syn"),
    path(
        "<int:client_pk>/projectbeheer/<int:pk>/addprojmanagertest",
        crudProjects.AddProjectManagerToProject,
        name="addprojmanagertoproject_syn",
    ),
    path(
        "<int:client_pk>/projectbeheer/<int:pk>/getorganisaties",
        crudProjects.GetOrganisatieToProject,
        name="getprojectpartijen",
    ),
    path(
        "<int:client_pk>/projectbeheer/<int:pk>/addorganisatie",
        crudProjects.AddOrganisatieToProject,
        name="projectaddpartijform",
    ),
    path("<int:client_pk>/project/addsd/<int:pk>", crudProjects.SOGAddDerdenToProj, name="sogaddderden"),

    # werknemers beheer "CRUD"
    path("<int:client_pk>/werknemers", crudWerknemers.ManageWerknemers, name="managewerknemers_syn"),
    path("<int:client_pk>/invite", crudWerknemers.AddAccount, name="invite_syn"),
    path("<int:client_pk>/invite/<str:key>", crudWerknemers.AcceptInvite, name="acceptinvite_syn"),
    path("<int:client_pk>/account/add", crudWerknemers.AddAccount, name="plusaccount_syn"),
    path(
        "<int:client_pk>/project/<int:pk>/addusers",
        crudWerknemers.InviteUsersToProject,
        name="addusersproject_syn",
    ),

    # project Actions
    path("<int:client_pk>/projects", actionsProject.ViewProjectOverview, name="viewprojectoverview_syn"),
    path("<int:client_pk>/project/<int:pk>", actionsProject.ViewProject, name="viewproject_syn"),
    path("<int:client_pk>/project/pve", actionsProject.download_pve_overview, name="downloadPveOverview_syn"),
    path("<int:client_pk>/project/<int:pk>/pve", actionsProject.download_pve, name="download_pve_syn"),
    path("<int:client_pk>/project/<int:pk>/<int:versie_pk>/addpve", actionsProject.ConnectPVE, name="connectpve_syn"),
    path("<int:client_pk>/project/<int:pk>/addpvepartial", actionsProject.KiesPVE, name="kiespveversie"),

    # first annotate crud
    path("<int:client_pk>/comment", crudFirstAnnotate.AddCommentOverview, name="plusopmerkingOverview_syn"),
    path("<int:client_pk>/project/<int:pk>/comment/add", crudFirstAnnotate.AddComment, name="plusopmerking_syn"),
    path("<int:client_pk>/project/<int:pk>/comment/all", crudFirstAnnotate.AllComments, name="alleopmerkingen_syn"),
    path("<int:client_pk>/project/<int:pk>/comment/my", crudFirstAnnotate.MyComments, name="mijnopmerkingen_syn"),
    path(
        "<int:client_pk>/project/<int:pk>/comment/my/deleteoverview",
        crudFirstAnnotate.MyCommentsDelete,
        name="mijnopmerkingendelete_syn",
    ),
    path(
        "<int:client_pk>/project/<int:project_id>/comment/<int:ann_id>/delete",
        crudFirstAnnotate.deleteAnnotationPve,
        name="deleteAnnotationPve_syn",
    ),
    path(
        "<int:client_pk>/project/<int:projid>/comment/my/<int:annid>",
        crudFirstAnnotate.AddAnnotationAttachment,
        name="bijlageaanopmerking_syn",
    ),
    path(
        "<int:client_pk>/project/<int:projid>/comment/my/<int:annid>/dl",
        utils.DownloadAnnotationAttachment,
        name="downloadbijlageaanopmerking_syn",
    ),
    path(
        "<int:client_pk>/project/<int:projid>/comment/my/<int:annid>/delete",
        crudFirstAnnotate.VerwijderAnnotationAttachment,
        name="verwijderbijlageopmerking_syn",
    ),
    path("<int:client_pk>/project/<int:pk>/firstfreeze", actionsPingPong.FirstFreeze, name="firstfreeze_syn"),

    # Ping pong process
    path("<int:client_pk>/project/<int:proj_id>/check", crudPingPong.CheckComments, name="commentscheck_syn"),
    # CRUD of replies and attachments to replies
    path("<int:client_pk>/project/<int:pk>/replies/my", crudPingPong.MyReplies, name="myreplies_syn"),
    path(
        "<int:client_pk>/project/<int:pk>/replies/my/deleteoverview",
        crudPingPong.MyRepliesDelete,
        name="replydeleteoverview_syn",
    ),
    path(
        "<int:client_pk>/project/<int:pk>/replies/<int:reply_id>/delete",
        crudPingPong.DeleteReply,
        name="deletereply_syn",
    ),
    path(
        "<int:client_pk>/project/<int:pk>/replies/my/<int:reply_id>",
        crudPingPong.AddReplyAttachment,
        name="addreplyattachment_syn",
    ),
    path(
        "<int:client_pk>/project/<int:pk>/replies/my/<int:reply_id>/dl",
        utils.DownloadReplyAttachment,
        name="downloadreplyattachment_syn",
    ),
    path(
        "<int:client_pk>/project/<int:pk>/replies/my/<int:reply_id>/delete",
        crudPingPong.DeleteReplyAttachment,
        name="deletereplyattachment_syn",
    ),
    # send back to projectmanager (and back to third parties)
    path("<int:client_pk>/project/<int:pk>/sendreplies", actionsPingPong.SendReplies, name="sendreplies_syn"),
    
    # final freeze after every comment is accepted.
    path("<int:client_pk>/project/<int:pk>/finalfreeze", actionsPingPong.FinalFreeze, name="finalfreeze_syn"),
]

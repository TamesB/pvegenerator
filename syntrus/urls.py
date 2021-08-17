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
    path("", base.LoginView, name="login_syn"),
    path("logout", base.LogoutView, name="logout_syn"),
    path("dashboard", base.DashboardView, name="dashboard_syn"),
    path("faq", base.FAQView, name="faq_syn"),
    path("generate", base.GeneratePVEView, name="generate_syn"),

    # organisatie beheer (groep van derden) CRUD
    path("organisaties", crudPartijen.ManageOrganisaties, name="manageorganisaties_syn"),
    path("organisaties/add", crudPartijen.AddOrganisatie, name="addorganisatie_syn"),
    path(
        "organisaties/<int:pk>/users/add",
        crudPartijen.AddUserOrganisatie,
        name="addusersorganisatie_syn",
    ),
    path(
        "organisaties/<int:pk>/delete",
        crudPartijen.DeleteOrganisatie,
        name="deleteorganisatie_syn",
    ),

    # projectbeheer CRUD
    path("projectbeheer", crudProjects.ManageProjects, name="manageprojecten_syn"),
    path("project/add", crudProjects.AddProject, name="plusproject_syn"),
    path(
        "projectbeheer/<int:pk>/addprojmanager",
        crudProjects.AddProjectManager,
        name="projectenaddprojmanager_syn",
    ),
    path(
        "projectbeheer/<int:pk>/addorganisatie",
        crudProjects.AddOrganisatieToProject,
        name="projectenaddorganisatie_syn",
    ),
    path("project/addsd/<int:pk>", crudProjects.SOGAddDerdenToProj, name="sogaddderden"),

    # werknemers beheer "CRUD"
    path("werknemers", crudWerknemers.ManageWerknemers, name="managewerknemers_syn"),
    path("invite", crudWerknemers.AddAccount, name="invite_syn"),
    path("invite/<str:key>", crudWerknemers.AcceptInvite, name="acceptinvite_syn"),
    path("account/add", crudWerknemers.AddAccount, name="plusaccount_syn"),
    path(
        "project/<int:pk>/addusers",
        crudWerknemers.InviteUsersToProject,
        name="addusersproject_syn",
    ),

    # project Actions
    path("projects", actionsProject.ViewProjectOverview, name="viewprojectoverview_syn"),
    path("project/<int:pk>", actionsProject.ViewProject, name="viewproject_syn"),
    path("project/pve", actionsProject.download_pve_overview, name="downloadPveOverview_syn"),
    path("project/<int:pk>/pve", actionsProject.download_pve, name="download_pve_syn"),
    path("project/<int:pk>/addpve", actionsProject.ConnectPVE, name="connectpve_syn"),

    # first annotate crud
    path("comment", crudFirstAnnotate.AddCommentOverview, name="plusopmerkingOverview_syn"),
    path("project/<int:pk>/comment/add", crudFirstAnnotate.AddComment, name="plusopmerking_syn"),
    path("project/<int:pk>/comment/all", crudFirstAnnotate.AllComments, name="alleopmerkingen_syn"),
    path("project/<int:pk>/comment/my", crudFirstAnnotate.MyComments, name="mijnopmerkingen_syn"),
    path(
        "project/<int:pk>/comment/my/deleteoverview",
        crudFirstAnnotate.MyCommentsDelete,
        name="mijnopmerkingendelete_syn",
    ),
    path(
        "project/<int:project_id>/comment/<int:ann_id>/delete",
        crudFirstAnnotate.deleteAnnotationPve,
        name="deleteAnnotationPve_syn",
    ),
    path(
        "project/<int:projid>/comment/my/<int:annid>",
        crudFirstAnnotate.AddAnnotationAttachment,
        name="bijlageaanopmerking_syn",
    ),
    path(
        "project/<int:projid>/comment/my/<int:annid>/dl",
        utils.DownloadAnnotationAttachment,
        name="downloadbijlageaanopmerking_syn",
    ),
    path(
        "project/<int:projid>/comment/my/<int:annid>/delete",
        crudFirstAnnotate.VerwijderAnnotationAttachment,
        name="verwijderbijlageopmerking_syn",
    ),
    path("project/<int:pk>/firstfreeze", actionsPingPong.FirstFreeze, name="firstfreeze_syn"),

    # Ping pong process
    path("project/<int:proj_id>/check", crudPingPong.CheckComments, name="commentscheck_syn"),
    # CRUD of replies and attachments to replies
    path("project/<int:pk>/replies/my", crudPingPong.MyReplies, name="myreplies_syn"),
    path(
        "project/<int:pk>/replies/my/deleteoverview",
        crudPingPong.MyRepliesDelete,
        name="replydeleteoverview_syn",
    ),
    path(
        "project/<int:pk>/replies/<int:reply_id>/delete",
        crudPingPong.DeleteReply,
        name="deletereply_syn",
    ),
    path(
        "project/<int:pk>/replies/my/<int:reply_id>",
        crudPingPong.AddReplyAttachment,
        name="addreplyattachment_syn",
    ),
    path(
        "project/<int:pk>/replies/my/<int:reply_id>/dl",
        utils.DownloadReplyAttachment,
        name="downloadreplyattachment_syn",
    ),
    path(
        "project/<int:pk>/replies/my/<int:reply_id>/delete",
        crudPingPong.DeleteReplyAttachment,
        name="deletereplyattachment_syn",
    ),
    # send back to projectmanager (and back to third parties)
    path("project/<int:pk>/sendreplies", actionsPingPong.SendReplies, name="sendreplies_syn"),
    
    # final freeze after every comment is accepted.
    path("project/<int:pk>/finalfreeze", actionsPingPong.FinalFreeze, name="finalfreeze_syn"),
]

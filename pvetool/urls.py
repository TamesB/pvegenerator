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
    path("<int:client_pk>/accept/<str:key>", base.BeheerdersAcceptUitnodiging, name="acceptuitnodigingbeheerder"),
    path("<int:client_pk>/logout", base.LogoutView, name="logout_syn"),
    path("<int:client_pk>/dashboard", base.DashboardView, name="dashboard_syn"),
    path("<int:client_pk>/faq", base.FAQView, name="faq_syn"),
    path("<int:client_pk>/generate/kiespve", base.KiesPVEGenerate, name="kiespvegenerate"),
    path("<int:client_pk>/generate/<int:version_pk>", base.GeneratePVEView, name="generate_syn"),

    # stakeholder beheer (groep van derden) CRUD
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
    path(
        "<int:client_pk>/organisaties/<int:organisatie_pk>/removeproj/<int:project_pk>",
        crudPartijen.OrganisatieRemoveFromProject,
        name="organisatieremovefromproject",
    ),
    path(
        "<int:client_pk>/organisaties/<int:organisatie_pk>/removeuser/<int:user_pk>",
        crudPartijen.GebruikerRemoveFromOrganisatie,
        name="userremovefromorganisatie",
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
    path("<int:client_pk>/project/delete/<int:pk>", crudProjects.DeleteProject, name="deleteproject"),

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
    path("<int:client_pk>/project/<int:pk>/<int:version_pk>/addpve", actionsProject.ConnectPVE, name="connectpve_syn"),
    path("<int:client_pk>/project/<int:pk>/addpvepartial", actionsProject.KiesPVE, name="kiespveversie"),

    # first annotate crud
    path("<int:client_pk>/comment", crudFirstAnnotate.AddCommentOverview, name="plusopmerkingOverview_syn"),
    path("<int:client_pk>/project/<int:pk>/comment/add", crudFirstAnnotate.AddComment, name="plusopmerking_syn"),
    path("<int:client_pk>/getparagraphsfirstannotate/<int:pk>/<int:chapter_pk>", crudFirstAnnotate.GetParagravenFirstAnnotate, name="getparagraphsfirstannotate"),
    path("<int:client_pk>/getitemsfirstannotate/<int:pk>/<int:chapter_pk>/<int:paragraph_id>", crudFirstAnnotate.GetItemsFirstAnnotate, name="getitemsfirstannotate"),
    path("<int:client_pk>/detailfirststatus/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailStatusFirst, name="detailfirststatus"),
    path("<int:client_pk>/detailitemfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailItemFirst, name="detailitemfirst"),
    path("<int:client_pk>/detailfirstannotation/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailAnnotationFirst, name="detailfirstannotation"),
    path("<int:client_pk>/detailfirstkostenverschil/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailKostenverschilFirst, name="detailfirstkostenverschil"),
    path("<int:client_pk>/addstatusfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.AddStatusFirst, name="addstatusfirst"),
    path("<int:client_pk>/addannotationfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.AddAnnotationFirst, name="addannotationfirst"),
    path("<int:client_pk>/addkostenverschilfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.AddKostenverschilFirst, name="addkostenverschilfirst"),
    path("<int:client_pk>/deletestatusfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DeleteStatusFirst, name="deletestatusfirst"),
    path("<int:client_pk>/deleteannotationfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DeleteAnnotationFirst, name="deleteannotationfirst"),
    path("<int:client_pk>/deletekostenverschilfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DeleteKostenverschilFirst, name="deletekostenverschilfirst"),
    path("<int:client_pk>/deleteattachmentfirst/<int:project_pk>/<int:annotation_pk>/<int:pk>", crudFirstAnnotate.DeleteBijlageFirst, name="deleteattachmentfirst"),
    path("<int:client_pk>/addattachmentfirst/<int:project_pk>/<int:item_pk>/<int:annotation_pk>/<int:attachment_id>", crudFirstAnnotate.AddBijlageFirst, name="addattachmentfirst"),
    path(
        "<int:client_pk>/project/<int:projid>/comment/my/<int:annid>/<int:attachment_id>/dl",
        utils.DownloadAnnotationAttachment,
        name="downloadattachmentaanopmerking_syn",
    ),
    path("<int:client_pk>/project/<int:pk>/firstfreeze", actionsPingPong.FirstFreeze, name="firstfreeze_syn"),

    # Ping pong process
    path("<int:client_pk>/project/<int:proj_id>/check", crudPingPong.CheckComments, name="commentscheck_syn"),
    path("<int:client_pk>/getparagraphspingpong/<int:pk>/<int:chapter_pk>/<int:type>/<int:accept>", crudPingPong.GetParagravenPingPong, name="getparagraphspingpong"),
    path("<int:client_pk>/getitemspingpong/<int:pk>/<int:chapter_pk>/<int:paragraph_id>/<int:type>/<int:accept>", crudPingPong.GetItemsPingPong, name="getitemspingpong"),
    
    # first acceptation process per rule
    path("<int:client_pk>/detailpong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailAcceptPong, name="detailpongaccept"),
    path("<int:client_pk>/firstacceptsteppong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.FirstAcceptStepPong, name="firstacceptsteppong"),
    path("<int:client_pk>/nonacceptitempong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.NonAcceptItemPong, name="nonacceptitempong"),
        path("<int:client_pk>/acceptitempong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AcceptItemPong, name="acceptitempong"),

    # details after first accept/deny per rule
    path("<int:client_pk>/redocommentdetail/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.RedoCommentDetail, name="redocommentdetail"),
    path("<int:client_pk>/detailitempong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailItemPong, name="detailitempong"),
    path("<int:client_pk>/detailpongstatus/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailStatusPong, name="detailpongstatus"),
    path("<int:client_pk>/detailpongreply/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailReplyPong, name="detailpongreply"),
    path("<int:client_pk>/detailpongkostenverschil/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailKostenverschilPong, name="detailpongkostenverschil"),
    path("<int:client_pk>/redocommentpong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.RedoCommentPong, name="redocommentpong"),
    
    # cruds of comments/costs/attachments
    path("<int:client_pk>/addstatuspong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AddStatusPong, name="addstatuspong"),
    path("<int:client_pk>/addreplypong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AddReplyPong, name="addreplypong"),
    path("<int:client_pk>/addkostenverschilpong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AddKostenverschilPong, name="addkostenverschilpong"),
    path("<int:client_pk>/addattachmentpong/<int:project_pk>/<int:item_pk>/<int:annotation_pk>/<int:type>/<int:new>/<int:attachment_id>", crudPingPong.AddBijlagePong, name="addattachmentpong"),
    path("<int:client_pk>/deletestatuspong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DeleteStatusPong, name="deletestatuspong"),
    path("<int:client_pk>/deletereplypong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DeleteReplyPong, name="deletereplypong"),
    path("<int:client_pk>/deletekostenverschilpong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DeleteKostenverschilPong, name="deletekostenverschilpong"),

    # Safe attachment downloads AWS
    path(
        "<int:client_pk>/project/<int:pk>/replies/my/<int:reply_id>/<int:attachment_id>/dl",
        utils.DownloadReplyAttachment,
        name="downloadreplyattachment_syn",
    ),
    # send back to other party
    path("<int:client_pk>/project/<int:pk>/sendreplies", actionsPingPong.SendReplies, name="sendreplies_syn"),
    
    # final freeze after every comment is accepted.
    path("<int:client_pk>/project/<int:pk>/finalfreeze", actionsPingPong.FinalFreeze, name="finalfreeze_syn"),
]

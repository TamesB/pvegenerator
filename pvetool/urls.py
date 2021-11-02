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
    path("<int:client_pk>/getparagravenfirstannotate/<int:pk>/<int:hoofdstuk_pk>", crudFirstAnnotate.GetParagravenFirstAnnotate, name="getparagravenfirstannotate"),
    path("<int:client_pk>/getitemsfirstannotate/<int:pk>/<int:hoofdstuk_pk>/<int:paragraaf_id>", crudFirstAnnotate.GetItemsFirstAnnotate, name="getitemsfirstannotate"),
    path("<int:client_pk>/detailfirststatus/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailStatusFirst, name="detailfirststatus"),
    path("<int:client_pk>/detailfirstannotation/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailAnnotationFirst, name="detailfirstannotation"),
    path("<int:client_pk>/detailfirstkostenverschil/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.DetailKostenverschilFirst, name="detailfirstkostenverschil"),
    path("<int:client_pk>/addstatusfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.AddStatusFirst, name="addstatusfirst"),
    path("<int:client_pk>/addannotationfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.AddAnnotationFirst, name="addannotationfirst"),
    path("<int:client_pk>/addkostenverschilfirst/<int:project_pk>/<int:item_pk>", crudFirstAnnotate.AddKostenverschilFirst, name="addkostenverschilfirst"),
    path("<int:client_pk>/addbijlagefirst/<int:project_pk>/<int:item_pk>/<int:annotation_pk>", crudFirstAnnotate.AddBijlageFirst, name="addbijlagefirst"),
    path(
        "<int:client_pk>/project/<int:projid>/comment/my/<int:annid>/dl",
        utils.DownloadAnnotationAttachment,
        name="downloadbijlageaanopmerking_syn",
    ),
    path("<int:client_pk>/project/<int:pk>/firstfreeze", actionsPingPong.FirstFreeze, name="firstfreeze_syn"),

    # Ping pong process
    path("<int:client_pk>/project/<int:proj_id>/check", crudPingPong.CheckComments, name="commentscheck_syn"),
    path("<int:client_pk>/getparagravenpingpong/<int:pk>/<int:hoofdstuk_pk>/<int:type>/<int:accept>", crudPingPong.GetParagravenPingPong, name="getparagravenpingpong"),
    path("<int:client_pk>/getitemspingpong/<int:pk>/<int:hoofdstuk_pk>/<int:paragraaf_id>/<int:type>/<int:accept>", crudPingPong.GetItemsPingPong, name="getitemspingpong"),
    path("<int:client_pk>/detailitempong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailItemPong, name="detailitempong"),
    path("<int:client_pk>/detailpongstatus/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailStatusPong, name="detailpongstatus"),
    path("<int:client_pk>/toggleaccept/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailAcceptPong, name="detailpongaccept"),
    path("<int:client_pk>/acceptitempong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AcceptItemPong, name="acceptitempong"),
    path("<int:client_pk>/nonacceptitempong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.NonAcceptItemPong, name="nonacceptitempong"),
    path("<int:client_pk>/detailpongreply/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailReplyPong, name="detailpongreply"),
    path("<int:client_pk>/detailpongkostenverschil/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DetailKostenverschilPong, name="detailpongkostenverschil"),
    path("<int:client_pk>/addstatuspong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AddStatusPong, name="addstatuspong"),
    path("<int:client_pk>/addreplypong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AddReplyPong, name="addreplypong"),
    path("<int:client_pk>/addkostenverschilpong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.AddKostenverschilPong, name="addkostenverschilpong"),
    path("<int:client_pk>/addbijlagepong/<int:project_pk>/<int:item_pk>/<int:annotation_pk>/<int:type>", crudPingPong.AddBijlagePong, name="addbijlagepong"),
    path("<int:client_pk>/deletestatuspong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DeleteStatusPong, name="deletestatuspong"),
    path("<int:client_pk>/deletereplypong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DeleteReplyPong, name="deletereplypong"),
    path("<int:client_pk>/deletekostenverschilpong/<int:project_pk>/<int:item_pk>/<int:type>", crudPingPong.DeleteKostenverschilPong, name="deletekostenverschilpong"),

    # CRUD of replies and attachments to replies
    path(
        "<int:client_pk>/project/<int:pk>/replies/my/<int:reply_id>/dl",
        utils.DownloadReplyAttachment,
        name="downloadreplyattachment_syn",
    ),
    # send back to projectmanager (and back to third parties)
    path("<int:client_pk>/project/<int:pk>/sendreplies", actionsPingPong.SendReplies, name="sendreplies_syn"),
    
    # final freeze after every comment is accepted.
    path("<int:client_pk>/project/<int:pk>/finalfreeze", actionsPingPong.FinalFreeze, name="finalfreeze_syn"),
]

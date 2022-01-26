# Author: Tames Boon

from django.urls import path

from . import views

# Urls for the specific app
urlpatterns = [
    path("", views.LoginPageView.as_view(), name="login"),
    path("dashboard", views.DashboardView.as_view(), name="dashboard"),
    path("clients", views.KlantOverzicht.as_view(), name="clientoverzicht"),
    path("clients/add", views.KlantToevoegen, name="clienttoevoegen"),
    path("clients/<int:client_pk>/delete", views.KlantVerwijderen.as_view(), name="clientverwijderen"),
    path("clients/logo/<int:client_pk>", views.GetLogo.as_view(), name="logoclientdetail"),
    path("clients/logo/<int:client_pk>/add", views.LogoKlantForm, name="logoclientform"),
    path("clients/beheerder/<int:client_pk>", views.GetBeheerderKlant, name="getbeheerderclient"),
    path("clients/beheerder/<int:client_pk>/add", views.BeheerderKlantForm, name="beheerderclientform"),
    path("logout", views.LogoutView.as_view(), name="logout"),

    path(
        "clientsversie",
        views.PVEBeleggerVersieOverview,
        name="clientversieoverview",
    ),
    path(
        "bewerkpveoverview/<int:version_pk>",
        views.PVEBewerkOverview,
        name="pvebewerkoverview",
    ),
    
    path("addpveversieform/<int:client_pk>", views.AddPvEVersie, name="addpveversieform"),
    path("clientversietable/<int:client_pk>", views.BeleggerVersieTable, name="pveversietable"),
    path("pveversiedetail/<int:version_pk>", views.PVEVersieDetail, name="getpveversie"),
    path("getpveversiedetail/<int:version_pk>", views.GetPveVersieDetail, name="getpveversiedetail"),
    path("pveversienameform/<int:version_pk>", views.PveVersieEditName, name="editpveversiename"),
    path("deletepveversie/<int:client_pk>/<int:version_pk>", views.DeletePVEVersie, name="deletepveversie"),
    path("pveactivity/<int:version_pk>", views.VersieActiviteit, name="getpveactivity"),
    path("makeactive/<int:version_pk>", views.ActivateVersie, name="maakactief"),
    path("makeinactive/<int:version_pk>", views.DeactivateVersie, name="maakinactief"),
    path("addclient", views.AddBelegger, name="addclient"),
    path(
        "parameters/<str:excelFilename>/download",
        views.DownloadWorksheet,
        name="worksheetdownload",
    ),
    path(
        "parameters/<int:version_pk>/attachments", views.attachmentsView, name="attachmentview"
    ),
    path(
        "parameters/<int:version_pk>/attachments/<int:pk>", views.attachmentDetail, name="attachmentdetail"
    ),
    path(
        "parameters/<int:version_pk>/attachments/add", views.attachmentAdd, name="addattachment"
    ),
    path(
        "parameters/<int:version_pk>/attachments/<int:pk>/edit", views.attachmentEdit, name="editattachment"
    ),
    path(
        "parameters/<int:version_pk>/attachments/<int:pk>/delete", views.attachmentDelete, name="deleteattachment"
    ),
    path(
        "parameters/<int:version_pk>", views.PVEHoofdstukListView, name="chapterview"
    ),
    path(
        "parameters/<int:version_pk>/addchapter",
        views.PVEaddchapterView,
        name="addchapter",
    ),
    path(
        "parameters/<int:version_pk>/editchapter/<int:pk>",
        views.PVEeditchapterView,
        name="editchapter",
    ),
    path(
        "parameters/<int:version_pk>/deletechapter/<int:pk>",
        views.PVEdeletechapterView,
        name="deletechapter",
    ),
    path(
        "parameters/<int:version_pk>/<int:pk>",
        views.paragraphlistView,
        name="viewParagraaf",
    ),
    path(
        "parameters/<int:version_pk>/<int:pk>/addparagraph",
        views.PVEaddparagraphView,
        name="addparagraph",
    ),
    path(
        "parameters/<int:version_pk>/<int:pk>/editparagraph",
        views.PVEeditparagraphView,
        name="editparagraph",
    ),
    path(
        "parameters/<int:version_pk>/<int:pk>/deleteparagraph",
        views.PVEdeleteparagraphView,
        name="deleteparagraph",
    ),
    path(
        "parameters/<int:version_pk>/<int:chapter_id>/<int:paragraph_id>",
        views.itemListView,
        name="itemlistview",
    ),
    path(
        "parameters/<int:version_pk>/<int:chapter_id>/<int:paragraph_id>/add",
        views.addItemView,
        name="additem",
    ),
    path(
        "parameters/<int:version_pk>/item/<int:pk>", views.viewItemView, name="viewitem"
    ),
    path(
        "parameters/<int:version_pk>/item/<int:pk>/edit",
        views.editItemView,
        name="edititem",
    ),
    path(
        "parameters/<int:version_pk>/item/<int:pk>/delete",
        views.deleteItemView,
        name="deleteitem",
    ),
    path(
        "parameters/item/<int:pk>/attachment",
        views.downloadBijlageView,
        name="downloadattachment",
    ),
    path(
        "parameterchoices/<int:version_pk>",
        views.parameterchoicesView,
        name="parameterchoicesview",
    ),
    path(
        "parameterchoices/<int:version_pk>/<int:type>/<int:parameter_id>/form",
        views.parameterchoiceform,
        name="parameterchoiceform",
    ),
    path(
        "parameterchoices/<int:version_pk>/<int:type>/addform",
        views.addparameterchoiceform,
        name="addparameterchoiceform",
    ),
    path(
        "parameterchoices/<int:version_pk>/<int:type>/table",
        views.parameterchoicetable,
        name="parameterchoicetable",
    ),
    path(
        "parameterchoices/<int:version_pk>/<int:type>/modaladd",
        views.parameterchoicemodaladd,
        name="parameterchoicemodaladd",
    ),

    path(
        "parameterchoices/<int:version_pk>/<int:type>/<int:parameter_id>/get",
        views.parameterchoicedetail,
        name="parameterchoicedetail",
    ),
    path(
        "parameterchoices/<int:version_pk>/<int:type_id>/add",
        views.addparameterchoiceView,
        name="addparameterchoice",
    ),
    path(
        "parameterchoices/<int:version_pk>/<int:type_id>/<int:item_id>/delete",
        views.deleteparameterchoiceView,
        name="parameterchoicedelete",
    ),
    path(
        "commentpermissions/<int:version_pk>",
        views.EditCommentPermissionsOverview,
        name="editcommentpermissionsoverview",
    ),
        path(
        "commentpermissions/<int:version_pk>/<int:active>/<str:status_str>/<int:type>/activate",
        views.detailReqButton,
        name="detailReqButton",
    ),
        path(
        "commentpermissions/<int:version_pk>/<str:status_str>/<int:type>/activate",
        views.makeReqActive,
        name="makeReqActive",
    ),
    path(
        "commentpermissions/<int:version_pk>/<str:status_str>/<int:type>/deactivate",
        views.makeReqInactive,
        name="makeReqInactive",
    ),

    path("heatmap", views.projectHeatmap, name="projectheatmap"),
    path("accounts", views.AccountOverview, name="accountoverview"),
]

# Author: Tames Boon

from django.urls import path

from . import views

# Urls for the specific app
urlpatterns = [
    path("", views.LoginPageView, name="login"),
    path("dashboard", views.DashboardView, name="dashboard"),
    path("klanten", views.KlantOverzicht, name="klantoverzicht"),
    path("klanten/add", views.KlantToevoegen, name="klanttoevoegen"),
    path("klanten/<int:client_pk>/delete", views.KlantVerwijderen, name="klantverwijderen"),
    path("klanten/logo/<int:client_pk>", views.GetLogo, name="logoklantdetail"),
    path("klanten/logo/<int:client_pk>/add", views.LogoKlantForm, name="logoklantform"),
    path("klanten/beheerder/<int:client_pk>", views.GetBeheerderKlant, name="getbeheerderklant"),
    path("klanten/beheerder/<int:client_pk>/add", views.BeheerderKlantForm, name="beheerderklantform"),
    path("logout", views.LogoutView, name="logout"),

    path(
        "beleggersversie",
        views.PVEBeleggerVersieOverview,
        name="beleggerversieoverview",
    ),
    path(
        "bewerkpveoverview/<int:versie_pk>",
        views.PVEBewerkOverview,
        name="pvebewerkoverview",
    ),
    path("addpveversie/<int:belegger_pk>", views.AddPvEVersie, name="addpveversie"),
    path("deletepveversie/<int:belegger_pk>/<int:versie_pk>", views.DeletePVEVersie, name="deletepveversie"),
    path("makeactive/<int:versie_pk>", views.ActivateVersie, name="maakactief"),
    path("makeinactive/<int:versie_pk>", views.DeactivateVersie, name="maakinactief"),
    path("addbelegger", views.AddBelegger, name="addbelegger"),
    path(
        "parameters/<int:versie_pk>/download",
        views.DownloadWorksheet,
        name="worksheetdownload",
    ),
    path(
        "parameters/<int:versie_pk>/bijlagen", views.bijlagenView, name="bijlageview"
    ),
    path(
        "parameters/<int:versie_pk>/bijlagen/<int:pk>", views.bijlageDetail, name="bijlagedetail"
    ),
    path(
        "parameters/<int:versie_pk>/bijlagen/add", views.bijlageAdd, name="addbijlage"
    ),
    path(
        "parameters/<int:versie_pk>/bijlagen/<int:pk>/edit", views.bijlageEdit, name="editbijlage"
    ),
    path(
        "parameters/<int:versie_pk>/bijlagen/<int:pk>/delete", views.bijlageDelete, name="deletebijlage"
    ),
    path(
        "parameters/<int:versie_pk>", views.PVEHoofdstukListView, name="hoofdstukview"
    ),
    path(
        "parameters/<int:versie_pk>/edit",
        views.PVEHoofdstukListViewEdit,
        name="hoofdstukviewedit",
    ),
    path(
        "parameters/<int:versie_pk>/delete",
        views.PVEHoofdstukListViewDelete,
        name="hoofdstukviewdelete",
    ),
    path(
        "parameters/<int:versie_pk>/addchapter",
        views.PVEaddhoofdstukView,
        name="addchapter",
    ),
    path(
        "parameters/<int:versie_pk>/editchapter/<int:pk>",
        views.PVEedithoofdstukView,
        name="editchapter",
    ),
    path(
        "parameters/<int:versie_pk>/deletechapter/<int:pk>",
        views.PVEdeletehoofdstukView,
        name="deletechapter",
    ),
    path(
        "parameters/<int:versie_pk>/<int:pk>",
        views.paragraaflistView,
        name="viewParagraaf",
    ),
    path(
        "parameters/<int:versie_pk>/<int:pk>/edit",
        views.paragraaflistViewEdit,
        name="viewParagraafEdit",
    ),
    path(
        "parameters/<int:versie_pk>/<int:pk>/delete",
        views.paragraaflistViewDelete,
        name="viewParagraafDelete",
    ),
    path(
        "parameters/<int:versie_pk>/<int:pk>/addparagraph",
        views.PVEaddparagraafView,
        name="addparagraph",
    ),
    path(
        "parameters/<int:versie_pk>/<int:pk>/editparagraph",
        views.PVEeditparagraafView,
        name="editparagraph",
    ),
    path(
        "parameters/<int:versie_pk>/<int:pk>/deleteparagraph",
        views.PVEdeleteparagraafView,
        name="deleteparagraph",
    ),
    path(
        "parameters/<int:versie_pk>/<int:chapter_id>/<int:paragraph_id>",
        views.itemListView,
        name="itemlistview",
    ),
    path(
        "parameters/<int:versie_pk>/<int:chapter_id>/<int:paragraph_id>/edit",
        views.itemListViewEdit,
        name="itemlistviewedit",
    ),
    path(
        "parameters/<int:versie_pk>/<int:chapter_id>/<int:paragraph_id>/delete",
        views.itemListViewDelete,
        name="itemlistviewdelete",
    ),
    path(
        "parameters/<int:versie_pk>/<int:chapter_id>/<int:paragraph_id>/add",
        views.addItemView,
        name="additem",
    ),
    path(
        "parameters/<int:versie_pk>/item/<int:pk>", views.viewItemView, name="viewitem"
    ),
    path(
        "parameters/<int:versie_pk>/item/<int:pk>/edit",
        views.editItemView,
        name="edititem",
    ),
    path(
        "parameters/<int:versie_pk>/item/<int:pk>/delete",
        views.deleteItemView,
        name="deleteitem",
    ),
    path(
        "parameters/item/<int:pk>/bijlage",
        views.downloadBijlageView,
        name="downloadbijlage",
    ),
    path(
        "kiesparameters/<int:versie_pk>",
        views.kiesparametersView,
        name="kiesparametersview",
    ),
    path(
        "kiesparameters/<int:versie_pk>/<int:type>/<int:parameter_id>/form",
        views.kiesparameterform,
        name="kiesparameterform",
    ),
    path(
        "kiesparameters/<int:versie_pk>/<int:type>/<int:parameter_id>/get",
        views.kiesparameterdetail,
        name="kiesparameterdetail",
    ),
    path(
        "kiesparameters/<int:versie_pk>/<int:type_id>/add",
        views.addkiesparameterView,
        name="addkiesparameter",
    ),
    path(
        "kiesparameters/<int:versie_pk>/<int:type_id>/<int:item_id>/delete",
        views.deletekiesparameterView,
        name="kiesparameterdelete",
    ),
    path("heatmap", views.projectHeatmap, name="projectheatmap"),
]

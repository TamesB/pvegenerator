# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('', views.LoginPageView, name='login'),
    path('logout', views.LogoutView, name='logout'),
        
    path('parameters', views.PVEsectionView, name='sectionview'),
    path('parameters/download', views.DownloadWorksheet, name='worksheetdownload'),
    path('parameters/edit', views.PVEsectionViewEdit, name='sectionviewedit'),
    path('parameters/delete', views.PVEsectionViewDelete, name='sectionviewdelete'),
    path('parameters/add', views.PVEaddsectionView, name='addsection'),
    
    path('parameters/<int:pk>/addchapter', views.PVEaddhoofdstukView, name='addchapter'),
    path('parameters/<int:pk>/editchapter', views.PVEedithoofdstukView, name='editchapter'),
    path('parameters/<int:pk>/deletechapter', views.PVEdeletehoofdstukView, name='deletechapter'),
    
    path('parameters/<int:pk>', views.paragraaflistView, name='viewParagraaf'),
    path('parameters/<int:pk>/edit', views.paragraaflistViewEdit, name='viewParagraafEdit'),
    path('parameters/<int:pk>/delete', views.paragraaflistViewDelete, name='viewParagraafDelete'),
    
    path('parameters/<int:pk>/addparagraph', views.PVEaddparagraafView, name='addparagraph'),
    path('parameters/<int:pk>/editparagraph', views.PVEeditparagraafView, name='editparagraph'),
    path('parameters/<int:pk>/deleteparagraph', views.PVEdeleteparagraafView, name='deleteparagraph'),
    
    path('parameters/<int:chapter_id>/<int:paragraph_id>', views.itemListView, name='itemlistview'),
    path('parameters/<int:chapter_id>/<int:paragraph_id>/edit', views.itemListViewEdit, name='itemlistviewedit'),
    path('parameters/<int:chapter_id>/<int:paragraph_id>/delete', views.itemListViewDelete, name='itemlistviewdelete'),
    path('parameters/<int:chapter_id>/<int:paragraph_id>/add', views.addItemView, name='additem'),
    path('parameters/item/<int:pk>', views.viewItemView, name='viewitem'),
    path('parameters/item/<int:pk>/edit', views.editItemView, name='edititem'),
    path('parameters/item/<int:pk>/delete', views.deleteItemView, name='deleteitem'),
    
    path('kiesparameters', views.kiesparametersView, name='kiesparametersview'),
    path('kiesparameters/edit', views.kiesparametersViewEdit, name='kiesparametersviewedit'),
    path('kiesparameters/delete', views.kiesparametersViewDelete, name='kiesparametersviewdelete'),
    path('kiesparameters/<int:type_id>/add', views.addkiesparameterView, name='addkiesparameter'),
    path('kiesparameters/<int:type_id>/<int:item_id>/edit', views.bewerkkiesparameterView, name='kiesparameteredit'),
    path('kiesparameters/<int:type_id>/<int:item_id>/delete', views.deletekiesparameterView, name='kiesparameterdelete'),

]

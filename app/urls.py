# Author: Tames Boon

from django.urls import path
from . import views

# Urls for the specific app
urlpatterns = [
    path('', views.LoginPageView, name='login'),
    path('logout', views.LogoutView, name='logout'),
    path('generate', views.GeneratePVEView, name='generate'),
    path('download/<str:filename>', views.download_file, name='download'),
        
    path('parameters', views.PVEsectionView, name='sectionview'),
    path('parameters/edit', views.PVEsectionViewEdit, name='sectionviewedit'),
    path('parameters/delete', views.PVEsectionViewDelete, name='sectionviewdelete'),
    path('parameters/add', views.PVEaddsectionView, name='addsection'),
    
    path('parameters/<int:id>/addchapter', views.PVEaddhoofdstukView, name='addchapter'),
    path('parameters/<int:id>/editchapter', views.PVEedithoofdstukView, name='editchapter'),
    path('parameters/<int:id>/deletechapter', views.PVEdeletehoofdstukView, name='deletechapter'),
    
    path('parameters/<int:id>', views.paragraaflistView, name='viewParagraaf'),
    path('parameters/<int:id>/edit', views.paragraaflistViewEdit, name='viewParagraafEdit'),
    path('parameters/<int:id>/delete', views.paragraaflistViewDelete, name='viewParagraafDelete'),
    
    path('parameters/<int:id>/addparagraph', views.PVEaddparagraafView, name='addparagraph'),
    path('parameters/<int:id>/editparagraph', views.PVEeditparagraafView, name='editparagraph'),
    path('parameters/<int:id>/deleteparagraph', views.PVEdeleteparagraafView, name='deleteparagraph'),
    
    path('parameters/<int:chapter_id>/<int:paragraph_id>', views.itemListView, name='itemlistview'),
    path('parameters/<int:chapter_id>/<int:paragraph_id>/edit', views.itemListViewEdit, name='itemlistviewedit'),
    path('parameters/<int:chapter_id>/<int:paragraph_id>/delete', views.itemListViewDelete, name='itemlistviewdelete'),
    path('parameters/<int:chapter_id>/<int:paragraph_id>/add', views.addItemView, name='additem'),
    path('parameters/item/<int:id>', views.viewItemView, name='viewitem'),
    path('parameters/item/<int:id>/edit', views.editItemView, name='edititem'),
    path('parameters/item/<int:id>/delete', views.deleteItemView, name='deleteitem'),
    
    path('kiesparameters', views.kiesparametersView, name='kiesparametersview'),
    path('kiesparameters/edit', views.kiesparametersViewEdit, name='kiesparametersviewedit'),
    path('kiesparameters/delete', views.kiesparametersViewDelete, name='kiesparametersviewdelete'),
    path('kiesparameters/<int:type_id>/add', views.addkiesparameterView, name='addkiesparameter'),
    path('kiesparameters/<int:type_id>/<int:item_id>/edit', views.bewerkkiesparameterView, name='kiesparameteredit'),
    path('kiesparameters/<int:type_id>/<int:item_id>/delete', views.deletekiesparameterView, name='kiesparameterdelete'),

]

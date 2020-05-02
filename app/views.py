# Author: Tames Boon

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from utils import writePdf
import datetime
import os
from django.conf import settings
import mimetypes
from . import models
from . import forms


def LoginPageView(request):
    # cant see lander page if already logged in
    if request.user.is_authenticated:
        return redirect('generate')

    if request.method == "POST":
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            (username, password) = (
                form.cleaned_data["username"], form.cleaned_data["password"])
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('generate')

    # render the page
    context = {}
    context["form"] = forms.LoginForm()

    return render(request, 'login.html', context)


@login_required
def LogoutView(request):
    logout(request)
    return redirect('login')


@login_required
def GeneratePVEView(request):
    if request.method == "POST":

        # get user entered form
        form = forms.PVEParameterForm(request.POST)

        # check validity
        if form.is_valid():
            # get parameters, find all pveitems with that
            (Bouwsoort, TypeObject, Doelgroep, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort"], form.cleaned_data["TypeObject"],
                form.cleaned_data["Doelgroep"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"]
            )

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(
                Bouwsoort__parameter__contains=Bouwsoort)
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.filter(
                    TypeObject__parameter__contains=TypeObject))
            query_set = basic_PVE.union(
                models.PVEItem.objects.filter(
                    Doelgroep__parameter__contains=Doelgroep))

            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                query_set = query_set.union(
                    models.PVEItem.objects.filter(Q(AED=True)))
            if Smarthome:
                query_set = query_set.union(
                    models.PVEItem.objects.filter(Q(Smarthome=True)))
            if EntreeUpgrade:
                query_set = query_set.union(
                    models.PVEItem.objects.filter(Q(EntreeUpgrade=True)))
            if Pakketdient:
                query_set = query_set.union(
                    models.PVEItem.objects.filter(Q(Pakketdient=True)))
            if JamesConcept:
                query_set = query_set.union(
                    models.PVEItem.objects.filter(Q(JamesConcept=True)))

            query_set.order_by('id')

            # make pdf
            parameters = [
                f"Bouwsoort: {Bouwsoort.parameter}",
                f"Object: {TypeObject.parameter}",
                f"Doelgroep: {Doelgroep.parameter}"
            ]

            date = datetime.datetime.now()
            filename = "PVE-%s%s%s%s%s%s" % (
                date.strftime("%H"),
                date.strftime("%M"),
                date.strftime("%S"),
                date.strftime("%d"),
                date.strftime("%m"),
                date.strftime("%Y")
            )

            pdfmaker = writePdf.PDFMaker()
            pdfmaker.makepdf(filename, query_set, parameters)

            # and render the result page
            context = {}
            context["itemsPVE"] = query_set
            context["filename"] = filename
            return render(request, 'PVEResult.html', context)

    # if get method, just render the empty form
    context = {}
    context["form"] = forms.PVEParameterForm()
    return render(request, 'GeneratePVE.html', context)


@login_required
def download_file(request, filename):
    fl_path = settings.EXPORTS_ROOT

    filename = f"/{filename}.pdf"

    try:
        fl = open(fl_path + filename, 'rb')
    except OSError:
        raise Http404("404")

    response = HttpResponse(fl, content_type="application/pdf")
    response['Content-Disposition'] = "inline; filename=%s" % filename

    return response


@staff_member_required
def PVEsectionView(request):
    Onderdelen = models.PVEOnderdeel.objects.all()
    SectionQuerySets = {}

    for onderdeel in Onderdelen:
        SectionQuerySets[onderdeel] = models.PVEHoofdstuk.objects.filter(
            onderdeel__naam=onderdeel.naam)

    context = {}
    context["SectionQuerySets"] = SectionQuerySets.items()
    context["onderdelen"] = Onderdelen

    return render(request, 'PVEListHfst.html', context)


@staff_member_required
def PVEsectionViewEdit(request):
    Onderdelen = models.PVEOnderdeel.objects.all()
    SectionQuerySets = {}

    for onderdeel in Onderdelen:
        SectionQuerySets[onderdeel] = models.PVEHoofdstuk.objects.filter(
            onderdeel__naam=onderdeel.naam)

    context = {}
    context["SectionQuerySets"] = SectionQuerySets.items()
    context["onderdelen"] = Onderdelen

    return render(request, 'PVEListHfstEdit.html', context)


@staff_member_required
def PVEsectionViewDelete(request):
    Onderdelen = models.PVEOnderdeel.objects.all()
    SectionQuerySets = {}

    for onderdeel in Onderdelen:
        SectionQuerySets[onderdeel] = models.PVEHoofdstuk.objects.filter(
            onderdeel__naam=onderdeel.naam)

    context = {}
    context["SectionQuerySets"] = SectionQuerySets.items()
    context["onderdelen"] = Onderdelen

    return render(request, 'PVEListHfstDelete.html', context)


@staff_member_required
def PVEaddsectionView(request):
    if request.method == 'POST':
        form = forms.SectionForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            onderdeel = models.PVEOnderdeel()
            onderdeel.naam = form.cleaned_data["naam"]
            onderdeel.save()
            return redirect('sectionview')

    # View below modal
    Onderdelen = models.PVEOnderdeel.objects.all()
    SectionQuerySets = {}

    for onderdeel in Onderdelen:
        SectionQuerySets[onderdeel] = models.PVEHoofdstuk.objects.filter(
            onderdeel__naam=onderdeel.naam)

    # form
    form = forms.SectionForm()

    context = {}
    context["SectionQuerySets"] = SectionQuerySets.items()
    context["onderdelen"] = Onderdelen
    context["form"] = form
    return render(request, 'addsectionform.html', context)


@staff_member_required
def PVEaddhoofdstukView(request, pk):
    if not models.PVEOnderdeel.objects.filter(id=pk):
        return Http404("404")

    specifiek_onderdeel = models.PVEOnderdeel.objects.filter(id=pk).first()

    if request.method == 'POST':
        form = forms.ChapterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            PVEHoofdstuk = models.PVEHoofdstuk()
            PVEHoofdstuk.onderdeel = specifiek_onderdeel
            PVEHoofdstuk.hoofdstuk = form.cleaned_data["hoofdstuk"]
            PVEHoofdstuk.save()
            return redirect('sectionview')

    # View below modal
    Onderdelen = models.PVEOnderdeel.objects.all()
    SectionQuerySets = {}

    for onderdeel in Onderdelen:
        SectionQuerySets[onderdeel] = models.PVEHoofdstuk.objects.filter(
            onderdeel__naam=onderdeel.naam)

    # form, initial chapter in specific onderdeel
    form = forms.ChapterForm(initial={'onderdeel': specifiek_onderdeel})

    context = {}
    context["SectionQuerySets"] = SectionQuerySets.items()
    context["onderdelen"] = Onderdelen
    context["onderdeel"] = specifiek_onderdeel
    context["form"] = form
    return render(request, 'addchapterform.html', context)


@staff_member_required
def PVEedithoofdstukView(request, pk):
    if not models.PVEHoofdstuk.objects.filter(id=pk):
        return Http404("404")

    if request.method == 'POST':
        form = forms.ChapterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            PVEhoofdstuk = models.PVEHoofdstuk.objects.filter(id=pk).first()
            PVEhoofdstuk.hoofdstuk = form.cleaned_data["hoofdstuk"]
            PVEhoofdstuk.save()
            return redirect('sectionview')

    # View below modal
    Onderdelen = models.PVEOnderdeel.objects.all()
    SectionQuerySets = {}

    for onderdeel in Onderdelen:
        SectionQuerySets[onderdeel] = models.PVEHoofdstuk.objects.filter(
            onderdeel__naam=onderdeel.naam)

    # form, initial chapter in specific onderdeel
    hoofdstuk = models.PVEHoofdstuk.objects.filter(id=id).first()
    form = forms.ChapterForm(instance=hoofdstuk)

    context = {}
    context["SectionQuerySets"] = SectionQuerySets.items()
    context["onderdelen"] = Onderdelen
    context["form"] = form
    context["chapter_id"] = id
    return render(request, 'changechapterform.html', context)


@staff_member_required
def paragraaflistView(request, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(id=pk):
        hoofdstuk = models.PVEHoofdstuk.objects.filter(id=pk).first()
    else:
        raise Http404("404")

    items = models.PVEItem.objects.filter(hoofdstuk=hoofdstuk)

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect('itemlistview', chapter_id=id, paragraph_id=0)

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = models.PVEParagraaf.objects.filter(
        hoofdstuk=hoofdstuk)
    context["sectie"] = hoofdstuk
    return render(request, 'PVEParagraphList.html', context)


@staff_member_required
def paragraaflistViewEdit(request, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(id=pk):
        hoofdstuk = models.PVEHoofdstuk.objects.filter(id=pk).first()
    else:
        raise Http404("404")

    items = models.PVEItem.objects.filter(hoofdstuk=hoofdstuk)

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect('itemlistviewedit', chapter_id=id, paragraph_id=0)

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = models.PVEParagraaf.objects.filter(
        hoofdstuk=hoofdstuk)
    context["sectie"] = hoofdstuk
    context["id"] = id
    return render(request, 'PVEParagraphListEdit.html', context)


@staff_member_required
def paragraaflistViewDelete(request, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(id=pk):
        hoofdstuk = models.PVEHoofdstuk.objects.filter(id=pk).first()
    else:
        raise Http404("404")

    items = models.PVEItem.objects.filter(hoofdstuk=hoofdstuk)

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect(
                'itemlistviewdelete',
                chapter_id=pk,
                paragraph_id=0)

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = models.PVEParagraaf.objects.filter(
        hoofdstuk=hoofdstuk)
    context["sectie"] = hoofdstuk
    context["id"] = pk
    return render(request, 'PVEParagraphListDelete.html', context)


@staff_member_required
def PVEaddparagraafView(request, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(id=pk):
        hoofdstuk = models.PVEHoofdstuk.objects.filter(id=pk).first()
    else:
        raise Http404("404")

    if request.method == 'POST':
        form = forms.ParagraafForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            PVEParagraaf = models.PVEParagraaf()
            PVEParagraaf.hoofdstuk = hoofdstuk
            PVEParagraaf.paragraaf = form.cleaned_data["paragraaf"]
            PVEParagraaf.save()
            return HttpResponseRedirect(reverse('viewParagraaf', args=(pk,)))

    # View below modal
    items = models.PVEItem.objects.filter(hoofdstuk=hoofdstuk)

    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect('itemlistview', chapter_id=pk, paragraph_id=0)

    form = forms.ParagraafForm(initial={'hoofdstuk': hoofdstuk})

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = models.PVEParagraaf.objects.filter(
        hoofdstuk=hoofdstuk)
    context["sectie"] = hoofdstuk
    context["form"] = form
    return render(request, 'addparagraphform.html', context)


@staff_member_required
def PVEeditparagraafView(request, pk):
    pk = int(pk)

    if models.PVEParagraaf.objects.filter(id=pk):
        paragraaf = models.PVEParagraaf.objects.filter(id=pk).first()
        hoofdstuk = paragraaf.hoofdstuk
    else:
        raise Http404("404")

    if request.method == 'POST':
        form = forms.ParagraafForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            PVEparagraaf = models.PVEParagraaf.objects.filter(id=pk).first()
            PVEparagraaf.paragraaf = form.cleaned_data["paragraaf"]
            PVEparagraaf.save()
            return HttpResponseRedirect(
                reverse(
                    'viewParagraaf', args=(
                        hoofdstuk.id,)))

    # View below modal
    items = models.PVEItem.objects.filter(hoofdstuk=hoofdstuk)
    # if an item is already in the chapter and doesnt have a paragraph ->
    # redirect to items
    if items:
        if items.first().paragraaf is None:
            return redirect(
                'itemlistview',
                chapter_id=hoofdstuk.id,
                paragraph_id=0)

    form = forms.ParagraafForm(instance=paragraaf)

    # otherwise, show paragraphs
    context = {}
    context["paragraven"] = models.PVEParagraaf.objects.filter(
        hoofdstuk=hoofdstuk)
    context["sectie"] = hoofdstuk
    context["paragraph_id"] = pk
    context["id"] = hoofdstuk.id
    context["form"] = form
    return render(request, 'changeparagraphform.html', context)


@staff_member_required
def itemListView(request, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)
    chapter_id = int(chapter_id)

    # Chapter_id doesnt exist
    if not models.PVEHoofdstuk.objects.filter(id=chapter_id):
        raise Http404("404")

    hoofdstuk = models.PVEHoofdstuk.objects.filter(id=chapter_id).first()

    # if no paragraph given but there are paragraphs in this chapter
    if paragraph_id == 0:
        if models.PVEParagraaf.objects.filter(hoofdstuk__id=chapter_id):
            raise Http404("404")

    # if paragraphs arent connected to this chapter
    if paragraph_id != 0:
        if not models.PVEParagraaf.objects.filter(hoofdstuk__id=chapter_id).filter(id=paragraph_id):
            raise Http404("404")
        
        paragraaf = models.PVEParagraaf.objects.filter(id=paragraph_id).first()
    
    context = {}

    # item niet in een paragraaf: haal ze van een hoofdstuk
    if paragraph_id == 0:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk__id=chapter_id)
        context["hoofdstuk"] = hoofdstuk
    else:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk__id=chapter_id).filter(
            paragraaf__id=paragraph_id)
        context["paragraaf"] = paragraaf
        context["hoofdstuk"] = hoofdstuk

    context["paragraaf_id"] = paragraph_id
    context["hoofdstuk_id"] = chapter_id

    return render(request, 'PVEItemList.html', context)


@staff_member_required
def itemListViewEdit(request, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)
    chapter_id = int(chapter_id)
    
    # Chapter_id doesnt exist
    if not models.PVEHoofdstuk.objects.filter(id=chapter_id):
        raise Http404("404")

    hoofdstuk = models.PVEHoofdstuk.objects.filter(id=chapter_id).first()

    # if no paragraph given but there are paragraphs in this chapter
    if paragraph_id == 0:
        if models.PVEParagraaf.objects.filter(hoofdstuk__id=chapter_id):
            raise Http404("404")

    # if paragraphs arent connected to this chapter
    if paragraph_id != 0:
        if not models.PVEParagraaf.objects.filter(hoofdstuk__id=chapter_id).filter(id=paragraph_id):
            raise Http404("404")
        
        paragraaf = models.PVEParagraaf.objects.filter(id=paragraph_id).first()

    context = {}

    # item niet in een paragraaf: haal ze van een hoofdstuk
    if paragraph_id == 0:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk__id=chapter_id)
        context["hoofdstuk"] = hoofdstuk
    else:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk__id=chapter_id).filter(
            paragraaf__id=paragraph_id)
        context["paragraaf"] = paragraaf
        context["hoofdstuk"] = hoofdstuk

    context["paragraaf_id"] = paragraph_id
    context["hoofdstuk_id"] = chapter_id

    return render(request, 'PVEItemListEdit.html', context)


@staff_member_required
def itemListViewDelete(request, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)
    chapter_id = int(chapter_id)

    # Chapter_id doesnt exist
    if not models.PVEHoofdstuk.objects.filter(id=chapter_id):
        raise Http404("404")

    hoofdstuk = models.PVEHoofdstuk.objects.filter(id=chapter_id).first()

    # if no paragraph given but there are paragraphs in this chapter
    if paragraph_id == 0:
        if models.PVEParagraaf.objects.filter(hoofdstuk__id=chapter_id):
            raise Http404("404")

    # if paragraphs arent connected to this chapter
    if paragraph_id != 0:
        if not models.PVEParagraaf.objects.filter(hoofdstuk__id=chapter_id).filter(id=paragraph_id):
            raise Http404("404")
        
        paragraaf = models.PVEParagraaf.objects.filter(id=paragraph_id).first()
                    
    context = {}

    # item niet in een paragraaf: haal ze van een hoofdstuk
    if paragraph_id == 0:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk__id=chapter_id)
        context["hoofdstuk"] = hoofdstuk
    else:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk__id=chapter_id).filter(
            paragraaf__id=paragraph_id)
        context["paragraaf"] = paragraaf
        context["hoofdstuk"] = hoofdstuk

    context["paragraaf_id"] = paragraph_id
    context["hoofdstuk_id"] = chapter_id

    return render(request, 'PVEItemListDelete.html', context)


@staff_member_required
def viewItemView(request, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(id=pk):
        PVEItem = models.PVEItem.objects.filter(id=pk).first()
    else:
        raise Http404("Item does not exist.")

    context = {}
    context["PVEItem"] = PVEItem
    context["Bouwsoort"] = PVEItem.Bouwsoort.all()
    context["TypeObject"] = PVEItem.TypeObject.all()
    context["Doelgroep"] = PVEItem.Doelgroep.all()

    if not PVEItem.paragraaf:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk=PVEItem.hoofdstuk)
        context["hoofdstuk"] = PVEItem.hoofdstuk
        context["paragraaf_id"] = 0
    else:
        context["queryset"] = models.PVEItem.objects.filter(
            hoofdstuk=PVEItem.hoofdstuk).filter(
            paragraaf=PVEItem.paragraaf)
        context["paragraaf"] = PVEItem.paragraaf
        context["hoofdstuk"] = PVEItem.hoofdstuk
        context["paragraaf_id"] = PVEItem.paragraaf.id

    context["hoofdstuk_id"] = PVEItem.hoofdstuk.id

    return render(request, 'PVEItemView.html', context)


@staff_member_required
def editItemView(request, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(id=pk):
        PVEItem = models.PVEItem.objects.filter(id=pk).first()
    else:
        raise Http404("Item does not exist.")

    if request.method == "POST":
        # get user entered form
        form = forms.PVEItemEditForm(request.POST, request.FILES)

        # check validity
        if form.is_valid():
            # get parameters and save new item
            PVEItem.inhoud = form.cleaned_data["inhoud"]
            PVEItem.bijlage = form.cleaned_data["bijlage"]
            PVEItem.save()

            PVEItem.Bouwsoort.set(form.cleaned_data["Bouwsoort"])
            PVEItem.TypeObject.set(form.cleaned_data["TypeObject"])
            PVEItem.Doelgroep.set(form.cleaned_data["Doelgroep"])
            PVEItem.Smarthome = form.cleaned_data["Smarthome"]
            PVEItem.AED = form.cleaned_data["AED"]
            PVEItem.EntreeUpgrade = form.cleaned_data["EntreeUpgrade"]
            PVEItem.Pakketdient = form.cleaned_data["Pakketdient"]
            PVEItem.JamesConcept = form.cleaned_data["JamesConcept"]

            PVEItem.save()

            # and reverse
            return HttpResponseRedirect(reverse('viewitem', args=(pk,)))

    # if get method, just render the empty form
    context = {}
    context["form"] = forms.PVEItemEditForm(instance=PVEItem)
    context["id"] = pk
    return render(request, 'PVEItemEdit.html', context)


@staff_member_required
def addItemView(request, chapter_id, paragraph_id):
    paragraph_id = int(paragraph_id)

    if request.method == "POST":
        # get user entered form
        form = forms.PVEItemEditForm(request.POST, request.FILES)

        # check validity
        if form.is_valid():
            PVEItem = models.PVEItem()
            # get parameters and save new item
            if int(paragraph_id) != 0:
                PVEItem.paragraaf = models.PVEParagraaf.objects.filter(
                    id=paragraph_id).first()

            PVEItem.hoofdstuk = models.PVEHoofdstuk.objects.filter(
                id=chapter_id).first()
            PVEItem.inhoud = form.cleaned_data["inhoud"]
            PVEItem.bijlage = form.cleaned_data["bijlage"]
            PVEItem.save()

            PVEItem.Bouwsoort.set(form.cleaned_data["Bouwsoort"])
            PVEItem.TypeObject.set(form.cleaned_data["TypeObject"])
            PVEItem.Doelgroep.set(form.cleaned_data["Doelgroep"])
            PVEItem.Smarthome = form.cleaned_data["Smarthome"]
            PVEItem.AED = form.cleaned_data["AED"]
            PVEItem.EntreeUpgrade = form.cleaned_data["EntreeUpgrade"]
            PVEItem.Pakketdient = form.cleaned_data["Pakketdient"]
            PVEItem.JamesConcept = form.cleaned_data["JamesConcept"]

            PVEItem.save()

            pk = PVEItem.id

            # and reverse
            return HttpResponseRedirect(reverse('viewitem', args=(pk,)))

    context = {}
    context["form"] = forms.PVEItemEditForm()
    context["chapter_id"] = chapter_id
    context["paragraph_id"] = int(paragraph_id)

    return render(request, 'PVEAddItem.html', context)


@staff_member_required
def deleteItemView(request, pk):
    pk = int(pk)

    if models.PVEItem.objects.filter(id=pk):
        PVEItem = models.PVEItem.objects.filter(id=pk).first()
        hoofdstuk = PVEItem.hoofdstuk
        paragraaf = PVEItem.paragraaf
    else:
        raise Http404("404.")

    PVEItem.delete()

    messages.success(request, f"Regel {pk} verwijderd.")

    if not paragraaf:
        return HttpResponseRedirect(
            reverse(
                'viewParagraafDelete',
                args=(
                    hoofdstuk.id,
                )))

    return HttpResponseRedirect(
        reverse(
            'itemlistviewdelete',
            args=(
                hoofdstuk.id,
                paragraaf.id)))


@staff_member_required
def PVEdeletehoofdstukView(request, pk):
    pk = int(pk)

    if models.PVEHoofdstuk.objects.filter(id=pk):
        PVEHoofdstuk = models.PVEHoofdstuk.objects.filter(id=pk).first()
        hoofdstuk = PVEHoofdstuk.hoofdstuk
    else:
        raise Http404("404.")

    PVEHoofdstuk.delete()

    messages.success(request, f"Hoofdstuk {hoofdstuk} verwijderd.")

    return redirect('sectionview')


@staff_member_required
def PVEdeleteparagraafView(request, pk):
    pk = int(pk)

    if models.PVEParagraaf.objects.filter(id=pk):
        PVEParagraaf = models.PVEParagraaf.objects.filter(id=pk).first()
        hoofdstuk = PVEParagraaf.hoofdstuk
        paragraaf = PVEParagraaf.paragraaf
    else:
        raise Http404("404.")

    PVEParagraaf.delete()

    messages.success(request, f"Paragraaf {paragraaf} verwijderd.")

    return HttpResponseRedirect(reverse('viewParagraaf', args=(hoofdstuk.id,)))


@staff_member_required
def kiesparametersView(request):
    context = {}
    context["bouwsoorten"] = models.Bouwsoort.objects.all()
    context["typeObjecten"] = models.TypeObject.objects.all()
    context["doelgroepen"] = models.Doelgroep.objects.all()
    return render(request, 'kiesparameters.html', context)


@staff_member_required
def kiesparametersViewEdit(request):
    context = {}
    context["bouwsoorten"] = models.Bouwsoort.objects.all()
    context["typeObjecten"] = models.TypeObject.objects.all()
    context["doelgroepen"] = models.Doelgroep.objects.all()
    return render(request, 'kiesparametersEdit.html', context)


@staff_member_required
def kiesparametersViewDelete(request):
    context = {}
    context["bouwsoorten"] = models.Bouwsoort.objects.all()
    context["typeObjecten"] = models.TypeObject.objects.all()
    context["doelgroepen"] = models.Doelgroep.objects.all()
    return render(request, 'kiesparametersDelete.html', context)


@staff_member_required
def addkiesparameterView(request, type_id):
    type_id = int(type_id)

    if request.method == "POST":
        # get user entered form
        form = forms.KiesParameterForm(request.POST)

        # check validity
        if form.is_valid():

            # If type_id not in available ones
            if type_id != 1 and type_id != 2 and type_id != 3:
                raise Http404("404")

            if type_id == 1:  # Bouwsoort
                item = models.Bouwsoort()

            if type_id == 2:  # Type Object
                item = models.TypeObject()

            if type_id == 3:  # Doelgroep
                item = models.Doelgroep()

            item.parameter = form.cleaned_data["parameter"]
            item.save()

            return HttpResponseRedirect(reverse('kiesparametersview'))

    form = forms.KiesParameterForm()

    context = {}
    context["form"] = form
    context["type_id"] = type_id
    context["bouwsoorten"] = models.Bouwsoort.objects.all()
    context["typeObjecten"] = models.TypeObject.objects.all()
    context["doelgroepen"] = models.Doelgroep.objects.all()

    return render(request, "addkiesparameter.html", context)


@staff_member_required
def bewerkkiesparameterView(request, type_id, item_id):
    type_id = int(type_id)
    item_id = int(item_id)

    if type_id != 1 and type_id != 2 and type_id != 3:
        raise Http404("404")

    if type_id == 1:  # Bouwsoort
        if not models.Bouwsoort.objects.filter(id=item_id):
            raise Http404("404")

        item = models.Bouwsoort.objects.filter(id=item_id).first()

    if type_id == 2:  # Type Object
        if not models.TypeObject.objects.filter(id=item_id):
            raise Http404("404")

        item = models.TypeObject.objects.filter(id=item_id).first()

    if type_id == 3:  # Doelgroep
        if not models.Doelgroep.objects.filter(id=item_id):
            raise Http404("404")

        item = models.Doelgroep.objects.filter(id=item_id).first()

    if request.method == "POST":
        form = forms.KiesParameterForm(request.POST)

        if form.is_valid():
            item.parameter = form.cleaned_data["parameter"]
            item.save()

            return HttpResponseRedirect(reverse('kiesparametersview'))

    form = forms.KiesParameterForm(initial={'parameter': item.parameter})

    context = {}
    context["form"] = form
    context["type_id"] = type_id
    context["item_id"] = item_id
    context["bouwsoorten"] = models.Bouwsoort.objects.all()
    context["typeObjecten"] = models.TypeObject.objects.all()
    context["doelgroepen"] = models.Doelgroep.objects.all()

    return render(request, "bewerkkiesparameter.html", context)


@staff_member_required
def deletekiesparameterView(request, type_id, item_id):
    type_id = int(type_id)
    item_id = int(item_id)

    if type_id != 1 and type_id != 2 and type_id != 3:
        raise Http404("404")

    if type_id == 1:  # Bouwsoort
        if not models.Bouwsoort.objects.filter(id=item_id):
            raise Http404("404")

        item = models.Bouwsoort.objects.filter(id=item_id).first()

    if type_id == 2:  # Type Object
        if not models.TypeObject.objects.filter(id=item_id):
            raise Http404("404")

        item = models.TypeObject.objects.filter(id=item_id).first()

    if type_id == 3:  # Doelgroep
        if not models.Doelgroep.objects.filter(id=item_id):
            raise Http404("404")

        item = models.Doelgroep.objects.filter(id=item_id).first()

    parameter = item.parameter
    item.delete()

    messages.success(request, f"{parameter} verwijderd.")

    return HttpResponseRedirect(reverse('kiesparametersviewdelete'))

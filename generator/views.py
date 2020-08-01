from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from utils import writePdf, writeDiffPdf
from django.contrib import messages
import datetime
import os
from django.conf import settings
import mimetypes
from . import models
from app import models
from . import forms
import zipfile

# Create your views here.
@login_required
def GeneratePVEView(request):
    if request.method == "POST":

        # get user entered form
        form = forms.PVEParameterForm(request.POST)

        # check validity
        if form.is_valid():

            # get parameters, find all pveitems with that
            (Bouwsoort1, TypeObject1, Doelgroep1, Bouwsoort2, TypeObject2, Doelgroep2, Smarthome,
             AED, EntreeUpgrade, Pakketdient, JamesConcept) = (
                form.cleaned_data["Bouwsoort1"], form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"], form.cleaned_data["Bouwsoort2"], form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"], form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"], form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(
                basisregel=True)
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.filter(
                    Bouwsoort__parameter__contains=Bouwsoort1))

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Bouwsoort__parameter__contains=Bouwsoort2))
            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject1))
            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        TypeObject__parameter__contains=TypeObject2))
            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep1))
            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Doelgroep__parameter__contains=Doelgroep2))

            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(AED=True)))
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Smarthome=True)))
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(EntreeUpgrade=True)))
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(Pakketdient=True)))
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(JamesConcept=True)))

            basic_PVE = basic_PVE.order_by('id')

            # make pdf
            parameters = []

            if Bouwsoort1:
                parameters += f"{Bouwsoort1.parameter} (Hoofd)",
            if Bouwsoort2:
                parameters += f"{Bouwsoort2.parameter} (Sub)",
            if TypeObject1:
                parameters += f"{TypeObject1.parameter} (Hoofd)",
            if TypeObject2:
                parameters += f"{TypeObject2.parameter} (Sub)",
            if Doelgroep1:
                parameters += f"{Doelgroep1.parameter} (Hoofd)",
            if Doelgroep2:
                parameters += f"{Doelgroep2.parameter} (Sub)",

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
            pdfmaker.makepdf(filename, basic_PVE, parameters)


            # get bijlagen
            bijlagen = [item.bijlage for item in basic_PVE if item.bijlage]
            #remove duplicates
            bijlagen = list(dict.fromkeys(bijlagen))


            # and render the result page
            context = {}
            context["itemsPVE"] = basic_PVE
            context["filename"] = filename
            return render(request, 'PVEResult.html', context)
        else:
            messages.warning(request, "Vul de verplichte keuzes in.")

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

@login_required
def download_bijlagen(request, bijlagen):
    filenames = bijlagen

    BASE = os.path.dirname(os.path.abspath(__file__))

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    # FIXME: Set this to something better
    zip_subdir = "bijlagen"
    zip_filename = "%s.zip" % zip_subdir

    path = BASE + settings.EXPORTS_URL + zip_filename

    # Open StringIO to grab in-memory ZIP contents
    s = io.StringIO.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = os.path.join(zip_subdir, fname)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), mimetype = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


@staff_member_required
def compareView(request):
    context = {}
    return render(request, 'compare.html', context)


@staff_member_required
def compareFormView(request, pk):
    pk = int(pk)
    context = {}
    context["pk"] = pk

    if request.method == "POST":
        if pk == 1:
            # get user entered form
            form = forms.CompareFormBouwsoort(request.POST)
        if pk == 2:
            form = forms.CompareFormTypeObject(request.POST)
        if pk == 3:
            form = forms.CompareFormDoelgroep(request.POST)

        # check validity
        if form.is_valid():
            parameters = []

            if pk == 1:
                (keuze1, keuze2) = (form.cleaned_data["Bouwsoort1"], form.cleaned_data["Bouwsoort2"])
                PvE1 = models.PVEItem.objects.filter(Bouwsoort__parameter__contains=keuze1)
                PvE2 = models.PVEItem.objects.filter(Bouwsoort__parameter__contains=keuze2)

            if pk == 2:
                (keuze1, keuze2) = (form.cleaned_data["TypeObject1"], form.cleaned_data["TypeObject2"])
                PvE1 = models.PVEItem.objects.filter(TypeObject__parameter__contains=keuze1)
                PvE2 = models.PVEItem.objects.filter(TypeObject__parameter__contains=keuze2)

            if pk == 3:
                (keuze1, keuze2) = (form.cleaned_data["Doelgroep1"], form.cleaned_data["Doelgroep2"])
                PvE1 = models.PVEItem.objects.filter(Doelgroep__parameter__contains=keuze1)
                PvE2 = models.PVEItem.objects.filter(Doelgroep__parameter__contains=keuze2)

            afwijkingen = PvE1.difference(PvE2)
            afwijkingen = afwijkingen.order_by('id')

            # make pdf
            if afwijkingen:
                parameters += f"{keuze1} t.o.v. {keuze2}"

                date = datetime.datetime.now()
                filename = "AFWIJKINGEN-%s%s%s%s%s%s" % (
                    date.strftime("%H"),
                    date.strftime("%M"),
                    date.strftime("%S"),
                    date.strftime("%d"),
                    date.strftime("%m"),
                    date.strftime("%Y")
                )

                pdfmaker = writeDiffPdf.PDFMaker()
                pdfmaker.makepdf(filename, afwijkingen, parameters)
                context["filename"] = filename

            context["afwijkingen"] = afwijkingen
            return render(request, 'compareResults.html', context)


    # if get method, just render the empty form
    if pk == 1:
        context["form"] = forms.CompareFormBouwsoort()
    if pk == 2:
        context["form"] = forms.CompareFormTypeObject()
    if pk == 3:
        context["form"] = forms.CompareFormDoelgroep()

    return render(request, 'compareForm.html', context)

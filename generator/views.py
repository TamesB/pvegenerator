from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from utils import writePdf
from django.contrib import messages
import datetime
import os
from django.conf import settings
import mimetypes
from . import models
from app import models
from . import forms

# Create your views here.
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
                form.cleaned_data["Pakketdient"], form.cleaned_data["JamesConcept"] )

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(
                basisregel=True)
            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.filter(
                    Bouwsoort__parameter__contains=Bouwsoort))
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

import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render

from app import models
from utils import createBijlageZip, writeDiffPdf, writePdf

from . import forms


# Create your views here.
@staff_member_required
def GeneratePVEView(request, versie_pk):
    pve_versie = models.PVEVersie.objects.get(id=versie_pk)

    if request.method == "POST":

        # get user entered form and set the parameters to its version
        form = forms.PVEParameterForm(request.POST)
        form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
            versie=pve_versie
        ).all()
        form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
            versie=pve_versie
        ).all()

        # check validity
        if form.is_valid():

            # get parameters, find all pveitems with that
            (
                Bouwsoort1,
                TypeObject1,
                Doelgroep1,
                Bouwsoort2,
                TypeObject2,
                Doelgroep2,
                Bouwsoort3,
                TypeObject3,
                Doelgroep3,
                Smarthome,
                AED,
                EntreeUpgrade,
                Pakketdient,
                JamesConcept,
            ) = (
                form.cleaned_data["Bouwsoort1"],
                form.cleaned_data["TypeObject1"],
                form.cleaned_data["Doelgroep1"],
                form.cleaned_data["Bouwsoort2"],
                form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep2"],
                form.cleaned_data["Bouwsoort3"],
                form.cleaned_data["TypeObject3"],
                form.cleaned_data["Doelgroep3"],
                form.cleaned_data["Smarthome"],
                form.cleaned_data["AED"],
                form.cleaned_data["EntreeUpgrade"],
                form.cleaned_data["Pakketdient"],
                form.cleaned_data["JamesConcept"],
            )

            # Entered parameters are in the manytomany parameters of the object
            basic_PVE = models.PVEItem.objects.filter(
                Q(versie__id=versie_pk) & Q(basisregel=True)
            )

            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.filter(
                    versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort1
                )
            )

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort2
                    )
                )
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort3
                    )
                )
            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk,
                        TypeObject__parameter__contains=TypeObject1,
                    )
                )
            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk,
                        TypeObject__parameter__contains=TypeObject2,
                    )
                )
            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk,
                        TypeObject__parameter__contains=TypeObject3,
                    )
                )
            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep1
                    )
                )
            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep2
                    )
                )
            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep3
                    )
                )

            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(Q(AED=True) & Q(versie__id=versie_pk))
                )
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(Smarthome=True) & Q(versie__id=versie_pk)
                    )
                )
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(EntreeUpgrade=True) & Q(versie__id=versie_pk)
                    )
                )
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(Pakketdient=True) & Q(versie__id=versie_pk)
                    )
                )
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.filter(
                        Q(JamesConcept=True) & Q(versie__id=versie_pk)
                    )
                )

            basic_PVE = basic_PVE.order_by("id")

            # make pdf
            parameters = []

            if Bouwsoort1:
                parameters += (f"{Bouwsoort1.parameter} (Hoofd)",)
            if Bouwsoort2:
                parameters += (f"{Bouwsoort2.parameter} (Sub)",)
            if Bouwsoort3:
                parameters += (f"{Bouwsoort3.parameter} (Sub)",)
            if TypeObject1:
                parameters += (f"{TypeObject1.parameter} (Hoofd)",)
            if TypeObject2:
                parameters += (f"{TypeObject2.parameter} (Sub)",)
            if TypeObject3:
                parameters += (f"{TypeObject3.parameter} (Sub)",)
            if Doelgroep1:
                parameters += (f"{Doelgroep1.parameter} (Hoofd)",)
            if Doelgroep2:
                parameters += (f"{Doelgroep2.parameter} (Sub)",)
            if Doelgroep3:
                parameters += (f"{Doelgroep3.parameter} (Sub)",)

            date = datetime.datetime.now()

            fileExt = "%s%s%s%s%s%s" % (
                date.strftime("%H"),
                date.strftime("%M"),
                date.strftime("%S"),
                date.strftime("%d"),
                date.strftime("%m"),
                date.strftime("%Y"),
            )

            filename = f"PvE-{fileExt}"
            zipFilename = f"PvE_Compleet-{fileExt}"

            # needed to generate
            opmerkingen = {}
            bijlagen = {}
            reacties = {}
            reactiebijlagen = {}

            versie_naam = versie.versie
            pdfmaker = writePdf.PDFMaker(versie_naam)
            pdfmaker.makepdf(
                filename,
                basic_PVE,
                versie_pk,
                opmerkingen,
                bijlagen,
                reacties,
                reactiebijlagen,
                parameters,
                [],
            )

            # get bijlagen
            bijlagen = [item for item in basic_PVE if item.bijlage]

            if bijlagen:
                zipmaker = createBijlageZip.ZipMaker()
                zipmaker.makeZip(zipFilename, filename, bijlagen)
            else:
                zipFilename = False

            # and render the result page
            context = {}
            context["itemsPVE"] = basic_PVE
            context["filename"] = filename
            context["zipFilename"] = zipFilename
            return render(request, "PVEResult.html", context)
        else:
            messages.warning(request, "Vul de verplichte keuzes in.")

    form = forms.PVEParameterForm()

    form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["Bouwsoort3"].queryset = models.Bouwsoort.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["TypeObject3"].queryset = models.TypeObject.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
        versie=pve_versie
    ).all()
    form.fields["Doelgroep3"].queryset = models.Doelgroep.objects.filter(
        versie=pve_versie
    ).all()

    # if get method, just render the empty form
    context = {}
    context["form"] = form
    context["versie_pk"] = versie_pk
    return render(request, "GeneratePVE.html", context)


@login_required
def download_file(request, filename):
    fl_path = settings.EXPORTS_ROOT

    filename = f"/{filename}.pdf"

    try:
        fl = open(fl_path + filename, "rb")
    except OSError:
        raise Http404("404")

    response = HttpResponse(fl, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=%s" % filename

    return response


@login_required
def download_bijlagen(request, zipFilename):
    fl_path = settings.EXPORTS_ROOT

    filename = f"/{zipFilename}.zip"

    try:
        fl = open(fl_path + filename, "rb")
    except OSError:
        raise Http404("404")

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(fl, content_type="application/x-zip-compressed")
    # ..and correct content-disposition
    resp["Content-Disposition"] = "attachment; filename=%s" % filename
    return resp


@staff_member_required
def compareView(request, versie_pk):
    context = {}
    context["versie_pk"] = versie_pk
    return render(request, "compare.html", context)


@staff_member_required
def compareFormView(request, versie_pk, pk):
    pk = int(pk)
    context = {}
    context["pk"] = pk
    context["versie_pk"] = versie_pk

    if request.method == "POST":
        if pk == 1:
            # get user entered form
            form = forms.CompareFormBouwsoort(request.POST)
            form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
                versie__id=versie_pk
            ).all()
            form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
                versie__id=versie_pk
            ).all()

        if pk == 2:
            form = forms.CompareFormTypeObject(request.POST)
            form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
                versie__id=versie_pk
            ).all()
            form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
                versie__id=versie_pk
            ).all()

        if pk == 3:
            form = forms.CompareFormDoelgroep(request.POST)
            form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
                versie__id=versie_pk
            ).all()
            form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
                versie__id=versie_pk
            ).all()

        # check validity
        if form.is_valid():
            parameters = []

            if pk == 1:
                (keuze1, keuze2) = (
                    form.cleaned_data["Bouwsoort1"],
                    form.cleaned_data["Bouwsoort2"],
                )
                PvE1 = models.PVEItem.objects.filter(
                    versie__id=versie_pk, Bouwsoort__parameter__contains=keuze1
                )
                PvE2 = models.PVEItem.objects.filter(
                    versie__id=versie_pk, Bouwsoort__parameter__contains=keuze2
                )

            if pk == 2:
                (keuze1, keuze2) = (
                    form.cleaned_data["TypeObject1"],
                    form.cleaned_data["TypeObject2"],
                )
                PvE1 = models.PVEItem.objects.filter(
                    versie__id=versie_pk, TypeObject__parameter__contains=keuze1
                )
                PvE2 = models.PVEItem.objects.filter(
                    versie__id=versie_pk, TypeObject__parameter__contains=keuze2
                )

            if pk == 3:
                (keuze1, keuze2) = (
                    form.cleaned_data["Doelgroep1"],
                    form.cleaned_data["Doelgroep2"],
                )
                PvE1 = models.PVEItem.objects.filter(
                    versie__id=versie_pk, Doelgroep__parameter__contains=keuze1
                )
                PvE2 = models.PVEItem.objects.filter(
                    versie__id=versie_pk, Doelgroep__parameter__contains=keuze2
                )

            afwijkingen = PvE1.difference(PvE2)
            afwijkingen = afwijkingen.order_by("id")

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
                    date.strftime("%Y"),
                )
                
                versie_naam = versie.versie
                pdfmaker = writeDiffPdf.PDFMaker(versie_naam)
                pdfmaker.makepdf(filename, afwijkingen, versie_pk, parameters)
                context["filename"] = filename

            context["afwijkingen"] = afwijkingen
            return render(request, "compareResults.html", context)

    # if get method, just render the empty form
    if pk == 1:
        form = forms.CompareFormBouwsoort()
        form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
            versie__id=versie_pk
        ).all()
        form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
            versie__id=versie_pk
        ).all()

    if pk == 2:
        form = forms.CompareFormTypeObject()
        form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
            versie__id=versie_pk
        ).all()
        form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
            versie__id=versie_pk
        ).all()

    if pk == 3:
        form = forms.CompareFormDoelgroep()
        form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
            versie__id=versie_pk
        ).all()
        form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
            versie__id=versie_pk
        ).all()

    context["form"] = form
    return render(request, "compareForm.html", context)

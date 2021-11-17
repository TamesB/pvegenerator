import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render
from pvetool.views.utils import GetAWSURL
from project.models import Beleggers
from app import models
from utils import createBijlageZip, writeDiffPdf, writePdf, writeExcel

from . import forms


# Create your views here.
@staff_member_required
def GeneratePVEView(request, client_pk, versie_pk):
    pve_versie = models.PVEVersie.objects.get(id=versie_pk)
    client = Beleggers.objects.get(id=client_pk)
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

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
            basic_PVE = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                Q(versie__id=versie_pk) & Q(basisregel=True)
            )

            basic_PVE = basic_PVE.union(
                models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                    versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort1
                )
            )

            if Bouwsoort2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort2
                    )
                )
            if Bouwsoort3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort3
                    )
                )
            if TypeObject1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk,
                        TypeObject__parameter__contains=TypeObject1,
                    )
                )
            if TypeObject2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk,
                        TypeObject__parameter__contains=TypeObject2,
                    )
                )
            if TypeObject3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk,
                        TypeObject__parameter__contains=TypeObject3,
                    )
                )
            if Doelgroep1:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep1
                    )
                )
            if Doelgroep2:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep2
                    )
                )
            if Doelgroep3:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep3
                    )
                )

            # If line is extra (AED, Smarthome, Entree Upgrade); Always include
            # if box checked
            if AED:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(Q(AED=True) & Q(versie__id=versie_pk))
                )
            if Smarthome:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        Q(Smarthome=True) & Q(versie__id=versie_pk)
                    )
                )
            if EntreeUpgrade:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        Q(EntreeUpgrade=True) & Q(versie__id=versie_pk)
                    )
                )
            if Pakketdient:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
                        Q(Pakketdient=True) & Q(versie__id=versie_pk)
                    )
                )
            if JamesConcept:
                basic_PVE = basic_PVE.union(
                    models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(
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

            versie_naam = pve_versie.versie
            pdfmaker = writePdf.PDFMaker(versie_naam, logo_url)
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
            bijlagen_models = models.ItemBijlages.objects.all()
            bijlagen = []

            for bijlage_model in bijlagen_models:
                for item in bijlage_model.items.all():
                    if item in basic_PVE:
                        bijlagen.append(bijlage_model)

            bijlagen = list(set(bijlagen))

            if bijlagen:
                zipmaker = createBijlageZip.ZipMaker()
                zipmaker.makeZip(zipFilename, filename, bijlagen)
            else:
                zipFilename = False
                
            worksheet = writeExcel.ExcelMaker()
            excelFilename = worksheet.linewriter(basic_PVE)
            # and render the result page
            context = {}
            context["itemsPVE"] = basic_PVE
            context["excelFilename"] = excelFilename
            context["filename"] = filename
            context["zipFilename"] = zipFilename
            context["client_pk"] = client_pk
            context["logo_url"] = logo_url
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
    context["versie"] = models.PVEVersie.objects.get(pk=versie_pk)
    context["client_pk"] = client_pk
    context["logo_url"] = logo_url

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
def compareFormView(request, versie_pk):
    versie = models.PVEVersie.objects.get(id=versie_pk)
    client = Beleggers.objects.get(id=versie.belegger.id)
    logo_url = None
    if client.logo:
        logo_url = GetAWSURL(client)

    form = forms.CompareForm(request.POST or None)
    form.fields["Bouwsoort1"].queryset = models.Bouwsoort.objects.filter(
        versie__id=versie_pk
    ).all()
    form.fields["Bouwsoort2"].queryset = models.Bouwsoort.objects.filter(
        versie__id=versie_pk
    ).all()

    form.fields["TypeObject1"].queryset = models.TypeObject.objects.filter(
        versie__id=versie_pk
    ).all()
    form.fields["TypeObject2"].queryset = models.TypeObject.objects.filter(
        versie__id=versie_pk
    ).all()

    form.fields["Doelgroep1"].queryset = models.Doelgroep.objects.filter(
        versie__id=versie_pk
    ).all()
    form.fields["Doelgroep2"].queryset = models.Doelgroep.objects.filter(
        versie__id=versie_pk
    ).all()

    context = {}
    context["logo_url"] = logo_url
    context["versie_pk"] = versie_pk
    context["versie"] = models.PVEVersie.objects.get(pk=versie_pk)
    context["form"] = form

    if request.method == "POST":

        # check validity
        if form.is_valid():
            parameters = []

            (Bouwsoort1, Bouwsoort2, TypeObject1, TypeObject2, Doelgroep1, Doelgroep2) = (
                form.cleaned_data["Bouwsoort1"],
                form.cleaned_data["Bouwsoort2"],
                form.cleaned_data["TypeObject1"],
                form.cleaned_data["TypeObject2"],
                form.cleaned_data["Doelgroep1"],
                form.cleaned_data["Doelgroep2"],
            )
            print(form.cleaned_data["Bouwsoort1"], form.cleaned_data["Bouwsoort2"])
            titel = ""

            eerste_pve = None
            eerste_count = 0

            if Bouwsoort1:
                eerste_pve = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort1)
                titel += f"{Bouwsoort1} "
                eerste_count += 1
            if TypeObject1:
                if eerste_pve:
                    eerste_pve.union(models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, TypeObject__parameter__contains=TypeObject1))
                else:
                    eerste_pve = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, TypeObject__parameter__contains=TypeObject1)
                titel += f"{TypeObject1} "
                eerste_count += 1
            if Doelgroep1:
                if eerste_pve:
                    eerste_pve.union(models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep1))
                else:
                    eerste_pve = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep1)
                titel += f"{Doelgroep1} "
                eerste_count += 1

            print(eerste_pve)
            tweede_pve = None
            titel += "t.o.v. "
            tweede_count = 0

            if Bouwsoort2:
                tweede_pve = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, Bouwsoort__parameter__contains=Bouwsoort2)
                titel += f"{Bouwsoort2} "
                tweede_count += 1
            if TypeObject2:
                if tweede_pve:
                    tweede_pve.union(models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, TypeObject__parameter__contains=TypeObject2))
                else:
                    tweede_pve = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, TypeObject__parameter__contains=TypeObject2)
                titel += f"{TypeObject2} "
                tweede_count += 1
            if Doelgroep2:
                if tweede_pve:
                    tweede_pve.union(models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep2))
                else:
                    tweede_pve = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").filter(versie__id=versie_pk, Doelgroep__parameter__contains=Doelgroep2)
                titel += f"{Doelgroep2} "
                tweede_count += 1

            titel = titel[:-1]
            if eerste_pve and tweede_pve:
                afwijkingen = eerste_pve.difference(tweede_pve)
            elif eerste_pve and not tweede_pve:
                afwijkingen = eerste_pve

                titel = ""
                if Bouwsoort1:
                    titel += f"{Bouwsoort1}, "
                if TypeObject1:
                    titel += f"{TypeObject1}, "
                if Doelgroep1:
                    titel += f"{Doelgroep1}"

            elif tweede_pve and not eerste_pve:
                afwijkingen = tweede_pve

                titel = ""
                if Bouwsoort2:
                    titel += f"{Bouwsoort2}, "
                if TypeObject2:
                    titel += f"{TypeObject2}, "
                if Doelgroep2:
                    titel += f"{Doelgroep2}"
            else:
                afwijkingen = None
            
            if afwijkingen:
                afwijkingen = afwijkingen.order_by("id")

                # make pdf
                parameters += titel

                date = datetime.datetime.now()
                filename = "AFWIJKINGEN-%s%s%s%s%s%s" % (
                    date.strftime("%H"),
                    date.strftime("%M"),
                    date.strftime("%S"),
                    date.strftime("%d"),
                    date.strftime("%m"),
                    date.strftime("%Y"),
                )
                
                versie_naam = models.PVEVersie.objects.filter(id=versie_pk).first().versie
                pdfmaker = writeDiffPdf.PDFMaker(versie_naam)
                pdfmaker.makepdf(filename, afwijkingen, versie_pk, parameters)
                context["filename"] = filename

                # get bijlagen
                bijlagen_models = models.ItemBijlages.objects.all()
                bijlagen = []

                for bijlage_model in bijlagen_models:
                    for item in bijlage_model.items.all():
                        if item in afwijkingen:
                            bijlagen.append(bijlage_model)

                bijlagen = list(set(bijlagen))

                if bijlagen:
                    zipmaker = createBijlageZip.ZipMaker()
                    zipmaker.makeZip(zipFilename, filename, bijlagen)
                else:
                    zipFilename = False

                context["zipFilename"] = zipFilename
                
                worksheet = writeExcel.ExcelMaker()
                excelFilename = worksheet.linewriter(afwijkingen)
                context["excelFilename"] = excelFilename

            context["afwijkingen"] = afwijkingen
            return render(request, "compareResults.html", context)

    # if get method, just render the empty form

    context["logo_url"] = logo_url
    return render(request, "compareForm.html", context)

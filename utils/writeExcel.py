import datetime
import os.path

import xlsxwriter
from django.conf import settings

from app import models


class ExcelMaker:
    def linewriter(self, versie_pk):
        PVEItems = [i for i in models.PVEItem.objects.prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").select_related("hoofdstuk").select_related("paragraaf").filter(versie__id=versie_pk)]

        date = datetime.datetime.now()
        filename = "PVEWORKSHEET-%s%s%s%s%s%s" % (
            date.strftime("%H"),
            date.strftime("%M"),
            date.strftime("%S"),
            date.strftime("%d"),
            date.strftime("%m"),
            date.strftime("%Y"),
        )

        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + filename

        # Create an new Excel file and add a worksheet.
        workbook = xlsxwriter.Workbook(f"{path}.xlsx")
        worksheet = workbook.add_worksheet()

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({"bold": True})

        row = 0
        column = 0

        Bouwsoorten = [
            bouwsrt for bouwsrt in models.Bouwsoort.objects.filter(versie__id=versie_pk)
        ]
        TypeObjecten = [
            typeobj
            for typeobj in models.TypeObject.objects.filter(versie__id=versie_pk)
        ]
        Doelgroepen = [
            doelgrp for doelgrp in models.Doelgroep.objects.filter(versie__id=versie_pk)
        ]

        # Titel row
        column = 1
        worksheet.write(row, column, "BASIS PVE", bold)
        column += 1

        for bouwsrt in Bouwsoorten:
            worksheet.write(row, column, bouwsrt.parameter, bold)
            column += 1

        for typeobj in TypeObjecten:
            worksheet.write(row, column, typeobj.parameter, bold)
            column += 1

        for doelgrp in Doelgroepen:
            worksheet.write(row, column, doelgrp.parameter, bold)
            column += 1

        row += 1
        column = 0

        hoofdstukken = models.PVEHoofdstuk.objects.filter(versie__id=versie_pk).order_by("id")
        hoofdstuknamen = [hoofdstuk.hoofdstuk for hoofdstuk in hoofdstukken]

        # Run door de items heen
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()
        print("start")

        bouwsoorten_item = {item.id:[i for i in item.Bouwsoort.all()] for item in PVEItems}
        typeobjecten_item = {item.id:[i for i in item.TypeObject.all()] for item in PVEItems}
        doelgroepen_item = {item.id:[i for i in item.Doelgroep.all()] for item in PVEItems}

        paragraven_hfst = {hoofdstuk.id:[i for i in models.PVEParagraaf.objects.filter(
                versie__id=versie_pk, hoofdstuk=hoofdstuk
            )] for hoofdstuk in hoofdstukken}

        for hoofdstuk in hoofdstukken:
            print(f"hoofdstuk: {hoofdstuk}")
            items = models.PVEItem.objects.select_related("hoofdstuk").select_related("paragraaf").filter(versie__id=versie_pk, hoofdstuk=hoofdstuk)
            worksheet.write(row, column, hoofdstuk.hoofdstuk, bold)
            row += 1

            paragraven = paragraven_hfst[hoofdstuk.id]

            if len(paragraven) > 0:
                for paragraaf in paragraven:
                    items_spec = [
                        item
                        for item in items
                        if item.paragraaf == paragraaf
                    ]
                    
                    worksheet.write(row, column, paragraaf.paragraaf, bold)
                    row += 1

                    for item in items_spec:
                        inhoud = "%s" % item.inhoud
                        worksheet.write(row, column, inhoud, cell_format)
                        column += 1

                        if item.basisregel:
                            worksheet.write(row, column, "x")
                            column += 1
                        else:
                            column += 1

                        for bouwsrt in Bouwsoorten:
                            if bouwsrt in bouwsoorten_item[item.id]:
                                worksheet.write(row, column, "x")
                                column += 1
                            else:
                                column += 1

                        for typeobj in TypeObjecten:
                            if typeobj in typeobjecten_item[item.id]:
                                worksheet.write(row, column, "x")
                                column += 1
                            else:
                                column += 1

                        for doelgrp in Doelgroepen:
                            if doelgrp in doelgroepen_item[item.id]:
                                worksheet.write(row, column, "x")
                                column += 1
                            else:
                                column += 1

                        row += 1
                        column = 0
            else:
                for item in items:
                    inhoud = "%s" % item.inhoud
                    worksheet.write(row, column, inhoud, cell_format)
                    column += 1

                    if item.basisregel:
                        worksheet.write(row, column, "x")
                        column += 1
                    else:
                        column += 1

                    for bouwsrt in Bouwsoorten:
                        if bouwsrt in bouwsoorten_item[item.id]:
                            worksheet.write(row, column, "x")
                            column += 1
                        else:
                            column += 1

                    for typeobj in TypeObjecten:
                        if typeobj in typeobjecten_item[item.id]:
                            worksheet.write(row, column, "x")
                            column += 1
                        else:
                            column += 1

                    for doelgrp in Doelgroepen:
                        if doelgrp in doelgroepen_item[item.id]:
                            worksheet.write(row, column, "x")
                            column += 1
                        else:
                            column += 1

                    row += 1
                    column = 0
        workbook.close()
        return filename

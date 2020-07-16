from app import models
import xlsxwriter
from django.conf import settings
import os.path
import datetime
import win32com.client as win32
import pythoncom


class ExcelMaker:

    def linewriter(self):
        PVEItems = models.PVEItem.objects.all()

        date = datetime.datetime.now()
        filename = "PVEWORKSHEET-%s%s%s%s%s%s" % (
            date.strftime("%H"),
            date.strftime("%M"),
            date.strftime("%S"),
            date.strftime("%d"),
            date.strftime("%m"),
            date.strftime("%Y")
        )

        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + filename

        # Create an new Excel file and add a worksheet.
        workbook = xlsxwriter.Workbook(f"{path}.xlsx")
        worksheet = workbook.add_worksheet()

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})

        row = 0
        column = 0

        Bouwsoorten = [bouwsrt for bouwsrt in models.Bouwsoort.objects.all()]
        TypeObjecten = [typeobj for typeobj in models.TypeObject.objects.all()]
        Doelgroepen = [doelgrp for doelgrp in models.Doelgroep.objects.all()]

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

        hoofdstukken = models.PVEHoofdstuk.objects.all()
        hoofdstuknamen = [hoofdstuk.hoofdstuk for hoofdstuk in hoofdstukken]

        # Run door de items heen
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()

        for hoofdstuk in hoofdstukken:
            
            items_exist = [item for item in PVEItems if item.hoofdstuk == hoofdstuk]
            if len(items_exist) > 0:
                worksheet.write(row, column, hoofdstuk.hoofdstuk, bold)
                row += 1
                
                paragraven = models.PVEParagraaf.objects.filter(hoofdstuk=hoofdstuk)
                
                if paragraven.exists():
                    for paragraaf in paragraven:
                        items = [item for item in PVEItems if item.hoofdstuk == hoofdstuk and item.paragraaf == paragraaf]

                        if len(items) > 0:
                            worksheet.write(row, column, paragraaf.paragraaf, bold)
                            row += 1

                            for item in items:
                                inhoud = ("%s" % item.inhoud)
                                worksheet.write(row, column, inhoud, cell_format)
                                column += 1

                                if item.basisregel:
                                    worksheet.write(row, column, "x")
                                    column += 1
                                else:
                                    column += 1

                                for bouwsrt in Bouwsoorten:
                                    if bouwsrt in item.Bouwsoort.all():
                                        worksheet.write(row, column, "x")
                                        column += 1
                                    else:
                                        column += 1

                                for typeobj in TypeObjecten:
                                    if typeobj in item.TypeObject.all():
                                        worksheet.write(row, column, "x")
                                        column += 1
                                    else:
                                        column += 1
                                
                                for doelgrp in Doelgroepen:
                                    if doelgrp in item.Doelgroep.all():
                                        worksheet.write(row, column, "x")
                                        column += 1
                                    else:
                                        column += 1

                                row += 1
                                column = 0
                                    
                else:
                    items = [item for item in PVEItems if item.hoofdstuk == hoofdstuk]
                    
                    if len(items) > 0:
                        for item in items:
                            inhoud = ("%s" % item.inhoud)
                            worksheet.write(row, column, inhoud, cell_format)
                            column += 1

                            if item.basisregel:
                                worksheet.write(row, column, "x")
                                column += 1
                            else:
                                column += 1

                            for bouwsrt in Bouwsoorten:
                                if bouwsrt in item.Bouwsoort.all():
                                    worksheet.write(row, column, "x")
                                    column += 1
                                else:
                                    column += 1

                            for typeobj in TypeObjecten:
                                if typeobj in item.TypeObject.all():
                                    worksheet.write(row, column, "x")
                                    column += 1
                                else:
                                    column += 1
                            
                            for doelgrp in Doelgroepen:
                                if doelgrp in item.Doelgroep.all():
                                    worksheet.write(row, column, "x")
                                    column += 1
                                else:
                                    column += 1

                            row += 1
                            column = 0

        workbook.close()

        pythoncom.CoInitialize()
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        wb = excel.Workbooks.Open(f"{path}.xlsx")
        ws = wb.Worksheets("Sheet1")
        ws.Columns.AutoFit()
        wb.Save()
        excel.Application.Quit()

        return filename
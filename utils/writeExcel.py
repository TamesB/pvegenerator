import datetime
import os.path

import xlsxwriter
from xlsxwriter.worksheet import (
    Worksheet, cell_number_tuple, cell_string_tuple)
from typing import Optional

from django.conf import settings

from app import models

class ExcelMaker:
    def linewriter(self, PVEItems):
        #hierboven version_pk als je hele version wil uitdraaien
        #PVEItems = [i for i in models.PVEItem.objects.prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").select_related("chapter").select_related("paragraph").filter(version__id=version_pk)]

        version_pk = PVEItems.first().version_id
        
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
        bold_rotate = workbook.add_format({"bold": True})
        bold_rotate.set_rotation(45)

        row = 0
        column = 0
        
        Bouwsoorten = [
            bouwsrt for bouwsrt in models.Bouwsoort.objects.filter(version__id=version_pk)
        ]
        TypeObjecten = [
            typeobj
            for typeobj in models.TypeObject.objects.filter(version__id=version_pk)
        ]
        Doelgroepen = [
            doelgrp for doelgrp in models.Doelgroep.objects.filter(version__id=version_pk)
        ]

        # Titel row
        column = 1
        worksheet.write(row, column, "BASIS PVE", bold_rotate)
        column += 1

        for bouwsrt in Bouwsoorten:
            worksheet.write(row, column, bouwsrt.parameter, bold_rotate)
            column += 1

        for typeobj in TypeObjecten:
            worksheet.write(row, column, typeobj.parameter, bold_rotate)
            column += 1

        for doelgrp in Doelgroepen:
            worksheet.write(row, column, doelgrp.parameter, bold_rotate)
            column += 1
            
        row += 1
        column = 0
        worksheet.freeze_panes(1, 1)
        chapters = list(set([item.chapter for item in PVEItems.order_by("id")]))

        # Run door de items heen
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()

        bouwsoorten_item = {item.id:[i for i in item.Bouwsoort.all()] for item in PVEItems}
        typeobjecten_item = {item.id:[i for i in item.TypeObject.all()] for item in PVEItems}
        doelgroepen_item = {item.id:[i for i in item.Doelgroep.all()] for item in PVEItems}

        paragraphs = list(set([item.paragraph for item in PVEItems if item.paragraph]))
        paragraphs_hfst = {chapter.id:[paragraph for paragraph in paragraphs if paragraph.chapter and paragraph.chapter == chapter] for chapter in chapters}

        for chapter in chapters:
            items = [item for item in PVEItems if item.chapter == chapter]
            worksheet.write(row, column, chapter.chapter, bold)

            row += 1

            paragraphs = paragraphs_hfst[chapter.id]

            if len(paragraphs) > 0:
                for paragraph in paragraphs:
                    items_spec = [
                        item
                        for item in items
                        if item.paragraph == paragraph
                    ]
                    
                    worksheet.write(row, column, paragraph.paragraph, bold)
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
                            
        for _ in range(len(worksheet.table.items())):
            self.set_column_autowidth(worksheet, _)
                    
        workbook.close()
        return filename


    def get_column_width(self, worksheet: Worksheet, column: int) -> Optional[int]:
        """Get the max column width in a `Worksheet` column."""
        strings = getattr(worksheet, '_ts_all_strings', None)
        if strings is None:
            strings = worksheet._ts_all_strings = sorted(
                worksheet.str_table.string_table,
                key=worksheet.str_table.string_table.__getitem__)
        lengths = set()
        for row_id, colums_dict in worksheet.table.items():  # type: int, dict
            data = colums_dict.get(column)
            if not data:
                continue
            if type(data) is cell_string_tuple:
                iter_length = len(strings[data.string])
                if not iter_length:
                    continue
                lengths.add(iter_length)
                continue
            if type(data) is cell_number_tuple:
                iter_length = len(str(data.number))
                if not iter_length:
                    continue
                lengths.add(iter_length)
        if not lengths:
            return None
        return max(lengths)


    def set_column_autowidth(self, worksheet: Worksheet, column: int):
        """
        Set the width automatically on a column in the `Worksheet`.
        !!! Make sure you run this function AFTER having all cells filled in
        the worksheet!
        """
        maxwidth = self.get_column_width(worksheet=worksheet, column=column)
        if maxwidth is None:
            return
        
        maxwidth = int(float(maxwidth) / 5)
        if maxwidth < 3:
            maxwidth = 3
            
        worksheet.set_column(first_col=column, last_col=column, width=maxwidth)

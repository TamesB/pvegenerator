import datetime
import os.path

import xlsxwriter
from xlsxwriter.worksheet import (
    Worksheet, cell_number_tuple, cell_string_tuple)
from typing import Optional

from django.conf import settings
from app import models
from project.models import PVEItemAnnotation

class WriteExcelProject:
    def linewriter(self, project):
        #hierboven version_pk als je hele version wil uitdraaien
        #PVEItems = [i for i in models.PVEItem.objects.prefetch_related("Bouwsoort").prefetch_related("TypeObject").prefetch_related("Doelgroep").select_related("chapter").select_related("paragraph").filter(version__id=version_pk)]

        version_pk = project.item.first().version_id
        
        items = project.item.select_related("chapter").select_related("paragraph").all()
        
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
        bold.set_text_wrap()

        bold_red = workbook.add_format({"bold": True})
        bold_red.set_bg_color("red")
        bold_yellow = workbook.add_format({"bold": True})
        bold_yellow.set_bg_color("yellow")
        bold_green = workbook.add_format({"bold": True})
        bold_green.set_bg_color("green")

        bold_chapter = workbook.add_format({"bold": True, 'bg_color': "#0078ae"})
        bold_chapter.set_font_color('white')
        bold_paragraph = workbook.add_format({"bold": True, 'bg_color': "#66acd1"})
        bold_paragraph.set_font_color("#204d77")
        bold_chapter.set_text_wrap()
        bold_paragraph.set_text_wrap()

        bold_rotate = workbook.add_format({"bold": True})
        bold_rotate.set_rotation(30)

        # Titel row
        column = 0
        row = 0
        
        worksheet.write(row, column, f"PvE - Project: { project.name }", bold_rotate)
        column += 1
        worksheet.write(row, column, "Status", bold_rotate)
        column += 1
        worksheet.write(row, column, "Kosten", bold_rotate)

        column = 0
        worksheet.freeze_panes(1, 1)
        worksheet.freeze_panes(1, 2)
        worksheet.freeze_panes(1, 3)
        chapters = list(set([item.chapter for item in items.order_by("id")]))

        # Run door de items heen
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()

        cell_format_blue = workbook.add_format()
        cell_format_blue.set_bg_color("#daedf2")
        cell_format_blue.set_text_wrap()

        accepted_cell = workbook.add_format()
        accepted_cell.set_bg_color("green")
        accepted_cell.set_text_wrap()

        paragraphs = list(set([item.paragraph for item in items if item.paragraph]))
        paragraphs_hfst = {chapter.id:[paragraph for paragraph in paragraphs if paragraph.chapter and paragraph.chapter == chapter] for chapter in chapters}

        annotations = {
            annotation.item.id: annotation
            for annotation in PVEItemAnnotation.objects.select_related("status").select_related("item").filter(project=project) if annotation
        }
        
        column = 3
        ann_objs = PVEItemAnnotation.objects.select_related("status").select_related("item").filter(project=project)
        first_annotate_group = ann_objs.first().user.stakeholder if ann_objs.first().user.stakeholder else ann_objs.first().user.client
        worksheet.write(row, column, f"{first_annotate_group.name}", bold_rotate)
        column = 0
        
        consequentCosts = {
            annotation.item.id: f"€ {annotation.consequentCosts} {annotation.costtype}"
            for annotation in PVEItemAnnotation.objects.select_related("status").select_related("item").filter(project=project) if annotation.consequentCosts
        }
        
        itemId_to_row = {}
        
        row += 1
        # start with writing just the PvE and the statuses
        for chapter in chapters:
            worksheet.write(row, column, chapter.chapter, bold_chapter)

            row += 1

            paragraphs = paragraphs_hfst[chapter.id]

            if len(paragraphs) > 0:
                for paragraph in paragraphs:
                    items_spec = [
                        item
                        for item in items
                        if item.paragraph == paragraph
                    ]
                    
                    worksheet.write(row, column, f"{paragraph.paragraph}", bold_paragraph)
                    row += 1

                    for item in items_spec:
                        using_format = cell_format
                        if row % 2 == 0:
                            using_format = cell_format_blue
                            
                        inhoud = "%s" % item.inhoud
                        worksheet.write(row, column, inhoud, using_format)
                        
                        if item.id in annotations.keys():
                            if annotations[item.id].status:
                                column = 1
                                
                                if "n.v.t." in f"{annotations[item.id].status}":
                                    style = bold_red
                                if "akkoord" in f"{annotations[item.id].status}":
                                    style = bold_green
                                if "niet akkoord" in f"{annotations[item.id].status}":
                                    style = bold_red
                                if "uitwerken" in f"{annotations[item.id].status}":
                                    style = bold_yellow
                                if "n.t.b." in f"{annotations[item.id].status}":
                                    style = bold_yellow
                                    
                                worksheet.write(row, column, f"{annotations[item.id].status}", style)
                            
                            comment_string = ""
                            
                            if annotations[item.id].firststatus:
                                comment_string += f"Nieuwe status: {annotations[item.id].firststatus}. "
                            if annotations[item.id].annotation:
                                comment_string += f"Opmerking: {annotations[item.id].annotation}."
                                
                            if comment_string != "":
                                column = 3
                                worksheet.write(row, column, comment_string, bold)

                                
                        if item.id in consequentCosts.keys():
                            column = 2
                            worksheet.write(row, column, f"{consequentCosts[item.id]}", bold)
                            
                        column = 0
                        
                        itemId_to_row[item.id] = row
                        row += 1
            else:
                items_chap = [item for item in items if item.chapter == chapter]
                for item in items_chap:
                    using_format = cell_format
                    if row % 2 == 0:
                        using_format = cell_format_blue

                    inhoud = "%s" % item.inhoud
                    worksheet.write(row, column, inhoud, using_format)
                    
                    if item.id in annotations.keys():
                        if annotations[item.id].status:
                            column = 1
                            
                            if "n.v.t." in f"{annotations[item.id].status}":
                                style = bold_red
                            if "akkoord" in f"{annotations[item.id].status}":
                                style = bold_green
                            if "niet akkoord" in f"{annotations[item.id].status}":
                                style = bold_red
                            if "uitwerken" in f"{annotations[item.id].status}":
                                style = bold_yellow
                            if "n.t.b." in f"{annotations[item.id].status}":
                                style = bold_yellow
                                
                            worksheet.write(row, column, f"{annotations[item.id].status}", style)
                        
                        comment_string = ""
                        
                        if annotations[item.id].firststatus:
                            comment_string += f"Nieuwe status: {annotations[item.id].firststatus}. "
                        if annotations[item.id].annotation:
                            comment_string += f"Opmerking: {annotations[item.id].annotation}."
                            
                        if comment_string != "":
                            column = 3
                            worksheet.write(row, column, comment_string, bold)

                            
                    if item.id in consequentCosts.keys():
                        column = 2
                        worksheet.write(row, column, f"{consequentCosts[item.id]}", bold)
                        
                    column = 0
                    
                    itemId_to_row[item.id] = row
                    row += 1
        
        # write the comments
        column = 4
        row = 0
        
        phases = project.phase.all()
        for phase in phases:
            replies = phase.reply.select_related("onComment__item").all()
            if replies:

                stakeholder = replies.first().user.stakeholder if replies.first().user.stakeholder else replies.first().user.client

                # write the name of the organisation that has this commentphase
                row = 0
                worksheet.write(row, column, f"{stakeholder.name} ({replies.first().date.strftime('%Y-%m-%d')})", bold_rotate)
                row += 1
                
                for reply in replies:
                    row = itemId_to_row[reply.onComment.item.id]
                    
                    comment_string = ""
                    
                    if reply.status:
                        comment_string += f"Nieuwe status: {reply.status}. "
                    if reply.comment:
                        comment_string += f"Opmerking: {reply.comment}. "
                    if reply.accept:
                        comment_string = f"akkoord."
                    
                    if comment_string != "":
                        if reply.accept:
                            worksheet.write(row, column, comment_string, accepted_cell)
                        else:
                            worksheet.write(row, column, comment_string, bold)

                column += 1

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
        if maxwidth < 20:
            maxwidth = 20
            
        if column == 1:
            maxwidth = 25

        worksheet.set_column(first_col=column, last_col=column, width=maxwidth)

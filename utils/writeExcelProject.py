import datetime
import os.path

import xlsxwriter
from xlsxwriter.worksheet import (
    Worksheet, cell_number_tuple, cell_string_tuple)
from typing import Optional

from django.conf import settings
from app import models
from project.models import PVEItemAnnotation
from PIL import Image
from urllib.request import urlopen
import numpy as np
import io

class WriteExcelProject:
    def linewriter(self, project, logo_filename_path):
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

        # Add a self.bold format to use to highlight cells.
        self.bold = workbook.add_format({"bold": True})
        self.bold.set_text_wrap()

        self.bold_red = workbook.add_format({"bold": True})
        self.bold_red.set_bg_color("red")
        self.bold_red.set_border(1)
        self.bold_red.set_border_color("#231F20")
        self.bold_yellow = workbook.add_format({"bold": True})
        self.bold_yellow.set_bg_color("yellow")
        self.bold_yellow.set_border(1)
        self.bold_yellow.set_border_color("#231F20")
        self.bold_green = workbook.add_format({"bold": True})
        self.bold_green.set_bg_color("green")
        self.bold_green.set_border(1)
        self.bold_green.set_border_color("#231F20")

        bold_chapter = workbook.add_format({"bold": True, 'bg_color': "#0078ae"})
        bold_chapter.set_font_color('white')
        bold_paragraph = workbook.add_format({"bold": True, 'bg_color': "#66acd1"})
        bold_paragraph.set_font_color("#204d77")
        bold_chapter.set_text_wrap()
        bold_paragraph.set_text_wrap()

        bold_rotate = workbook.add_format({"bold": True, 'bg_color': "#0078ae"})
        bold_rotate.set_font_color('white')
        bold_rotate.set_rotation(30)

        self.column = 0
        self.row = 0
        
        worksheet.freeze_panes(1, 1)
        worksheet.freeze_panes(1, 2)
        worksheet.freeze_panes(1, 3)
        chapters = list(set([item.chapter for item in items.order_by("id")]))

        # Run door de items heen
        self.cell_format = workbook.add_format()
        self.cell_format.set_text_wrap()

        self.cell_format_blue = workbook.add_format()
        self.cell_format_blue.set_bg_color("#daedf2")
        self.cell_format_blue.set_text_wrap()
        
        accepted_cell = workbook.add_format()
        accepted_cell.set_bg_color("green")
        accepted_cell.set_text_wrap()

        self.grey_bg = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
        self.grey_bg.set_border(1)
        self.grey_bg.set_border_color("#231F20")

        # define paragraphs and map their id's
        paragraphs = list(set([item.paragraph for item in items if item.paragraph]))
        paragraphs_hfst = {chapter.id:[paragraph for paragraph in paragraphs if paragraph.chapter and paragraph.chapter == chapter] for chapter in chapters}

        # get the first self.annotations and map their id's
        self.annotations = {
            annotation.item.id: annotation
            for annotation in PVEItemAnnotation.objects.select_related("status").select_related("item").filter(project=project) if annotation
        }
        
        # write the author of the first self.annotations
        self.column = 4
        ann_objs = PVEItemAnnotation.objects.select_related("status").select_related("item").filter(project=project)
        
        if ann_objs.first():
            if ann_objs.first().user:
                first_annotate_group = ann_objs.first().user.stakeholder if ann_objs.first().user.stakeholder else ann_objs.first().user.client
            else:
                first_annotate_group = None
        else:
            first_annotate_group = None
               
        header_list = []
        
        if first_annotate_group:
            header_list.append(f"{first_annotate_group.name} ({ann_objs.first().date.strftime('%Y-%m-%d %H:%M')})")
        

        self.column = 0
        
        # map the costs with their id's
        self.consequentCosts = {
            annotation.item.id: f"€ {annotation.consequentCosts} {annotation.costtype}"
            for annotation in PVEItemAnnotation.objects.select_related("status").select_related("item").filter(project=project) if annotation.consequentCosts
        }

        self.itemId_to_row = {}
        
        self.row += 1
        max_row = self.row
        # start with writing just the PvE and the statuses
        for chapter in chapters:
            worksheet.write(self.row, self.column, chapter.chapter, bold_chapter)

            self.row += 1

            paragraphs = paragraphs_hfst[chapter.id]

            if len(paragraphs) > 0:
                for paragraph in paragraphs:
                    items_spec = [
                        item
                        for item in items
                        if item.paragraph == paragraph
                    ]
                    
                    worksheet.write(self.row, self.column, f"{paragraph.paragraph}", bold_paragraph)
                    self.row += 1

                    for item in items_spec:
                        self.writeItemStatusAnnotation(item, worksheet)

            else:
                items_chap = [item for item in items if item.chapter == chapter]
                for item in items_chap:
                    self.writeItemStatusAnnotation(item, worksheet)
            
            # for length of table
            if self.row > max_row:
                max_row = self.row
        
        # write the comments
        self.column = 4
        self.row = 0
        
        phases = project.phase.all().order_by("id")
        max_col = self.column
        
        # write each further comment for each commentphase
        for phase in phases:
            replies = phase.reply.select_related("onComment__item").all()
            first_reply = replies.first()
            # if a reply exists for this commentphase
            if first_reply:
                stakeholder = first_reply.user.stakeholder if first_reply.user.stakeholder else first_reply.user.client
                header = f"{stakeholder.name} ({first_reply.date.strftime('%Y-%m-%d %H:%M')})"
                header_list.append(header)

            if replies:
                
                self.row = 1
                
                for reply in replies:
                    self.row = self.itemId_to_row[reply.onComment.item.id]
                    
                    comment_string = ""
                    
                    if reply.status:
                        comment_string   += f"Nieuwe status: {reply.status}. "
                    if reply.comment:
                        comment_string += f"Opmerking: {reply.comment}. "
                    if reply.accept:
                        comment_string = f"."
                    
                    # if the string actually has a comment (either accepted (.) or has new status/comment), post it
                    if comment_string != "":
                        style = self.bold
                        # green background if accepted
                        if reply.accept:
                            style = accepted_cell
                            
                        worksheet.write(self.row, self.column, comment_string, style)

                self.column += 1
                
                if self.column > max_col:
                    max_col = self.column
                                            
        max_col = self.column - 1    
        
        # make grey bgs and convert PvE, Status and comments to tables
        worksheet.conditional_format(0, 1, max_row, 2, {'type':'blanks', 'format': self.grey_bg})

        pve_title =  [f"PvE - Project: { project.name }"]
        cols_title = ["Status", "Kosten"]

        for col in cols_title:
            pve_title.append(col)
            
        for col in header_list:
            pve_title.append(col)
        
        print(pve_title)
        worksheet.add_table(0, 0, max_row, max_col, {"columns": [{"header": header} for header in pve_title]})
        
        # final title style
        worksheet.set_row(row=0, cell_format=bold_chapter)

        # set autowidth to beautify
        for _ in range(len(worksheet.table.items())):
            self.set_column_autowidth(worksheet, _)
        
        workbook.close()
        return filename

    def writeItemStatusAnnotation(self, item, worksheet):
        using_format = self.cell_format
        if self.row % 2 == 0:
            using_format = self.cell_format_blue

        inhoud = "%s" % item.inhoud
        worksheet.write(self.row, self.column, inhoud, using_format)
        
        if item.id in self.annotations.keys():
            if self.annotations[item.id].status:
                self.column = 1
                style = self.cell_format_blue

                if "n.v.t." in f"{self.annotations[item.id].status}":
                    style = self.bold_red
                if "akkoord" in f"{self.annotations[item.id].status}":
                    style = self.bold_green
                if "niet akkoord" in f"{self.annotations[item.id].status}":
                    style = self.bold_red
                if "uitwerken" in f"{self.annotations[item.id].status}":
                    style = self.bold_yellow
                if "n.t.b." in f"{self.annotations[item.id].status}":
                    style = self.bold_yellow
                    
                worksheet.write(self.row, self.column, f"{self.annotations[item.id].status}", style)
            
            comment_string = ""
            
            if self.annotations[item.id].firststatus:
                comment_string += f"Nieuwe status: {self.annotations[item.id].firststatus}. "
            if self.annotations[item.id].annotation:
                comment_string += f"Opmerking: {self.annotations[item.id].annotation}."
                
            if comment_string != "":
                self.column = 3
                worksheet.write(self.row, self.column, comment_string, self.bold)

                
        if item.id in self.consequentCosts.keys():
            self.column = 2
            worksheet.write(self.row, self.column, f"{self.consequentCosts[item.id]}", self.grey_bg)
            
        self.column = 0
        
        self.itemId_to_row[item.id] = self.row
        self.row += 1


    def get_column_width(self, worksheet: Worksheet, column: int) -> Optional[int]:
        """Get the max self.column width in a `Worksheet` self.column."""
        strings = getattr(worksheet, '_ts_all_strings', None)
        if strings is None:
            strings = worksheet._ts_all_strings = sorted(
                worksheet.str_table.string_table,
                key=worksheet.str_table.string_table.__getitem__)
        lengths = set()
        for _, colums_dict in worksheet.table.items():  # type: int, dict
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
        Set the width automatically on a self.column in the `Worksheet`.
        !!! Make sure you run this function AFTER having all cells filled in
        the worksheet!
        """
        maxwidth = self.get_column_width(worksheet=worksheet, column=column)
        if maxwidth is None:
            return
        
        maxwidth = int(float(maxwidth) / 5)
        if maxwidth < 20:
            maxwidth = 20
        
        if column == 0:
            maxwidth = 100
            
        if column == 1:
            maxwidth = 25
            
        if column == 2:
            maxwidth = 13

        worksheet.set_column(first_col=column, last_col=column, width=maxwidth)

# Author: Tames Boon

import datetime
import os.path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app import models


class PDFMaker:
    def __init__(self, versiename):
        self.date = datetime.datetime.now()

        self.bedrijfsname = "PVETool"

        self.defaultPageSize = letter
        self.PAGE_HEIGHT = self.defaultPageSize[1]
        self.PAGE_WIDTH = self.defaultPageSize[0]
        self.styles = getSampleStyleSheet()

        self.version = versiename
        self.Topleft = f"PVE SAREF {self.version}"
        self.Topright = "CONCEPT"
        self.Centered = "PARAMETERS"
        self.Bottomleft = "%s-%s-%s" % (
            self.date.strftime("%d"),
            self.date.strftime("%m"),
            self.date.strftime("%Y"),
        )

        self.LeftPadding = 22
        self.BottomPadding = 20
        self.TopPadding = 33
        self.RightPadding = 55

        self.InhoudWidth = self.PAGE_WIDTH - self.LeftPadding - (self.RightPadding / 3)

        self.OpmerkingBoxPadding = self.PAGE_HEIGHT - (self.TopPadding * 2)
        self.OpmerkingBoxTitelHeight = 20
        self.OpmerkingBoxHeight = -150
        self.PrePVEBoxHeight = -75
        self.logo = "./utils/logo.png"

        self.chapterStyle = ParagraphStyle(
            textColor=colors.Color(red=1, green=1, blue=1),
            backColor=colors.Color(red=49 / 255, green=133 / 255, blue=154 / 255),
            name="Normal",
            fontName="Calibri-Bold",
            fontSize=8,
            leading=12,
        )

        self.paragraphStyle = ParagraphStyle(
            textColor=colors.Color(red=33 / 255, green=89 / 255, blue=103 / 255),
            bg=colors.Color(red=182 / 255, green=221 / 255, blue=232 / 255),
            backColor=colors.Color(red=182 / 255, green=221 / 255, blue=232 / 255),
            name="Normal",
            fontName="Calibri-Bold",
            fontSize=8,
            leftIndent=30,
        )

        self.regelStyle = ParagraphStyle(
            name="Normal", fontName="Calibri", fontSize=8, leftIndent=60
        )

        self.regelStyleSwitch = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
        )

    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        # eerste pagina: opmerkingen, logo, etc aan de top. Datum en paginanr onderaan.
        canvas.setTitle(f"PvE Afwijkingen lijst")
        canvas.setAuthor(f"{self.bedrijfsname} / Tames Boon")
        # titelbox (OPMERKINGEN)
        canvas.setLineWidth(2)
        canvas.setFillColorRGB(145 / 255, 205 / 255, 219 / 255)
        canvas.setStrokeColorRGB(145 / 255, 205 / 255, 219 / 255)
        canvas.rect(
            self.LeftPadding,
            self.OpmerkingBoxPadding,
            self.InhoudWidth,
            self.OpmerkingBoxTitelHeight,
            fill=1,
        )

        # OPMERKINGEN Tekst
        canvas.setFillColorRGB(1, 1, 1)
        canvas.setFont("Calibri", 8)
        canvas.drawCentredString(
            self.PAGE_WIDTH / 2.0,
            self.OpmerkingBoxPadding + (self.TopPadding / 4),
            "OPMERKINGEN",
        )

        # opmerking box met logo erin en tekst linksonder
        canvas.setStrokeColorRGB(76 / 255, 149 / 255, 167 / 255)
        canvas.rect(
            self.LeftPadding,
            self.OpmerkingBoxPadding,
            self.InhoudWidth,
            self.OpmerkingBoxHeight,
            fill=0,
        )

        canvas.drawInlineImage(
            self.logo,
            self.LeftPadding + 8,
            self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 3) - 8,
            self.PAGE_WIDTH / 3,
            (-self.OpmerkingBoxHeight / 3),
        )

        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont("Calibri", 8)
        canvas.drawString(
            self.LeftPadding + 1,
            self.OpmerkingBoxPadding + self.OpmerkingBoxHeight + 2,
            f"PROGRAMMA VAN EISEN AFWIJKINGEN",
        )

        # Blauwe Box voordat PVE begint
        canvas.setFillColorRGB(75 / 255, 172 / 255, 198 / 255)
        canvas.setStrokeColorRGB(75 / 255, 172 / 255, 198 / 255)
        canvas.rect(
            self.LeftPadding,
            self.OpmerkingBoxPadding + self.OpmerkingBoxHeight - 10,
            self.InhoudWidth,
            self.PrePVEBoxHeight,
            fill=1,
        )

        # StandardText
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont("Calibri", 8)
        canvas.drawCentredString(
            self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - self.TopPadding, self.Centered
        )
        canvas.drawString(
            self.LeftPadding, self.PAGE_HEIGHT - self.TopPadding, self.Topleft
        )
        canvas.drawString(
            self.PAGE_WIDTH - self.RightPadding,
            self.PAGE_HEIGHT - self.TopPadding,
            self.Topright,
        )
        canvas.drawString(self.LeftPadding, self.BottomPadding, "%s" % self.Bottomleft)
        canvas.drawString(
            self.PAGE_WIDTH - self.RightPadding,
            self.BottomPadding,
            "Pagina %s" % doc.page,
        )

        canvas.restoreState()

    def myLaterPages(self, canvas, doc):
        canvas.saveState()

        # Standard text
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont("Calibri", 8)
        canvas.drawCentredString(
            self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - self.TopPadding, self.Centered
        )
        canvas.drawString(
            self.LeftPadding, self.PAGE_HEIGHT - self.TopPadding, self.Topleft
        )
        canvas.drawString(
            self.PAGE_WIDTH - self.RightPadding,
            self.PAGE_HEIGHT - self.TopPadding,
            self.Topright,
        )
        canvas.drawString(self.LeftPadding, self.BottomPadding, "%s" % self.Bottomleft)
        canvas.drawString(
            self.PAGE_WIDTH - self.RightPadding,
            self.BottomPadding,
            "Pagina %s" % doc.page,
        )

        canvas.restoreState()

    def makepdf(self, filename, PVEItems, version_pk, parameters):
        # for switching background styles between added items

        item_added = 0
        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + filename

        doc = SimpleDocTemplate(
            f"{path}.pdf",
            pagesize=letter,
            leftMargin=self.LeftPadding - 7,
            rightMargin=-7 + self.RightPadding / 3,
        )

        Story = [Spacer(0, 224)]
        style = self.styles["Normal"]

        version = models.PVEVersie.objects.get(id=version_pk)

        chapters = models.PVEHoofdstuk.objects.filter(version=version)
        
        chapters_exist = []
        paragraphs_exist = []
        
        for item in PVEItems:
            if item.chapter not in chapters_exist:
                chapters_exist.append(item.chapter)

            if item.paragraph not in paragraphs_exist:
                paragraphs_exist.append(item.paragraph)
                
        # Excel tabel simulasie
        for chapter in chapters:
            if chapter in chapters_exist:
                items_exist = [item for item in PVEItems if item.chapter == chapter]
                if len(items_exist) > 0:
                    p = Paragraph("%s" % chapter, self.chapterStyle)
                    Story.append(p)

                    paragraphs = models.PVEParagraaf.objects.filter(chapter=chapter)

                    if paragraphs.exists():
                        for paragraph in paragraphs:
                            if paragraph in paragraphs_exist:
                                items = [
                                    item
                                    for item in PVEItems
                                    if item.chapter == chapter
                                    and item.paragraph == paragraph
                                ]

                                if len(items) > 0:
                                    Story.append(Spacer(self.LeftPadding, 0))
                                    p = Paragraph(
                                        "%s" % paragraph.paragraph, self.paragraphStyle
                                    )
                                    Story.append(p)

                                    for item in items:

                                        Story.append(Spacer(self.LeftPadding, 0))
                                        inhoud = "%s" % item.inhoud

                                        if (item_added % 2) == 0:
                                            item_added += 1
                                            p = Paragraph(
                                                inhoud.replace("\n", "<br />\n"),
                                                self.regelStyle,
                                            )
                                        else:
                                            item_added += 1
                                            p = Paragraph(
                                                inhoud.replace("\n", "<br />\n"),
                                                self.regelStyleSwitch,
                                            )

                                        Story.append(p)
                    else:
                        items = [item for item in PVEItems if item.chapter == chapter]

                        if len(items) > 0:
                            for item in items:

                                Story.append(Spacer(self.LeftPadding, 0))
                                inhoud = "%s" % item.inhoud

                                if (item_added % 2) == 0:
                                    item_added += 1
                                    p = Paragraph(
                                        inhoud.replace("\n", "<br />\n"), self.regelStyle
                                    )
                                else:
                                    item_added += 1
                                    p = Paragraph(
                                        inhoud.replace("\n", "<br />\n"),
                                        self.regelStyleSwitch,
                                    )

                                Story.append(p)

        self.Centered = "".join(parameters)
        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)

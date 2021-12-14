# Author: Tames Boon

import datetime
import os.path
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from urllib.request import urlopen
import io
from app import models
from reportlab.lib.utils import ImageReader
from PIL import Image
import numpy as np

class PDFMaker:
    def __init__(self, version, logo_url):
        self.date = datetime.datetime.now()

        self.bedrijfsname = "PVETool"

        self.defaultPageSize = letter
        self.PAGE_HEIGHT = self.defaultPageSize[1]
        self.PAGE_WIDTH = self.defaultPageSize[0]
        self.styles = getSampleStyleSheet()

        self.version = version
        self.Topleft = f"PVE SAREF {self.version}"
        self.BijlageDisclaimer = f"Bijlages van regels zijn in het mapje BasisBijlages, attachments van opmerkingen in het mapje OpmerkingBijlages."
        self.GeaccepteerdDisclaimer = f"Geaccepteerde statussen zijn in het groen."
        self.NietGeaccepteerdDisclaimer = (
            f"Niet geaccepteerde statussen zijn in het rood."
        )
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
        self.TopRightPadding = 0
        self.kostenverschil = 0

        self.InhoudWidth = self.PAGE_WIDTH - self.LeftPadding - (self.RightPadding / 3)

        self.OpmerkingBoxPadding = self.PAGE_HEIGHT - (self.TopPadding * 2)
        self.OpmerkingBoxTitelHeight = 20
        self.OpmerkingBoxHeight = -150
        self.PrePVEBoxHeight = -75
        
        if logo_url:
            data = urlopen(logo_url).read()
            rgba = np.array(Image.open(io.BytesIO(data)))
            # make transparent white
            rgba[rgba[...,-1]==0] = [255,255,255,0]
            logo = Image.fromarray(rgba)
            self.logo = logo
        else:
            self.logo = None

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

        self.regelStyleOpmrk = ParagraphStyle(
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.red,
        )
        self.regelStyleOpmrkGreen = ParagraphStyle(
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.green,
        )
        self.regelStyleOpmrkOrange = ParagraphStyle(
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.orange,
        )

        self.regelStyleSwitchOpmrk = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.red,
        )
        self.regelStyleSwitchOpmrkGreen = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.green,
        )
        self.regelStyleSwitchOpmrkOrange = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.orange,
        )

    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        # eerste pagina: opmerkingen, logo, etc aan de top. Datum en paginanr onderaan.
        canvas.setTitle(f"Programma van Eisen - {self.bedrijfsname}")
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

        if self.logo:
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
            f"PROGRAMMA VAN EISEN {self.version}",
        )
        #   rode kleur voor disclaimer
        canvas.drawString(
            self.LeftPadding + 4,
            self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) + 8,
            f"Huidige kostenverschil: €{self.kostenverschil},-",
        )
        canvas.drawString(
            self.LeftPadding + 4,
            self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 2,
            self.BijlageDisclaimer,
        )
        canvas.setFillColorRGB(0, 128, 0)
        canvas.drawString(
            self.LeftPadding + 4,
            self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 12,
            self.GeaccepteerdDisclaimer,
        )
        canvas.setFillColorRGB(255, 0, 0)
        canvas.drawString(
            self.LeftPadding + 4,
            self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 22,
            self.NietGeaccepteerdDisclaimer,
        )

        canvas.setFillColorRGB(0, 0, 0)
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
            self.PAGE_WIDTH - self.RightPadding - self.TopRightPadding,
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
            self.PAGE_WIDTH - self.RightPadding - self.TopRightPadding,
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

    def makepdf(
        self,
        filename,
        PVEItems,
        version_pk,
        opmerkingen,
        attachments,
        reacties,
        reactieattachments,
        parameters,
        accepted_comment_ids,
    ):
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

        # get pve version
        version = models.PVEVersie.objects.get(id=version_pk)

        chapters = models.PVEHoofdstuk.objects.prefetch_related("paragraph").filter(version__pk=version.pk).order_by("id")

        # Excel tabel simulasie
        for chapter in chapters:

            items_exist = [item for item in PVEItems if item.chapter == chapter]
            if len(items_exist) > 0:
                p = Paragraph("%s" % chapter, self.chapterStyle)
                Story.append(p)

                paragraphs = [_ for _ in chapter.paragraph.all()]

                if paragraphs:
                    for paragraph in paragraphs:
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

                                # basis pve regels
                                inhoud = "%s" % item.inhoud
                                inhoud = inhoud

                                if (item_added % 2) == 0:
                                    item_added += 1

                                    # opmerkingen en alles printen
                                    if item.id in opmerkingen:
                                        p = Paragraph(
                                            f"{inhoud}".replace("\n", "<br />\n"),
                                            self.regelStyle,
                                        )
                                        betrokken_str = f""
                                        opmrk = f"{opmerkingen[item.id].date.strftime('%Y-%m-%d')}: "
                                        #if opmerkingen[item.id].annotation:
                                        #    opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].user}. "
                                        if opmerkingen[item.id].status:
                                            opmrk += f"Status: {opmerkingen[item.id].status}. "
                                        if opmerkingen[item.id].consequentCosts:
                                            opmrk += f"Kostenverschil: €{opmerkingen[item.id].consequentCosts} {opmerkingen[item.id].costtype}. "
                                        if opmerkingen[item.id].attachment:
                                            opmrk += f"Zie attachment(n) "

                                            for attachment in attachments[item.id]:
                                                opmrk += f"'{attachment}'. "
                                                
                                        if opmerkingen[item.id].user.stakeholder:
                                            betrokken_partij = f"{opmerkingen[item.id].user.stakeholder} "
                                        else:
                                            betrokken_partij = f"{opmerkingen[item.id].user.client} "
                                        
                                        betrokken_str += betrokken_partij
                                    
                                        if item.id in reacties:
                                            for reactie in reacties[item.id]:
                                                reactie_str = f""
                                                #if reactie.comment:
                                                #    if len(reactie_str) == 0:
                                                #        reactie_str += f"Opmerking: "
                                                #    reactie_str += f""""{reactie.comment}" -{reactie.user}. """

                                                if reactie.id in reactieattachments.keys():
                                                #    if len(reactie_str) == 0:
                                                #        reactie_str += f"Opmerking: "
                                                    
                                                #    reactie_str += f"Zie attachment(n) "                                                    
                                                
                                                    if "Zie attachment" not in opmrk and "Zie attachment" not in reactie_str:
                                                        reactie_str += f"Zie attachment(n): "
                                                    
                                                    for attachment in reactieattachments[reactie.id]:
                                                        reactie_str += f"'{attachment.name}', "
                                                        
                                                if reactie.user.stakeholder:
                                                    betrokken_partij = reactie.user.stakeholder
                                                else:
                                                    betrokken_partij = reactie.user.client
                                                    
                                                if f"{betrokken_partij}" not in betrokken_str:
                                                    betrokken_str += f", {betrokken_partij} "

                                                opmrk += reactie_str
                                                                                        
                                        opmrk += f"Betrokken partijen: {betrokken_str}"
                                     
                                        if (
                                            len(opmrk)
                                            == len(
                                                opmerkingen[item.id].date.strftime(
                                                    "%Y-%m-%d"
                                                )
                                            )
                                            + 2
                                        ):
                                            opmrk = ""

                                        opmrk = opmrk + "<br />"

                                        # kleur geaccepteerde aanvullingen/opmerkingen als groen
                                        if (
                                            opmerkingen[item.id].id
                                            in accepted_comment_ids
                                        ):
                                            j = Paragraph(
                                                f"{opmrk}".replace("\n", "<br />\n"),
                                                self.regelStyleOpmrkGreen,
                                            )
                                        else:
                                            j = Paragraph(
                                                f"{opmrk}".replace("\n", "<br />\n"),
                                                self.regelStyleOpmrk,
                                            )

                                        Story.append(p)
                                        Story.append(j)
                                    else:
                                        p = Paragraph(
                                            inhoud.replace("\n", "<br />\n"),
                                            self.regelStyle,
                                        )
                                        Story.append(p)

                                else:
                                    item_added += 1
                                    # opmerkingen en alles printen
                                    if item.id in opmerkingen:
                                        p = Paragraph(
                                            f"{inhoud}".replace("\n", "<br />\n"),
                                            self.regelStyleSwitch,
                                        )
                                        betrokken_str = f""
                                        opmrk = f"{opmerkingen[item.id].date.strftime('%Y-%m-%d')}: "
                                        #if opmerkingen[item.id].annotation:
                                        #    opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].user}. "
                                        if opmerkingen[item.id].status:
                                            opmrk += f"Status: {opmerkingen[item.id].status}. "
                                        if opmerkingen[item.id].consequentCosts:
                                            opmrk += f"Kostenverschil: €{opmerkingen[item.id].consequentCosts} {opmerkingen[item.id].costtype}. "
                                        if opmerkingen[item.id].attachment:
                                            opmrk += f"Zie attachment(n) "

                                            for attachment in attachments[item.id]:
                                                opmrk += f"'{attachment}'. "
                                                
                                        if opmerkingen[item.id].user.stakeholder:
                                            betrokken_partij = f"{opmerkingen[item.id].user.stakeholder} "
                                        else:
                                            betrokken_partij = f"{opmerkingen[item.id].user.client} "
                                        
                                        betrokken_str += betrokken_partij
                                    
                                        if item.id in reacties:
                                            for reactie in reacties[item.id]:
                                                reactie_str = f""
                                                #if reactie.comment:
                                                #    if len(reactie_str) == 0:
                                                #        reactie_str += f"Opmerking: "
                                                #    reactie_str += f""""{reactie.comment}" -{reactie.user}. """

                                                if reactie.id in reactieattachments.keys():
                                                #    if len(reactie_str) == 0:
                                                #        reactie_str += f"Opmerking: "
                                                    
                                                #    reactie_str += f"Zie attachment(n) "                                                    
                                                
                                                    if "Zie attachment" not in opmrk and "Zie attachment" not in reactie_str:
                                                        reactie_str += f"Zie attachment(n): "
                                                    
                                                    for attachment in reactieattachments[reactie.id]:
                                                        reactie_str += f"'{attachment.name}', "

                                                opmrk += reactie_str
                                                
                                                if reactie.user.stakeholder:
                                                    betrokken_partij = reactie.user.stakeholder
                                                else:
                                                    betrokken_partij = reactie.user.client
                                                    
                                                if f"{betrokken_partij}" not in betrokken_str:
                                                    betrokken_str += f", {betrokken_partij} "
                                            
                                        opmrk += f"Betrokken partijen: {betrokken_str}"

                                        if (
                                            len(opmrk)
                                            == len(
                                                opmerkingen[item.id].date.strftime(
                                                    "%Y-%m-%d"
                                                )
                                            )
                                            + 2
                                        ):
                                            opmrk = ""

                                        opmrk = opmrk + "<br />"

                                        # kleur aanvullingen/opmerkingen als groen
                                        if (
                                            opmerkingen[item.id].id
                                            in accepted_comment_ids
                                        ):
                                            j = Paragraph(
                                                f"{opmrk}".replace("\n", "<br />\n"),
                                                self.regelStyleSwitchOpmrkGreen,
                                            )
                                        else:
                                            j = Paragraph(
                                                f"{opmrk}".replace("\n", "<br />\n"),
                                                self.regelStyleSwitchOpmrk,
                                            )

                                        Story.append(p)
                                        Story.append(j)

                                    else:
                                        p = Paragraph(
                                            inhoud.replace("\n", "<br />\n"),
                                            self.regelStyleSwitch,
                                        )
                                        Story.append(p)

                else:
                    items = [item for item in PVEItems if item.chapter == chapter]
                    
                    for item in items:
                        if item.chapter.chapter == "1 ALGEMEEN":
                            print(item)
                
                    if chapter.id == 682:
                        print(items)

                    if len(items) > 0:
                        for item in items:

                            Story.append(Spacer(self.LeftPadding, 0))
                            inhoud = "%s" % item.inhoud

                            if (item_added % 2) == 0:
                                item_added += 1
                                # opmerkingen en alles printen
                                if item.id in opmerkingen:
                                    p = Paragraph(
                                        f"{inhoud}".replace("\n", "<br />\n"),
                                        self.regelStyle,
                                    )
                                    betrokken_str = f""
                                    opmrk = f"{opmerkingen[item.id].date.strftime('%Y-%m-%d')}: "
                                    #if opmerkingen[item.id].annotation:
                                    #    opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].user}. "
                                    if opmerkingen[item.id].status:
                                        opmrk += f"Status: {opmerkingen[item.id].status}. "
                                    if opmerkingen[item.id].consequentCosts:
                                        opmrk += f"Kostenverschil: €{opmerkingen[item.id].consequentCosts} {opmerkingen[item.id].costtype}. "
                                    if opmerkingen[item.id].attachment:
                                        opmrk += f"Zie attachment(n) "

                                        for attachment in attachments[item.id]:
                                            opmrk += f"'{attachment}'. "
                                            
                                    if opmerkingen[item.id].user.stakeholder:
                                        betrokken_partij = f"{opmerkingen[item.id].user.stakeholder} "
                                    else:
                                        betrokken_partij = f"{opmerkingen[item.id].user.client} "
                                    
                                    betrokken_str += betrokken_partij
                                
                                    if item.id in reacties:
                                        for reactie in reacties[item.id]:
                                            reactie_str = f""
                                            #if reactie.comment:
                                            #    if len(reactie_str) == 0:
                                            #        reactie_str += f"Opmerking: "
                                            #    reactie_str += f""""{reactie.comment}" -{reactie.user}. """

                                            if reactie.id in reactieattachments.keys():
                                            #    if len(reactie_str) == 0:
                                            #        reactie_str += f"Opmerking: "
                                                
                                            #    reactie_str += f"Zie attachment(n) "                                                    
                                            
                                                if "Zie attachment" not in opmrk and "Zie attachment" not in reactie_str:
                                                    reactie_str += f"Zie attachment(n): "
                                                
                                                for attachment in reactieattachments[reactie.id]:
                                                    reactie_str += f"'{attachment.name}', "
                                                    
                                            if reactie.user.stakeholder:
                                                betrokken_partij = reactie.user.stakeholder
                                            else:
                                                betrokken_partij = reactie.user.client
                                                
                                            if f"{betrokken_partij}" not in betrokken_str:
                                                betrokken_str += f", {betrokken_partij} "

                                            opmrk += reactie_str
                                              
                                    opmrk += f"Betrokken partijen: {betrokken_str}"

                                    if (
                                        len(opmrk)
                                        == len(
                                            opmerkingen[item.id].date.strftime(
                                                "%Y-%m-%d"
                                            )
                                        )
                                        + 2
                                    ):
                                        opmrk = ""

                                    opmrk = opmrk + "<br />"

                                    if opmerkingen[item.id].id in accepted_comment_ids:
                                        j = Paragraph(
                                            f"{opmrk}".replace("\n", "<br />\n"),
                                            self.regelStyleOpmrkGreen,
                                        )
                                    else:
                                        j = Paragraph(
                                            f"{opmrk}".replace("\n", "<br />\n"),
                                            self.regelStyleOpmrk,
                                        )

                                    Story.append(p)
                                    Story.append(j)

                                else:
                                    p = Paragraph(
                                        inhoud.replace("\n", "<br />\n"),
                                        self.regelStyle,
                                    )
                                    Story.append(p)
                            else:
                                item_added += 1
                                # opmerkingen en alles printen
                                if item.id in opmerkingen:
                                    p = Paragraph(
                                        f"{inhoud}".replace("\n", "<br />\n"),
                                        self.regelStyleSwitch,
                                    )

                                    opmrk = f"{opmerkingen[item.id].date.strftime('%Y-%m-%d')}: "
                                    #if opmerkingen[item.id].annotation:
                                    #    opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].user}. "
                                    if opmerkingen[item.id].status:
                                        opmrk += f"Status: {opmerkingen[item.id].status}. "
                                    if opmerkingen[item.id].consequentCosts:
                                        opmrk += f"Kostenverschil: €{opmerkingen[item.id].consequentCosts} {opmerkingen[item.id].costtype}."
                                    if opmerkingen[item.id].attachment:
                                        opmrk += f"Zie attachment(n) "

                                        for attachment in attachments[item.id]:
                                            opmrk += f"'{attachment}'. "

                                    if item.id in reacties:
                                        for reactie in reacties[item.id]:
                                            reactie_str = f""
                                            #if reactie.comment:
                                            #    if len(reactie_str) == 0:
                                            #        reactie_str += f"Opmerking: "
                                            #    reactie_str += f""""{reactie.comment}" -{reactie.user}. """

                                            if reactie.id in reactieattachments.keys():
                                            #    if len(reactie_str) == 0:
                                            #        reactie_str += f"Opmerking: "
                                                
                                            #    reactie_str += f"Zie attachment(n) "
                                        
                                                if "Zie attachment" not in opmrk and "Zie attachment" not in reactie_str:
                                                    reactie_str += f"Zie attachment(n): "
                                                for attachment in reactieattachments[reactie.id]:
                                                    reactie_str += f"'{attachment.name}', "

                                            opmrk += reactie_str

                                    if (
                                        len(opmrk)
                                        == len(
                                            opmerkingen[item.id].date.strftime(
                                                "%Y-%m-%d"
                                            )
                                        )
                                        + 2
                                    ):
                                        opmrk = ""

                                    opmrk = opmrk + "<br />"

                                    if opmerkingen[item.id].id in accepted_comment_ids:
                                        j = Paragraph(
                                            f"{opmrk}".replace("\n", "<br />\n"),
                                            self.regelStyleSwitchOpmrkGreen,
                                        )
                                    else:
                                        j = Paragraph(
                                            f"{opmrk}".replace("\n", "<br />\n"),
                                            self.regelStyleSwitchOpmrk,
                                        )

                                    Story.append(p)
                                    Story.append(j)

                                else:
                                    p = Paragraph(
                                        inhoud.replace("\n", "<br />\n"),
                                        self.regelStyleSwitch,
                                    )
                                    Story.append(p)

        self.Centered = " / ".join(parameters)
        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)

# Author: Tames Boon

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime

from app import models
from django.conf import settings
import os.path

class PDFMaker:
    def __init__(self):
        self.date = datetime.datetime.now()

        self.bedrijfsnaam = "Syntrus"
        
        self.defaultPageSize = letter
        self.PAGE_HEIGHT=self.defaultPageSize[1]; self.PAGE_WIDTH=self.defaultPageSize[0]
        self.styles = getSampleStyleSheet()

        self.year = self.date.strftime("%Y")
        self.Topleft = f"PVE SAREF {self.year}"
        self.BijlageDisclaimer = f"Bijlages van regels zijn in het mapje BasisBijlages, bijlagen van opmerkingen in het mapje OpmerkingBijlages."
        self.GeaccepteerdDisclaimer = f"Geaccepteerde statussen zijn in het groen."
        self.NietGeaccepteerdDisclaimer = f"Niet geaccepteerde statussen zijn in het rood."
        self.Topright = "CONCEPT"
        self.Centered = "PARAMETERS"
        self.Bottomleft = "%s-%s-%s" % (self.date.strftime("%d"), self.date.strftime("%m"), self.year)

        self.LeftPadding = 22
        self.BottomPadding = 20
        self.TopPadding = 33
        self.RightPadding = 55
        self.TopRightPadding = 0
        self.kostenverschil = 0

        self.InhoudWidth = self.PAGE_WIDTH - self.LeftPadding - (self.RightPadding / 3)

        self.OpmerkingBoxPadding = self.PAGE_HEIGHT- (self.TopPadding * 2)
        self.OpmerkingBoxTitelHeight = 20
        self.OpmerkingBoxHeight = -150
        self.PrePVEBoxHeight = -75
        self.logo = './utils/logo.png'

        self.hoofdstukStyle = ParagraphStyle(
                                textColor=colors.Color(red=1, green=1, blue=1), 
                                backColor=colors.Color(red=49/255, green=133/255, blue=154/255),
                                name='Normal', 
                                fontName='Calibri-Bold', 
                                fontSize=8, 
                                leading=12
                        )
                            
        self.paragraafStyle = ParagraphStyle(
                                textColor=colors.Color(red=33/255, green=89/255, blue=103/255), 
                                bg=colors.Color(red=182/255, green=221/255, blue=232/255), 
                                backColor=colors.Color(red=182/255, green=221/255, blue=232/255), 
                                name='Normal', 
                                fontName='Calibri-Bold', 
                                fontSize=8, 
                                leftIndent=30
                        )
                        
        self.regelStyle = ParagraphStyle(
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60
                        )
                        
        self.regelStyleSwitch = ParagraphStyle(
                                backColor=colors.Color(red=218/255, green=237/255, blue=242/255), 
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60
                        )

        self.regelStyleOpmrk = ParagraphStyle(
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60,
                                textColor=colors.red,
                        )
        self.regelStyleOpmrkGreen = ParagraphStyle(
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60,
                                textColor=colors.green,
                        )
        self.regelStyleOpmrkOrange = ParagraphStyle(
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60,
                                textColor=colors.orange,
                        )
                        
        self.regelStyleSwitchOpmrk = ParagraphStyle(
                                backColor=colors.Color(red=218/255, green=237/255, blue=242/255), 
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60,
                                textColor=colors.red,
                        )
        self.regelStyleSwitchOpmrkGreen = ParagraphStyle(
                                backColor=colors.Color(red=218/255, green=237/255, blue=242/255), 
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60,
                                textColor=colors.green,
                        )
        self.regelStyleSwitchOpmrkOrange = ParagraphStyle(
                                backColor=colors.Color(red=218/255, green=237/255, blue=242/255), 
                                name='Normal', 
                                fontName='Calibri', 
                                fontSize=8, 
                                leftIndent=60,
                                textColor=colors.orange,
                        )
                
    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        # eerste pagina: opmerkingen, logo, etc aan de top. Datum en paginanr onderaan.
        canvas.setTitle(f"Programma van Eisen - {self.bedrijfsnaam}")
        canvas.setAuthor(f"{self.bedrijfsnaam} / Tames Boon")
        # titelbox (OPMERKINGEN)
        canvas.setLineWidth(2)
        canvas.setFillColorRGB(145/255, 205/255, 219/255)
        canvas.setStrokeColorRGB(145/255, 205/255, 219/255)
        canvas.rect(self.LeftPadding, self.OpmerkingBoxPadding, self.InhoudWidth, self.OpmerkingBoxTitelHeight, fill=1)
        
        # OPMERKINGEN Tekst
        canvas.setFillColorRGB(1, 1, 1)
        canvas.setFont('Calibri',8)
        canvas.drawCentredString(self.PAGE_WIDTH/2.0, self.OpmerkingBoxPadding + (self.TopPadding / 4), "OPMERKINGEN")

        # opmerking box met logo erin en tekst linksonder
        canvas.setStrokeColorRGB(76/255, 149/255, 167/255)
        canvas.rect(self.LeftPadding, self.OpmerkingBoxPadding, self.InhoudWidth, self.OpmerkingBoxHeight, fill=0)

        canvas.drawInlineImage(self.logo, self.LeftPadding + 8, self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 3) - 8, self.PAGE_WIDTH / 3, (-self.OpmerkingBoxHeight / 3))

        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont('Calibri',8)
        canvas.drawString(self.LeftPadding + 1, self.OpmerkingBoxPadding + self.OpmerkingBoxHeight + 2, f"PROGRAMMA VAN EISEN {self.year}")
        #   rode kleur voor disclaimer
        canvas.drawString(self.LeftPadding + 4, self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) + 8, f"Huidige kostenverschil: €{self.kostenverschil},-")
        canvas.drawString(self.LeftPadding + 4, self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 2, self.BijlageDisclaimer)
        canvas.setFillColorRGB(0, 128, 0)
        canvas.drawString(self.LeftPadding + 4, self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 12, self.GeaccepteerdDisclaimer)
        canvas.setFillColorRGB(255, 0, 0)
        canvas.drawString(self.LeftPadding + 4, self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 22, self.NietGeaccepteerdDisclaimer)

        canvas.setFillColorRGB(0, 0, 0)
        # Blauwe Box voordat PVE begint
        canvas.setFillColorRGB(75/255, 172/255, 198/255)
        canvas.setStrokeColorRGB(75/255, 172/255, 198/255)
        canvas.rect(self.LeftPadding, self.OpmerkingBoxPadding + self.OpmerkingBoxHeight - 10, self.InhoudWidth, self.PrePVEBoxHeight, fill=1)
        
        # StandardText
        canvas.setFillColorRGB(0,0,0)
        canvas.setFont('Calibri',8)
        canvas.drawCentredString(self.PAGE_WIDTH/2.0, self.PAGE_HEIGHT- self.TopPadding, self.Centered)
        canvas.drawString(self.LeftPadding, self.PAGE_HEIGHT- self.TopPadding, self.Topleft)
        canvas.drawString(self.PAGE_WIDTH - self.RightPadding - self.TopRightPadding, self.PAGE_HEIGHT- self.TopPadding, self.Topright)
        canvas.drawString(self.LeftPadding, self.BottomPadding, "%s" % self.Bottomleft)
        canvas.drawString(self.PAGE_WIDTH - self.RightPadding, self.BottomPadding, "Pagina %s" % doc.page)

        canvas.restoreState()

    def myLaterPages(self, canvas, doc):
        canvas.saveState()
        
        # Standard text
        canvas.setFillColorRGB(0,0,0)
        canvas.setFont('Calibri',8)
        canvas.drawCentredString(self.PAGE_WIDTH/2.0, self.PAGE_HEIGHT- self.TopPadding, self.Centered)
        canvas.drawString(self.LeftPadding, self.PAGE_HEIGHT- self.TopPadding, self.Topleft)
        canvas.drawString(self.PAGE_WIDTH - self.RightPadding - self.TopRightPadding, self.PAGE_HEIGHT- self.TopPadding, self.Topright)
        canvas.drawString(self.LeftPadding, self.BottomPadding, "%s" % self.Bottomleft)
        canvas.drawString(self.PAGE_WIDTH - self.RightPadding, self.BottomPadding, "Pagina %s" % doc.page)

        canvas.restoreState()

    def makepdf(self, filename, PVEItems, opmerkingen, bijlagen, reacties, reactiebijlagen, parameters, accepted_comment_ids):
        # for switching background styles between added items
        
        item_added = 0
        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + filename
        
        doc = SimpleDocTemplate(f"{path}.pdf", pagesize=letter, leftMargin=self.LeftPadding - 7, rightMargin=-7+self.RightPadding / 3)
        
        Story = [Spacer(0, 224)]
        style = self.styles["Normal"]
        
        hoofdstukken = models.PVEHoofdstuk.objects.all()
        hoofdstuknamen = [hoofdstuk.hoofdstuk for hoofdstuk in hoofdstukken]
            
        # Excel tabel simulasie
        for hoofdstuk in hoofdstukken:
            
            items_exist = [item for item in PVEItems if item.hoofdstuk == hoofdstuk]
            if len(items_exist) > 0:
                p = Paragraph("%s" % hoofdstuk, self.hoofdstukStyle)
                Story.append(p)
                
                paragraven = models.PVEParagraaf.objects.filter(hoofdstuk=hoofdstuk)
                
                if paragraven.exists():
                    for paragraaf in paragraven:
                        items = [item for item in PVEItems if item.hoofdstuk == hoofdstuk and item.paragraaf == paragraaf]

                        if len(items) > 0:
                            Story.append(Spacer(self.LeftPadding, 0))
                            p = Paragraph("%s" % paragraaf.paragraaf, self.paragraafStyle)
                            Story.append(p)

                            for item in items:
                                
                                Story.append(Spacer(self.LeftPadding, 0))

                                # basis pve regels
                                inhoud = "%s" % item.inhoud
                                inhoud = (inhoud)

                                if (item_added % 2) == 0:
                                    item_added += 1

                                    # opmerkingen en alles printen
                                    if item.id in opmerkingen:
                                        p = Paragraph(f"{inhoud}".replace('\n','<br />\n'), self.regelStyle)

                                        opmrk = f"{opmerkingen[item.id].datum.strftime('%Y-%m-%d')}: "
                                        if opmerkingen[item.id].annotation:
                                            opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].gebruiker}. "
                                        if opmerkingen[item.id].status:
                                            opmrk += f"Status: {opmerkingen[item.id].status}. "
                                        if opmerkingen[item.id].kostenConsequenties:
                                            opmrk += f"Kostenverschil: €{opmerkingen[item.id].kostenConsequenties}. "
                                        if opmerkingen[item.id].bijlage:
                                            opmrk += f"Zie bijlage '{bijlagen[item.id].bijlage}'. "
                                        
                                        if item.id in reacties:
                                            reactie_str = f""
                                            for reactie in reacties[item.id]:
                                                if reactie.comment:
                                                    if len(reactie_str) == 0:
                                                        reactie_str += f"Opmerkingen: "
                                                    reactie_str += f""""{reactie.comment}" -{reactie.gebruiker}. """

                                                if reactie.id in reactiebijlagen:
                                                    if len(reactie_str) == 0:
                                                        reactie_str += f"Opmerkingen: "
                                                    reactie_str += f"Zie bijlage '{reactiebijlagen[reactie.id].bijlage}'. "
                                                
                                            opmrk += reactie_str

                                        if len(opmrk) == len(opmerkingen[item.id].datum.strftime('%Y-%m-%d')) + 2:
                                            opmrk = ""
                                        
                                        opmrk = (opmrk)
     
                                        # kleur geaccepteerde aanvullingen/opmerkingen als groen
                                        if opmerkingen[item.id].id in accepted_comment_ids:
                                            j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleOpmrkGreen)
                                        else:
                                            j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleOpmrk)

                                        Story.append(p)
                                        Story.append(j)
                                    else:
                                        p = Paragraph(inhoud.replace('\n','<br />\n'), self.regelStyle)
                                        Story.append(p)


                                else:
                                    item_added += 1

                                    # opmerkingen en alles printen
                                    if item.id in opmerkingen:
                                        p = Paragraph(f"{inhoud}".replace('\n','<br />\n'), self.regelStyleSwitch)

                                        opmrk = f"{opmerkingen[item.id].datum.strftime('%Y-%m-%d')}: "
                                        if opmerkingen[item.id].annotation:
                                            opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].gebruiker}. "
                                        if opmerkingen[item.id].status:
                                            opmrk += f"Status: {opmerkingen[item.id].status}. "
                                        if opmerkingen[item.id].kostenConsequenties:
                                            opmrk += f"Kostenverschil: €{opmerkingen[item.id].kostenConsequenties}. "
                                        if opmerkingen[item.id].bijlage:
                                            opmrk += f"Zie bijlage '{bijlagen[item.id].bijlage}'. "
                                        
                                        if item.id in reacties:
                                            reactie_str = f""
                                            for reactie in reacties[item.id]:
                                                if reactie.comment:
                                                    if len(reactie_str) == 0:
                                                        reactie_str += f"Opmerkingen: "
                                                    reactie_str += f"'{reactie.comment}' -{reactie.gebruiker}. "

                                                if reactie.id in reactiebijlagen:
                                                    if len(reactie_str) == 0:
                                                        reactie_str += f"Opmerkingen: "
                                                    reactie_str += f"Zie bijlage '{reactiebijlagen[reactie.id].bijlage}'. "
                                                
                                            opmrk += reactie_str
                                        
                                        if len(opmrk) == len(opmerkingen[item.id].datum.strftime('%Y-%m-%d')) + 2:
                                            opmrk = ""

                                        opmrk = (opmrk)

                                        # kleur aanvullingen/opmerkingen als groen
                                        if opmerkingen[item.id].id in accepted_comment_ids:
                                            j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleSwitchOpmrkGreen)
                                        else:
                                            j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleSwitchOpmrk)

                                        Story.append(p)
                                        Story.append(j)

                                    else:
                                        p = Paragraph(inhoud.replace('\n','<br />\n'), self.regelStyleSwitch)
                                        Story.append(p)

                                    
                else:
                    items = [item for item in PVEItems if item.hoofdstuk == hoofdstuk]
                    
                    if len(items) > 0:
                        for item in items:
                            
                            Story.append(Spacer(self.LeftPadding, 0))
                            inhoud = ("%s" % item.inhoud)
                            
                            if (item_added % 2) == 0:
                                item_added += 1
                                # opmerkingen en alles printen
                                if item.id in opmerkingen:
                                    p = Paragraph(f"{inhoud}".replace('\n','<br />\n'), self.regelStyle)

                                    opmrk = f"{opmerkingen[item.id].datum.strftime('%Y-%m-%d')}: "
                                    if opmerkingen[item.id].annotation:
                                        opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].gebruiker}. "
                                    if opmerkingen[item.id].status:
                                        opmrk += f"Status: {opmerkingen[item.id].status}. "
                                    if opmerkingen[item.id].kostenConsequenties:
                                        opmrk += f"Kostenverschil: €{opmerkingen[item.id].kostenConsequenties}. "
                                    if opmerkingen[item.id].bijlage:
                                        opmrk += f"Zie bijlage '{bijlagen[item.id].bijlage}'. "
                                    
                                    if item.id in reacties:
                                        reactie_str = f""
                                        for reactie in reacties[item.id]:
                                            if reactie.comment:
                                                if len(reactie_str) == 0:
                                                    reactie_str += f"Opmerkingen: "
                                                reactie_str += f"'{reactie.comment}' -{reactie.gebruiker}. "

                                            if reactie.id in reactiebijlagen:
                                                if len(reactie_str) == 0:
                                                    reactie_str += f"Opmerkingen: "
                                                reactie_str += f"Zie bijlage '{reactiebijlagen[reactie.id].bijlage}'. "
                                            
                                        opmrk += reactie_str
                                                                            
                                    if len(opmrk) == len(opmerkingen[item.id].datum.strftime('%Y-%m-%d')) + 2:
                                        opmrk = ""

                                    opmrk = (opmrk)

                                    if opmerkingen[item.id].id in accepted_comment_ids:
                                        j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleOpmrkGreen)
                                    else:
                                        j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleOpmrk)
                                    
                                    Story.append(p)
                                    Story.append(j)

                                else:
                                    p = Paragraph(inhoud.replace('\n','<br />\n'), self.regelStyle)
                                    Story.append(p)
                            else:
                                item_added += 1
                                # opmerkingen en alles printen
                                if item.id in opmerkingen:
                                    p = Paragraph(f"{inhoud}".replace('\n','<br />\n'), self.regelStyleSwitch)

                                    opmrk = f"{opmerkingen[item.id].datum.strftime('%Y-%m-%d')}: "
                                    if opmerkingen[item.id].annotation:
                                        opmrk += f"Aanvulling: '{opmerkingen[item.id].annotation}' -{opmerkingen[item.id].gebruiker}. "
                                    if opmerkingen[item.id].status:
                                        opmrk += f"Status: {opmerkingen[item.id].status}. "
                                    if opmerkingen[item.id].kostenConsequenties:
                                        opmrk += f"Kostenverschil: €{opmerkingen[item.id].kostenConsequenties}. "
                                    if opmerkingen[item.id].bijlage:
                                        opmrk += f"Zie bijlage '{bijlagen[item.id].bijlage}'. "
                                    
                                    if item.id in reacties:
                                        reactie_str = f""
                                        for reactie in reacties[item.id]:
                                            if reactie.comment:
                                                if len(reactie_str) == 0:
                                                    reactie_str += f"Opmerkingen: "
                                                reactie_str += f"'{reactie.comment}' -{reactie.gebruiker}. "

                                            if reactie.id in reactiebijlagen:
                                                if len(reactie_str) == 0:
                                                    reactie_str += f"Opmerkingen: "
                                                reactie_str += f"Zie bijlage '{reactiebijlagen[reactie.id].bijlage}'. "
                                            
                                        opmrk += reactie_str
                                                                        
                                    if len(opmrk) == len(opmerkingen[item.id].datum.strftime('%Y-%m-%d')) + 2:
                                        opmrk = ""

                                    opmrk = (opmrk)

                                    if opmerkingen[item.id].id in accepted_comment_ids:
                                        j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleSwitchOpmrkGreen)
                                    else:
                                        j = Paragraph(f"{opmrk}".replace('\n','<br />\n'), self.regelStyleSwitchOpmrk)
                                    
                                    Story.append(p)
                                    Story.append(j)

                                else:
                                    p = Paragraph(inhoud.replace('\n','<br />\n'), self.regelStyleSwitch)
                                    Story.append(p)
                                        
        self.Centered = " / ".join(parameters)
        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
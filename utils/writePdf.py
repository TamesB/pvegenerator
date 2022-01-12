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
from PIL import Image
import numpy as np

class PDFMaker:
    def __init__(self, version, logo_url, project):
        self.date = datetime.datetime.now()

        self.bedrijfsname = "PVETool"
        self.project = project
        
        self.stakeholders = None
        if project:
            self.stakeholders = project.organisaties.all()
            self.stakeholderDisclaimer = f"Betrokken partijen: {project.client.name} (hierna genoteerd als; {project.client.name[0]}), "
            
            
            for stakeholder in self.stakeholders:
                if f"(hierna genoteerd als; {stakeholder.name[0]})" in self.stakeholderDisclaimer:
                    self.stakeholderDisclaimer += f"{stakeholder.name} (hierna genoteerd als; {stakeholder.name[0:1]}), "
                else:
                    self.stakeholderDisclaimer += f"{stakeholder.name} (hierna genoteerd als; {stakeholder.name[0]}), "

            self.stakeholderDisclaimer = self.stakeholderDisclaimer[:-2]
        
        self.defaultPageSize = letter
        self.PAGE_HEIGHT = self.defaultPageSize[1]
        self.PAGE_WIDTH = self.defaultPageSize[0]
        self.styles = getSampleStyleSheet()

        self.version = version
        self.Topleft = f"PVE versie {self.version}"
        self.IntroDisclaimer = ""
        if self.project:
            self.IntroDisclaimer = f"Een voortgangs snapshot van het PvE overeenkomst van project {self.project.name} van {self.project.client.name}. De gebruikte PvE versie is {self.version}."
            if self.project.fullyFrozen:
                self.IntroDisclaimer = f"De voltooide versie van het PvE overeenkomst van project {self.project.name} van {self.project.client.name}. De gebruikte PvE versie is {self.version}."
        self.BijlageDisclaimer = f"Bijlages van regels zijn te vinden in het mapje BasisBijlages, bijlagen van opmerkingen zijn te vinden in het mapje OpmerkingBijlages."
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

        self.ruleStyle = ParagraphStyle(
            name="Normal", fontName="Calibri", fontSize=8, leftIndent=60
        )

        self.ruleStyleSwitch = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
        )

        self.ruleStyleRed = ParagraphStyle(
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.red,
        )
        self.ruleStyleGreen = ParagraphStyle(
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.green,
        )
        self.ruleStyleOrange = ParagraphStyle(
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.orange,
        )

        self.ruleStyleSwitchRed = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.red,
        )
        self.ruleStyleSwitchGreen = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.green,
        )
        self.ruleStyleSwitchOrange = ParagraphStyle(
            backColor=colors.Color(red=218 / 255, green=237 / 255, blue=242 / 255),
            name="Normal",
            fontName="Calibri",
            fontSize=8,
            leftIndent=60,
            textColor=colors.orange,
        )

        
    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        # eerste pagina: annotations, logo, etc aan de top. Datum en paginanr onderaan.
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

        if self.project:
            canvas.drawString(
                self.LeftPadding + 4,
                self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) + 8,
                self.IntroDisclaimer,
            )

            canvas.drawString(
                self.LeftPadding + 4,
                self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 2,
                f"Huidige totale kostenverschil: €{self.kostenverschil},-",
            )

        canvas.drawString(
            self.LeftPadding + 4,
            self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 12,
            self.BijlageDisclaimer,
        )
        
        if self.project:
            canvas.setFillColorRGB(0, 128, 0)
            canvas.drawString(
                self.LeftPadding + 4,
                self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 22,
                self.GeaccepteerdDisclaimer,
            )
            canvas.setFillColorRGB(255, 0, 0)
            canvas.drawString(
                self.LeftPadding + 4,
                self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 32,
                self.NietGeaccepteerdDisclaimer,
            )
            canvas.setFillColorRGB(0, 0, 0)
            canvas.drawString(
                self.LeftPadding + 4,
                self.OpmerkingBoxPadding + (self.OpmerkingBoxHeight / 2) - 42,
                self.stakeholderDisclaimer,
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
        
    def generateRuleBasicInfo(self, annotations, item, attachments):
        # add the party of the first replier to the party-string, with its initial
        if annotations[item.id].user.stakeholder:
            party_involved = f"{annotations[item.id].user.stakeholder} "
        else:
            party_involved = f"{annotations[item.id].user.client} "
            
        # add the first time, and the party initial. Empty string for comparison after if anything is added.
        total_string = f"<b>Totaal:</b> "
        empty_string = f"<b>Totaal:</b> "
        
        # here we add the basic info (status and costs)
        if annotations[item.id].status:
            total_string += f"<b>Status: {annotations[item.id].status}. </b>"
        if annotations[item.id].consequentCosts:
            total_string += f"<b>Kostenverschil: €{annotations[item.id].consequentCosts} {annotations[item.id].costtype}. </b>"
        
        start_comments = "<br />Opmerkingsverloop: "
        total_string += start_comments
        
        # now we add annotations and attachments added specifically by the first replier.
        second_string = f"<i>({annotations[item.id].date.strftime('%Y-%m-%d')})</i> <b>{ party_involved[0] }:</b> "
        empty_second_string = f"<i>({annotations[item.id].date.strftime('%Y-%m-%d')})</i> <b>{ party_involved[0] }:</b> "
        
        if annotations[item.id].firststatus:
            second_string += f"Nieuwe status: {annotations[item.id].firststatus}. "
        if annotations[item.id].annotation:
            second_string += f""""{annotations[item.id].annotation}". """
        if annotations[item.id].attachment:
            second_string += f"Zie bijlage(n) "

            for attachment in attachments[item.id]:
                second_string += f"'{attachment}'. "
        
        if second_string != empty_second_string:
            second_string += "<br />"
            total_string += second_string
            
        # just don't show anything if there are no statuses/costs/attachments
        if total_string == (empty_string + start_comments):
            total_string = ""
        
        return total_string

    def generateRepliesToRule(self, annotations, item, replies, replyAttachments, total_string):
        # if the item has replies
        all_replies = ""
        if item.id in replies:
            # for each reply
            for reply in replies[item.id]:
                # add the repliers party to the party-string
                if reply.user.stakeholder:
                    party_involved = f"{reply.user.stakeholder}"
                else:
                    party_involved = f"{reply.user.client}"
                    
                # initiate comment with the party initial, and "empty string" for comparison
                single_comment = f"""<i>({reply.date.strftime('%Y-%m-%d')})</i> <b>{ party_involved[0] }:</b> """
                empty_string = f"""<i>({reply.date.strftime('%Y-%m-%d')})</i> <b>{ party_involved[0] }:</b> """
                
                if reply.status:
                    single_comment += f"Nieuwe status: {reply.status}. "
                
                # if it has a comment, add the first letter of the party and the comment
                if reply.comment:
                    single_comment += f""""{reply.comment}". """

                # if the party accepted the status
                if reply.accept:
                    single_comment += "<i>akkoord.</i> "
                    
                # if the reply has attachments
                if reply.id in replyAttachments.keys():
                
                    # if the string doesnt have attachment initiation yet, add it
                    if "Zie bijlage(n)" not in total_string and "Zie bijlage" not in single_comment:
                        single_comment += f"Zie bijlage(n): "
                    
                    # add all the attachments to the string
                    for attachment in replyAttachments[reply.id]:
                        single_comment += f"'{attachment.name}', "
                
                # check if anything is added.
                if single_comment != empty_string:
                    # ensure newline to next comment if there is any added
                    if "<br />" not in single_comment:
                        single_comment += "<br />"
                        
                # otherwise just delete the string (not useful anyways)
                else:
                    single_comment = ""

                all_replies += single_comment
        
        # add all replies
        total_string += all_replies
        
        # if there isnt any replies, change to empty string.
        if (
            len(total_string)
            == len(
                annotations[item.id].date.strftime(
                    "%Y-%m-%d"
                )
            )
            + 2
        ):
            total_string = ""
        
        return total_string

    def styleParagraph(self, annotations, accepted_comment_ids, total_string, Story, item_added, item):
        # blue or white background?
        styleGreen = self.ruleStyleGreen
        ruleStyle = self.ruleStyleRed
        
        if (item_added % 2) != 0:
            styleGreen = self.ruleStyleSwitchGreen
            ruleStyle = self.ruleStyleSwitchRed

        # color the text green if the rule is accepted
        if (
            annotations[item.id].id
            in accepted_comment_ids
        ):
            j = Paragraph(
                f"{total_string}".replace("\n", "<br />\n"),
                styleGreen,
            )
        else:
            j = Paragraph(
                f"{total_string}".replace("\n", "<br />\n"),
                ruleStyle,
            )

        return j
    
    def writeReplies(self, Story, item, content, annotations, replies, attachments, replyAttachments, accepted_comment_ids, item_added):
        # determine the background color
        style = self.ruleStyle
        
        if (item_added % 2) != 0:
            style = self.ruleStyleSwitch

        # create paragraph of the item, replacing pythonic linebreak with html linebreak
        p = Paragraph(
            content.replace("\n", "<br />\n"),
            style,
        )
        
        # if the item has replies
        if item.id in annotations:
            
            # create the text of the replies
            total_string = self.generateRuleBasicInfo(annotations, item, attachments)
            total_string = self.generateRepliesToRule(annotations, item, replies, replyAttachments, total_string)
            j = self.styleParagraph(annotations, accepted_comment_ids, total_string, Story, item_added, item)
            
            # write the item (p) and replies (j)
            Story.append(p)
            Story.append(j)
        else:
            # only write the item if no replies
            Story.append(p)

    def makepdf(
        self,
        filename,
        PVEItems,
        version_pk,
        annotations,
        attachments,
        replies,
        replyAttachments,
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

        # Go through the chapters
        for chapter in chapters:

            items_exist = [item for item in PVEItems if item.chapter == chapter]
            if len(items_exist) > 0:
                p = Paragraph("%s" % chapter, self.chapterStyle)
                Story.append(p)

                paragraphs = [_ for _ in chapter.paragraph.all()]

                # spacing difference of paragraphs
                if paragraphs:
                    # go through each paragraph
                    for paragraph in paragraphs:
                        items = [
                            item
                            for item in PVEItems
                            if item.chapter == chapter
                            and item.paragraph == paragraph
                        ]                            

                        # if items exist within this paragraph, write the paragraph title first
                        if len(items) > 0:
                            Story.append(Spacer(self.LeftPadding, 0))
                            p = Paragraph(
                                "%s" % paragraph.paragraph, self.paragraphStyle
                            )
                            Story.append(p)

                            # write each item
                            for item in items:
                                Story.append(Spacer(self.LeftPadding, 0))

                                # basis pve rules
                                content = "%s" % item.inhoud
                                content = content

                                item_added += 1
                                    
                                # write replies of this item
                                self.writeReplies(Story, item, content, annotations, replies, attachments, replyAttachments, accepted_comment_ids, item_added)

                # otherwise directly write items
                else:
                    items = [item for item in PVEItems if item.chapter == chapter]
                    
                    if len(items) > 0:
                        for item in items:

                            Story.append(Spacer(self.LeftPadding, 0))
                            content = "%s" % item.inhoud
                            item_added += 1
                            
                            # write replies of this item
                            self.writeReplies(Story, item, content, annotations, replies, attachments, replyAttachments, accepted_comment_ids, item_added)
                            


        self.Centered = " / ".join(parameters)
        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)


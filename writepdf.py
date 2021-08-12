from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import csv


with open('deelnemerslijst.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        row = row[0]
        packet = io.BytesIO()

        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 12)
        can.drawString(185, 600, f"{row}")
        can.save()

        packet.seek(0)
        new_pdf = PdfFileReader(packet)

        existing_pdf = PdfFileReader(open("pdfs/template.pdf", "rb"))
        output = PdfFileWriter()

        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

        outputStream = open(f"pdfs/generated/{row}.pdf", "wb")
        output.write(outputStream)
        outputStream.close()

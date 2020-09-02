from app import models
from django.conf import settings
import os
import zipfile
from os.path import basename
import urllib

class ZipMaker:
    def makeZip(self, zipFilename, filename, items):
        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + zipFilename
        pdfPath = BASE + settings.EXPORTS_URL + filename + '.pdf'

        if not items:
            return False

        zipf = zipfile.ZipFile(f"{path}.zip", 'w', zipfile.ZIP_DEFLATED)

        for item in items:
            # open attachment in AWS S3 server
            page = urllib.request.urlopen(item.bijlage.url)  # Change to website
            # put in this map of the zip with this name
            attachname = f"BasisBijlagen/{item.bijlage}"
            zipf.writestr(attachname, page.read())

        # write the pdf in the root of zip

        zipf.write(pdfPath, f"ProgrammaVanEisen.pdf")
        zipf.close()
        return True
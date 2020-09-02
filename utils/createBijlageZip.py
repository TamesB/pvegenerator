from app import models
from django.conf import settings
import os
import zipfile
from os.path import basename
import urllib

class ZipMaker:
    def makeZip(self, filename, items):
        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + filename

        if not items:
            return False

        zipf = zipfile.ZipFile(f"{path}.zip", 'w', zipfile.ZIP_DEFLATED)

        for item in items:
            page = urllib.request.urlopen(item.bijlage.url)  # Change to website
            attachname = f"bijlagen/{item.bijlage}"
            zipf.writestr(attachname, page.read())

        zipf.close()
        return True
from app import models
from django.conf import settings
import os
import zipfile
from os.path import basename

class ZipMaker:
    def makeZip(self, filename, bijlagen):
        BASE = os.path.dirname(os.path.abspath(__file__))
        path = BASE + settings.EXPORTS_URL + filename

        if not bijlagen:
            return False

        zipf = zipfile.ZipFile(f"{path}.zip", 'w', zipfile.ZIP_DEFLATED)

        for bijlage in bijlagen:
            filepath = f"{settings.MEDIA_ROOT + '/' + bijlage}"
            zipf.write(filepath, basename(filepath))

        zipf.close()
        return True
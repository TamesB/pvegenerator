import datetime
import hashlib
import os
from functools import partial


def _update_filename(instance, filename, path):
    path = path

    date = datetime.datetime.now()
    filename = f"{filename}-%s%s%s%s%s%s" % (
        date.strftime("%H"),
        date.strftime("%M"),
        date.strftime("%S"),
        date.strftime("%d"),
        date.strftime("%m"),
    )
    return os.path.join(path, filename)


def upload_to(path):
    return partial(_update_filename, path=path)

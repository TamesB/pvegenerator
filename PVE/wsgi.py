# Author: Tames Boon

"""
WSGI config for PVE project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PVE.settings")

# set below max connections (20 for heroku)
os.environ["ASGI_THREADS"] = "16"

application = get_wsgi_application()

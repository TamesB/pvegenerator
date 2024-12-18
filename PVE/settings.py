# Author: Tames Boon

import os
import platform

import django
import django_heroku
import environ
from django.utils.log import DEFAULT_LOGGING
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


root = environ.Path(__file__)
env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env.str("SECRET_KEY")

# OSGEO stuff
if os.name == "nt":
    OSGEO4W = r"C:\OSGeo4W"
    if "64" in platform.architecture()[0]:
        OSGEO4W += "64"
        pass
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ["OSGEO4W_ROOT"] = OSGEO4W
    os.environ["GDAL_DATA"] = OSGEO4W + r"\share\gdal"
    os.environ["PROJ_LIB"] = OSGEO4W + r"\share\proj"
    os.environ["PATH"] = OSGEO4W + r"\bin;" + os.environ["PATH"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    os.environ["HOST1"],
    os.environ["HOST2"],
]

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

DEFAULT_LOGGING["handlers"]["console"]["filters"] = []

# debug toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

# register pdf fonts
pdfmetrics.registerFont(TTFont("Calibri", os.path.join(BASE_DIR, "utils/calibri.ttf")))
pdfmetrics.registerFont(
    TTFont("Calibri-Bold", os.path.join(BASE_DIR, "utils/calibrib.ttf"))
)

# Application definition
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "leaflet",
    "django.contrib.gis",
    "app",
    "generator",
    "project",
    "users",
    "pvetool",
    "semanticuiforms",
    "storages",
    "simple_history",
    #"debug_toolbar",
    #"template_profiler_panel",
    'django_feather',
]

#
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "PVE.middleware.last_visit.last_visit_middleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    #"debug_toolbar.middleware.DebugToolbarMiddleware",
    #'csp.middleware.CSPMiddleware',
    "htmlmin.middleware.HtmlMinifyMiddleware",
    "htmlmin.middleware.MarkRequestMiddleware",
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

HTML_MINIFY = True

ROOT_URLCONF = "PVE.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
            "libraries": {"custom_tags": "pvetool.template_tags.custom_tags"},
        },
    },
]

WSGI_APPLICATION = "PVE.wsgi.application"

TEMPLATE_LOADERS = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# For Heroku hosting, switch 'default' and 'extra' to switch database options.
DATABASES = {
    # environment variable database (Database URI's)
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        'NAME': os.environ["NAME"],
        'USER': os.environ["USER"],
        'PASSWORD': os.environ["PASSWORD"],
        'HOST': os.environ["HOST"],
        'PORT':  os.environ["PORT"],
        'TEST': {
            'NAME': 'test',
        },
    },

}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "nl"

TIME_ZONE = "CET"

USE_I18N = True

USE_TZ = True

# Custom user stuff
AUTH_USER_MODEL = "users.CustomUser"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATIC_HOST = env.str("DJANGO_STATIC_HOST", "")
STATIC_URL = STATIC_HOST + "/static/"

STATICFILES_DIRS = (os.path.join("static"),)


STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

GEOS_LIBRARY_PATH = '/app/.heroku/vendor/lib/libgeos_c.so' if os.environ.get('ENV') == 'HEROKU' else os.getenv('GEOS_LIBRARY_PATH')
GDAL_LIBRARY_PATH = '/app/.heroku/vendor/lib/libgdal.so' if os.environ.get('ENV') == 'HEROKU' else os.getenv('GDAL_LIBRARY_PATH')

# django admin site
ADMIN_ENABLED = True

# making exports
EXPORTS_URL = "/PVEexports/"
EXPORTS_ROOT = os.path.join(BASE_DIR, "utils/PVEexports")

# @login_required url redirect
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/home"

SECURE_BROWSER_XSS_FILTER = True
## X-Frame-Options
X_FRAME_OPTIONS = "DENY"
# X-Content-Type-Options
SECURE_CONTENT_TYPE_NOSNIFF = True

# bulkform
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

ANNOTATION_ATTACHMENT_DIR = "OpmerkingBijlages/"

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
# s3 static settings
AWS_STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_REGION_NAME = "eu-central-1"  # change to your region
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DOWNLOAD_EXPIRE = 5000
# Email setup
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")
SERVER_EMAIL = os.getenv("EMAIL_HOST_USER")

CSRF_TRUSTED_ORIGINS = [os.environ["CSRF_TRUSTED_ORIGIN1"], os.environ["CSRF_TRUSTED_ORIGIN2"], os.environ["CSRF_TRUSTED_ORIGIN3"], 'https://*.127.0.0.1']

django.setup()

# Heroku settings
django_heroku.settings(locals(), staticfiles=False)
DATABASES["default"]["CONN_MAX_AGE"] = 0

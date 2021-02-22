# Author: Tames Boon

import os
import environ
import django_heroku
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import platform
import dj_database_url

root = environ.Path(__file__)
env = environ.Env()
environ.Env.read_env()

# OSGEO stuff
if os.name == 'nt':
    OSGEO4W = r"C:\OSGeo4W"
    if '64' in platform.architecture()[0]:
        OSGEO4W += "64"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = ["*"]

# debug toolbar
INTERNAL_IPS = [
    #'127.0.0.1',
]

# register pdf fonts
pdfmetrics.registerFont(TTFont('Calibri', os.path.join(BASE_DIR, 'utils/calibri.ttf')))
pdfmetrics.registerFont(TTFont('Calibri-Bold', os.path.join(BASE_DIR, 'utils/calibrib.ttf')))

# Application definition
INSTALLED_APPS = [
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'leaflet',
    'django.contrib.gis',
    'app',
    'generator',
    'project',
    'users',
    'syntrus',
    'semanticuiforms',
    'storages',
    'simple_history',
    'debug_toolbar',
    'cached_modelforms',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'PVE.middleware.last_visit.last_visit_middleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    #'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'PVE.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
            'libraries': {
                'custom_tags':'syntrus.template_tags.custom_tags'
            }
        },
    },
]

TEMPLATE_LOADERS = ['django.template.loaders.filesystem.Loader',
'django.template.loaders.app_directories.Loader'
]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# For Heroku hosting, switch 'default' and 'extra' to switch database options.
DATABASES = {
    # Extra local database
    #'default': {
    #    'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #},
    
    # environment variable database (Database URI's)
    'default': {
        'NAME': env.db,
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Custom user stuff
AUTH_USER_MODEL = 'users.CustomUser'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATIC_URL = '/static/'

STATICFILES_DIRS = ( os.path.join('static'), )

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH')

# django admin site
ADMIN_ENABLED = True

# making exports
EXPORTS_URL = '/PVEexports/'
EXPORTS_ROOT = os.path.join(BASE_DIR, 'utils/PVEexports')

# @login_required url redirect
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/home"

# Use in the pvegenerator.net production
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#SECURE_BROWSER_XSS_FILTER = True
## X-Frame-Options
#X_FRAME_OPTIONS = 'DENY'
#X-Content-Type-Options
#SECURE_CONTENT_TYPE_NOSNIFF = True

############## All True in Deployment
## that requests over HTTP are redirected to HTTPS. aslo can config in webserver
#SECURE_SSL_REDIRECT = True 
## Strict-Transport-Security
#SECURE_HSTS_SECONDS = 63072000
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#SECURE_HSTS_PRELOAD = True
##############

# for more security
#CSRF_COOKIE_SECURE = True
#CSRF_USE_SESSIONS = True
#CSRF_COOKIE_HTTPONLY = True
#SESSION_COOKIE_SECURE = True
#SESSION_COOKIE_SAMESITE = 'Strict'

#CSP_DEFAULT_SRC = ("'none'",)
#CSP_STYLE_SRC = ("'self'", 'ajax.googleapis.com', 'fonts.googleapis.com', 'sha256-Y7kgPWQdS/jgNu5itxfRoU6O5xEw/w7EBBi5d7MG+28=', 'sha256-biLFinpqYMtWHmXfkA1BPeCY0/fNt46SAZ+BBk5YUog=')
#CSP_SCRIPT_SRC = ("'self'", 'ajax.googleapis.com', 'sha256-85/9BrizOkSpDOJIc1bvbYi66vI0uMNcuSZ0Fb7E2Ms=')
#CSP_FONT_SRC = ("'self'", 'ajax.googleapis.com', 'fonts.gstatic.com', 'fonts.googleapis.com')
#CSP_IMG_SRC = ("'self'",)

#bulkform
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

ANNOTATION_ATTACHMENT_DIR = 'OpmerkingBijlages/'

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
# s3 static settings
AWS_STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_REGION_NAME = 'eu-central-1' #change to your region
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_DOWNLOAD_EXPIRE = 5000
# Email setup
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL")
EMAIL_HOST_USER =  os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")
SERVER_EMAIL = os.getenv("EMAIL_HOST_USER")

# Heroku settings
django_heroku.settings(locals())
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


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = ["*"]

# register pdf fonts
pdfmetrics.registerFont(TTFont('Calibri', os.path.join(BASE_DIR, 'utils/calibri.ttf')))
pdfmetrics.registerFont(TTFont('Calibri-Bold', os.path.join(BASE_DIR, 'utils/calibrib.ttf')))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'app',
    'generator',
    'project',
    'users',
    'semanticuiforms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
        },
    },
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

TIME_ZONE = 'UTC'

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

# Uploading attachment
MEDIA_URL = '/files/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'files')

# making exports
EXPORTS_URL = '/PVEexports/'
EXPORTS_ROOT = os.path.join(BASE_DIR, 'utils/PVEexports')

# @login_required url   redirect
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/home"

# Security
#CSRF_COOKIE_SECURE = True
#CSRF_USE_SESSIONS = True

#SECURE_BROWSER_XSS_FILTER = True

#SESSION_COOKIE_SECURE = True

#SECURE_HSTS_PRELOAD = True
#SECURE_HSTS_SECONDS = 20
#SECURE_REFERRER_POLICY = 'same-origin'

# Use ONLY for proxy
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Heroku settings
django_heroku.settings(locals())
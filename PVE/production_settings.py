import os
import environ

root = environ.Path(__file__)
env = environ.Env()
environ.Env.read_env()

## that requests over HTTP are redirected to HTTPS. also can config this in webserver
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
## Strict-Transport-Security
SECURE_HSTS_SECONDS = 63072000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
##############

# for more security
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Strict"

# CSP_DEFAULT_SRC = ("'none'",)
# CSP_STYLE_SRC = ("'self'", 'ajax.googleapis.com', 'fonts.googleapis.com', 'sha256-Y7kgPWQdS/jgNu5itxfRoU6O5xEw/w7EBBi5d7MG+28=', 'sha256-biLFinpqYMtWHmXfkA1BPeCY0/fNt46SAZ+BBk5YUog=')
# CSP_SCRIPT_SRC = ("'self'", 'ajax.googleapis.com', 'sha256-85/9BrizOkSpDOJIc1bvbYi66vI0uMNcuSZ0Fb7E2Ms=')
# CSP_FONT_SRC = ("'self'", 'ajax.googleapis.com', 'fonts.gstatic.com', 'fonts.googleapis.com')
# CSP_IMG_SRC = ("'self'",)

ALLOWED_HOSTS = [os.environ["HOST1"]]

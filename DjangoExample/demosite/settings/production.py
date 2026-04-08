import os
from .base import *

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-set-SECRET_KEY-env-var')
DEBUG = False
ALLOWED_HOSTS = ['*']

# Railway terminates SSL at its reverse proxy and forwards X-Forwarded-Proto.
# Without this Django treats every request as HTTP and CSRF checks fail.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF trusted origins — required for POST requests served over HTTPS.
# Priority:
#   1. CSRF_TRUSTED_ORIGINS env var (space-separated list, e.g. "https://myapp.up.railway.app")
#   2. RAILWAY_PUBLIC_DOMAIN auto-set by Railway (e.g. myapp.up.railway.app)
#   3. Empty list (CSRF will block all POST — set one of the above)
_trusted_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if _trusted_raw:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _trusted_raw.split() if o.strip()]
elif os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
    CSRF_TRUSTED_ORIGINS = [f"https://{os.environ['RAILWAY_PUBLIC_DOMAIN']}"]
else:
    CSRF_TRUSTED_ORIGINS = []

# Whitenoise serves static files without a CDN
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

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# DeviceBroker management socket (internal, always localhost)
DEVICEBROKER_ADDRESS = os.environ.get('DEVICEBROKER_ADDRESS', '127.0.0.1:8002')

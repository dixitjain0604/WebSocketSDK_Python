import os
from .base import *

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-set-SECRET_KEY-env-var')
DEBUG = False
ALLOWED_HOSTS = ['*']

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

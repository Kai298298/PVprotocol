"""
Django settings for pv_protocol project.

Diese Datei enthält alle sicherheitsrelevanten Einstellungen und Hinweise für eine produktionsreife Django-App.
Bitte lies die Kommentare aufmerksam und passe die Einstellungen für den Produktivbetrieb an!
"""
from pathlib import Path
from decouple import config
import os
# Sentry Error-Tracking (optional - DSN in .env/config!)
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    SENTRY_DSN = config('SENTRY_DSN', default=None, cast=str)
    # Fange True/False/None explizit ab
    if SENTRY_DSN and SENTRY_DSN not in ['None', 'True', 'False', True, False]:
        sentry_sdk.init(
            dsn=str(SENTRY_DSN),
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=True
        )
except (ImportError, ModuleNotFoundError):
    # Sentry nicht verfügbar - optional
    pass

# Prometheus Monitoring (Hinweis):
# Für Prometheus empfiehlt sich das Paket django-prometheus.
# Installation: pip install django-prometheus
# Dann in INSTALLED_APPS und MIDDLEWARE eintragen und /metrics-Endpoint bereitstellen.

# Basisverzeichnis
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SICHERHEITSEINSTELLUNGEN ---
# Niemals DEBUG=True in Produktion!
DEBUG = True  # Für lokale Entwicklung

# Niemals den SECRET_KEY im Code speichern!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# ALLOWED_HOSTS muss in Produktion gesetzt werden (z.B. ['deine-domain.de'])
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.65.56']

# CSRF & Session Sicherheit (für Entwicklung alles auf False)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_SSL_REDIRECT = False
X_FRAME_OPTIONS = 'DENY'

# Logging für sicherheitsrelevante Ereignisse
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django-security.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# --- ENDE SICHERHEITSEINSTELLUNGEN ---

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.gis',  # Nur aktivieren, wenn GDAL installiert ist
    # Third party apps
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_prometheus',
    # 'leaflet',  # Deaktiviert, da GIS nicht verfügbar
    # Lokale Apps
    'accounts',
    'installations',
    'protocols',
    'payments',
    'learning_center',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Prometheus DB-Engine (optional, für volle Metriken):
# DATABASES['default']['ENGINE'] = 'django_prometheus.db.backends.sqlite3'

# /metrics-Endpoint: In urls.py einbinden (siehe README)

ROOT_URLCONF = 'pv_protocol.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pv_protocol.wsgi.application'

# --- DATENBANK ---
# Standard: SQLite für Entwicklung, Postgres für Produktion empfohlen
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Für Produktion (Postgres, Beispiel):
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }

# --- PASSWORTVALIDIERUNG ---
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},  # Mindestlänge 12 Zeichen
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# --- INTERNATIONALISIERUNG ---
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# --- STATIC & MEDIA ---
STATIC_URL = str(config('STATIC_URL', default='/static/', cast=str))
STATIC_ROOT = BASE_DIR / str(config('STATIC_ROOT', default='staticfiles', cast=str))
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = str(config('MEDIA_URL', default='/media/', cast=str))
MEDIA_ROOT = BASE_DIR / str(config('MEDIA_ROOT', default='media', cast=str))

# WhiteNoise für statische Dateien in Produktion
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- FILE UPLOADS ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB

# --- LOGIN/LOGOUT ---
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = "/installations/"
LOGOUT_REDIRECT_URL = '/'

# --- BENUTZERMODELL ---
AUTH_USER_MODEL = 'accounts.User'

# --- REST FRAMEWORK ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# --- CRISPY FORMS ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- LEAFLET ---
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (51.3397, 12.3731),  # Leipzig
    'DEFAULT_ZOOM': 10,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'SCALE': 'metric',
    'ATTRIBUTION_PREFIX': 'PV Protocol System',
}

# --- DEFAULT PRIMARY KEY ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# === E-Mail-Benachrichtigungen (Dummy-Konfiguration, bitte Zugangsdaten später eintragen) ===
# Django sendet E-Mails über SMTP. Für Entwicklung/Tests kann man auch das Console-Backend nutzen.
# Für Produktivbetrieb: Zugangsdaten (USER, PASSWORD) und Absender anpassen!

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'  # z.B. Gmail, Posteo, Firmenserver
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'dein-benutzername@gmail.com'
# EMAIL_HOST_PASSWORD = 'dein-passwort'
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = 'PV-Protokoll <noreply@deine-domain.de>'

# Für Entwicklung: E-Mails werden in der Konsole ausgegeben
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@pv-protokoll.de'

# E-Mail-Einstellungen für Einladungen
INVITATION_EXPIRY_DAYS = 7  # Tage bis Einladung abläuft

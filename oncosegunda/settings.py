# oncosegunda/settings.py
import os
from pathlib import Path
from datetime import timedelta

# Cargar variables de entorno desde un archivo .env si existe (opcional)
try:
    # python-dotenv es opcional: si no está instalado, no fallamos
    from dotenv import load_dotenv
    load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, '.env'))
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-secret-key-aqui'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

import sys

# Agregar la carpeta 'apps' al path de Python
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps personalizadas - Autenticación y Gestión de Casos
    'authentication.apps.AuthConfig',
    'cases.apps.CasesConfig',
    'documents.apps.DocumentsConfig',
    'notifications.apps.NotificationsConfig',
    
    # Terceros
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    'guardian',
    'auditlog',
]

# Configuración de modelo de usuario personalizado
AUTH_USER_MODEL = 'authentication.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'oncosegunda.urls'

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

WSGI_APPLICATION = 'oncosegunda.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Django-guardian (object permissions)
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Required by django-guardian
ANONYMOUS_USER_ID = -1

# django-auditlog configuration
# Explicit model for auditlog entries (default model provided by package)
AUDITLOG_LOGENTRY_MODEL = 'auditlog.LogEntry'

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuración de Email
if DEBUG:
    # En desarrollo, mostrar los emails en la consola
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    # Desarrollo: ejecutar tareas Celery de forma síncrona (no requiere broker)
    # Útil para probar sin Redis/Docker en entorno local.
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = True
    # Broker por defecto en desarrollo si se necesita: memoria (solo funciona en proceso)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'memory://')
else:
    # En producción, usar SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@secondopinionmedica.com')

# Allow overriding email backend via environment variable (useful to test SMTP in DEBUG)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', globals().get('EMAIL_BACKEND'))

# If an SMTP backend is requested via env, ensure SMTP settings are loaded from env
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', globals().get('DEFAULT_FROM_EMAIL', 'noreply@secondopinionmedica.com'))

# Public site root used to build absolute URLs in emails (include scheme)
# Can be overridden with the SITE_ROOT or SITE_URL environment variable.
SITE_ROOT = os.getenv('SITE_ROOT', os.getenv('SITE_URL', 'http://127.0.0.1:8000'))

# Celery (colas) - valores por defecto; en producción usar REDIS o broker externo
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Logging: controlar la verbosidad desde la variable de entorno LOG_LEVEL (e.g. DEBUG, INFO)
import logging

LOG_LEVEL_NAME = os.getenv('LOG_LEVEL', 'INFO')
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME.upper(), logging.INFO)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL_NAME,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL_NAME,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL_NAME,
            'propagate': False,
        },
    },
}


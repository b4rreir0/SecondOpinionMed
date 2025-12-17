# oncosegunda/settings_prod.py
"""
Configuración de producción para el sistema de segunda opinión oncológica.
Esta configuración está optimizada para entornos de producción con mayor seguridad y rendimiento.
"""

import os
from pathlib import Path
from .settings import *

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================

DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError('La variable de entorno DJANGO_SECRET_KEY no está configurada')

# Hosts permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Configuración HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# =============================================================================
# BASE DE DATOS - PRODUCCIÓN
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'oncosegunda_prod'),
        'USER': os.environ.get('DB_USER', 'oncosegunda_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,  # Mantener conexiones abiertas por 10 minutos
    }
}

# =============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA - PRODUCCIÓN
# =============================================================================

# Configuración para servir archivos estáticos con WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de AWS S3 para archivos media (opcional)
USE_S3 = os.environ.get('USE_S3', 'False').lower() == 'true'

if USE_S3:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    # Configuración de archivos media en S3
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# =============================================================================
# EMAIL - PRODUCCIÓN
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@oncosegunda.com')

# =============================================================================
# LOGGING - PRODUCCIÓN
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/oncosegunda/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# CACHE - PRODUCCIÓN
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Cache de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# =============================================================================
# CONFIGURACIONES ADICIONALES DE PRODUCCIÓN
# =============================================================================

# Configuración de compresión
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Configuración de CSRF
CSRF_TRUSTED_ORIGINS = [
    f"https://{host.strip()}" for host in ALLOWED_HOSTS if host.strip()
]

# Configuración de rate limiting (requiere django-ratelimit)
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Configuración de monitoreo (requiere django-health-check)
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # porcentaje
    'MEMORY_MIN': 100,    # MB
}

# =============================================================================
# CONFIGURACIONES DE SEGURIDAD ADICIONALES
# =============================================================================

# Deshabilitar el modo DEBUG en producción
if DEBUG:
    raise ValueError('DEBUG no puede estar habilitado en producción')

# Verificar que las variables críticas estén configuradas
required_env_vars = [
    'DJANGO_SECRET_KEY',
    'DB_PASSWORD',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
]

for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f'La variable de entorno {var} es requerida en producción')
"""
WSGI config for oncosegunda project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Usar configuración de producción por defecto, puede ser sobreescrita por variables de entorno
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oncosegunda.settings_prod")

application = get_wsgi_application()

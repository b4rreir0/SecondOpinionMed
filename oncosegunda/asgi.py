"""
ASGI config for oncosegunda project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Usar configuración de producción por defecto, puede ser sobreescrita por variables de entorno
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oncosegunda.settings_prod")

application = get_asgi_application()

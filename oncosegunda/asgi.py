"""
ASGI config for oncosegunda project.

It exposes the ASGI callable as a module-level variable named ``application``.

Para más información sobre este archivo, ver:
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Usar configuración de producción por defecto
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oncosegunda.settings_prod")

# Importar routing de canales después de configurar Django
django_asgi_app = get_asgi_application()

# Importar las rutas de WebSocket
from apps.cases import routing as cases_routing

application = ProtocolTypeRouter({
    # HTTP -> Django
    "http": django_asgi_app,
    
    # WebSockets -> Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            cases_routing.websocket_urlpatterns
        )
    ),
})

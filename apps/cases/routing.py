"""
Routing de WebSockets para Django Channels.

Define los patrones de URL para las conexiones WebSocket.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat MDT por grupo
    re_path(
        r'ws/mdt/(?P<grupo_id>\w+)/$',
        consumers.MDTChatConsumer.as_asgi(),
        name='mdt_grupo_chat'
    ),
    
    # Chat MDT por caso específico
    re_path(
        r'ws/mdt/(?P<grupo_id>\w+)/caso/(?P<caso_id>[^/]+)/$',
        consumers.MDTChatConsumer.as_asgi(),
        name='mdt_caso_chat'
    ),
    
    # Presencia de usuario
    re_path(
        r'ws/presence/(?P<user_id>\w+)/$',
        consumers.PresenceConsumer.as_asgi(),
        name='presence'
    ),
    
    # Notificaciones personales
    re_path(
        r'ws/notifications/(?P<user_id>\w+)/$',
        consumers.NotificationConsumer.as_asgi(),
        name='notifications'
    ),
]

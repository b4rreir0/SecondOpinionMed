"""
Consumers de Django Channels para tiempo real.

Contiene:
- ChatConsumer: Mensajería MDT en tiempo real
- PresenceConsumer: Control de presencia en tiempo real
- NotificationConsumer: Notificaciones push
"""

import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class MDTChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer para el chat en tiempo real del comité MDT.
    
    Canales:
    - /mdt/{grupo_id}/ - Sala de un grupo médico específico
    - /mdt/{grupo_id}/caso/{caso_id}/ - Chat de un caso específico
    """
    
    async def connect(self):
        self.grupo_id = self.scope['url_route']['kwargs'].get('grupo_id')
        self.caso_id = self.scope['url_route']['kwargs'].get('caso_id')
        
        # Construir nombre de grupo de canales
        if self.caso_id:
            self.channel_group = f'mdt_caso_{self.caso_id}'
        else:
            self.channel_group = f'mdt_grupo_{self.grupo_id}'
        
        # Unirse al grupo de canales
        await self.channel_layer.group_add(
            self.channel_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Notificar conexión
        await self.channel_layer.group_send(
            self.channel_group,
            {
                'type': 'system_message',
                'message': 'Usuario conectado al chat MDT',
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def disconnect(self, close_code):
        # Salir del grupo de canales
        if hasattr(self, 'channel_group'):
            await self.channel_layer.group_discard(
                self.channel_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recibe mensaje del WebSocket y lo distribuye al grupo"""
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            # Guardar mensaje en BD
            mensaje_data = await self.guardar_mensaje(data)
            
            # Distribuir a todos en el grupo
            await self.channel_layer.group_send(
                self.channel_group,
                {
                    'type': 'chat_message',
                    'message': data.get('message', ''),
                    'autor': data.get('autor', 'Anonymous'),
                    'autor_id': data.get('autor_id'),
                    'timestamp': timezone.now().isoformat(),
                    'message_id': mensaje_data.get('id') if mensaje_data else None
                }
            )
        
        elif message_type == 'typing':
            # Notificar que alguien está escribiendo
            await self.channel_layer.group_send(
                self.channel_group,
                {
                    'type': 'typing_indicator',
                    'autor': data.get('autor', 'Anonymous'),
                    'is_typing': data.get('is_typing', True)
                }
            )
        
        elif message_type == 'read_receipt':
            # Marcar mensajes como leídos
            await self.channel_layer.group_send(
                self.channel_group,
                {
                    'type': 'read_receipt',
                    'lector': data.get('autor', 'Anonymous'),
                    'message_ids': data.get('message_ids', [])
                }
            )
    
    @database_sync_to_async
    def guardar_mensaje(self, data):
        """Guarda el mensaje en la base de datos"""
        try:
            from cases.mdt_models import MDTMessage
            from cases.models import Case
            from medicos.models import Medico, MedicalGroup
            
            caso = Case.objects.get(case_id=self.caso_id) if self.caso_id else None
            grupo = MedicalGroup.objects.get(id=self.grupo_id) if self.grupo_id else None
            autor = Medico.objects.get(id=data.get('autor_id')) if data.get('autor_id') else None
            
            mensaje = MDTMessage.objects.create(
                caso=caso,
                grupo=grupo,
                autor=autor,
                contenido=data.get('message', ''),
                tipo='mensaje'
            )
            
            return {'id': mensaje.id}
        except Exception as e:
            print(f"Error guardando mensaje: {e}")
            return None
    
    async def chat_message(self, event):
        """Envía mensaje al WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'autor': event['autor'],
            'timestamp': event['timestamp'],
            'message_id': event.get('message_id')
        }))
    
    async def typing_indicator(self, event):
        """Envía indicador de escritura"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'autor': event['autor'],
            'is_typing': event['is_typing']
        }))
    
    async def read_receipt(self, event):
        """Envía confirmación de lectura"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'lector': event['lector'],
            'message_ids': event['message_ids']
        }))
    
    async def system_message(self, event):
        """Envía mensaje del sistema"""
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': event['message'],
            'timestamp': event['timestamp']
        }))


class PresenceConsumer(AsyncWebsocketConsumer):
    """
    Consumer para gestionar presencia en tiempo real.
    
    Maneja:
    - Conexión/desconexión de usuarios
    - Heartbeats para mantener estado
 de estado (online,    - Cambio away, busy)
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.channel_group = f'presence_user_{self.user_id}'
        
        # Unirse al canal de presencia
        await self.channel_layer.group_add(
            self.channel_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Actualizar presencia en BD
        await self.actualizar_presence('online')
    
    async def disconnect(self, close_code):
        # Marcar como desconectado
        await self.actualizar_presence('offline')
        
        # Salir del canal
        await self.channel_layer.group_discard(
            self.channel_group,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'heartbeat':
            await self.actualizar_presence(data.get('status', 'online'))
        
        elif action == 'change_status':
            await self.actualizar_presence(data.get('status', 'online'))
            
            # Notificar a otros canales
            await self.channel_layer.group_send(
                f'presence_global',
                {
                    'type': 'presence_update',
                    'user_id': self.user_id,
                    'status': data.get('status')
                }
            )
    
    @database_sync_to_async
    def actualizar_presence(self, status):
        """Actualiza la presencia del usuario"""
        try:
            from cases.mdt_models import UserPresence
            from medicos.models import Medico
            
            medico = Medico.objects.get(id=self.user_id)
            UserPresence.objects.update_or_create(
                usuario=medico,
                defaults={'estado': status}
            )
        except Exception as e:
            print(f"Error actualizando presencia: {e}")
    
    async def presence_update(self, event):
        """Recibe actualización de presencia de otros"""
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'user_id': event['user_id'],
            'status': event['status']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer para notificaciones push en tiempo real.
    
    Canales:
    - /notifications/{user_id}/ - Notificaciones personales
    - /notifications/group/{group_id}/ - Notificaciones de grupo
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        
        if self.user_id:
            self.channel_group = f'notifications_{self.user_id}'
            await self.channel_layer.group_add(
                self.channel_group,
                self.channel_name
            )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'channel_group'):
            await self.channel_layer.group_discard(
                self.channel_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Procesa mensajes del cliente (ej: marcar como leída)"""
        data = json.loads(text_data)
        # Aquí se puede implementar lógica para marcar notificaciones como leídas
        pass
    
    async def notification(self, event):
        """Envía notificación al WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event.get('title', ''),
            'message': event.get('message', ''),
            'notification_type': event.get('notification_type', 'info'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))

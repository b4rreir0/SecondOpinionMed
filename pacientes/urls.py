from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', views.dashboard, name='dashboard'),

    # Perfil y cuenta
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('configuracion/', views.configuracion, name='configuracion'),

    # Solicitudes de segunda opinión
    path('solicitudes/', views.lista_solicitudes, name='lista_solicitudes'),
    path('solicitudes/nueva/', views.nueva_solicitud, name='nueva_solicitud'),

    # Flujo de nueva solicitud (paso a paso)
    path('solicitudes/nueva/paso1/', views.nueva_solicitud_paso1, name='nueva_solicitud_paso1'),
    path('solicitudes/nueva/paso2/<int:solicitud_id>/', views.nueva_solicitud_paso2, name='nueva_solicitud_paso2'),
    path('solicitudes/nueva/paso3/<int:solicitud_id>/', views.nueva_solicitud_paso3, name='nueva_solicitud_paso3'),
    path('solicitudes/nueva/completar/<int:solicitud_id>/', views.completar_solicitud, name='completar_solicitud'),

    # Detalle y gestión de solicitud
    path('solicitudes/<int:solicitud_id>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('solicitudes/<int:solicitud_id>/editar/', views.editar_solicitud, name='editar_solicitud'),
    path('solicitudes/<int:solicitud_id>/cancelar/', views.cancelar_solicitud, name='cancelar_solicitud'),
    path('solicitudes/<int:solicitud_id>/documentos/', views.agregar_documentos, name='agregar_documentos'),
    path('solicitudes/<int:solicitud_id>/documentos/<int:documento_id>/eliminar/', views.eliminar_documento, name='eliminar_documento'),

    # Seguimiento
    path('solicitudes/<int:solicitud_id>/seguimiento/', views.seguimiento, name='seguimiento'),
    path('solicitudes/<int:solicitud_id>/timeline/', views.timeline, name='timeline'),

    # Informes
    path('informes/', views.lista_informes, name='lista_informes'),
    path('informes/<int:informe_id>/', views.detalle_informe, name='detalle_informe'),
    path('informes/<int:informe_id>/descargar/', views.descargar_informe, name='descargar_informe'),
    path('informes/<int:informe_id>/compartir/', views.compartir_informe, name='compartir_informe'),

    # Comunicación
    path('mensajes/', views.lista_mensajes, name='lista_mensajes'),
    path('mensajes/nuevo/', views.nuevo_mensaje, name='nuevo_mensaje'),
    path('mensajes/<int:mensaje_id>/', views.detalle_mensaje, name='detalle_mensaje'),
    path('mensajes/<int:mensaje_id>/responder/', views.responder_mensaje, name='responder_mensaje'),

    # Notificaciones
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('notificaciones/<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]
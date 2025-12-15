# administracion/urls.py
from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),

    # Usuarios
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:user_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),

    # Médicos
    path('medicos/', views.gestion_medicos, name='gestion_medicos'),
    path('medicos/<int:medico_id>/', views.detalle_medico, name='detalle_medico'),

    # Configuración
    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),
    path('configuracion/<str:clave>/editar/', views.editar_configuracion, name='editar_configuracion'),

    # Auditoría
    path('auditoria/', views.ver_auditoria, name='ver_auditoria'),

    # Reportes
    path('reportes/', views.generar_reportes, name='generar_reportes'),

    # API endpoints
    path('api/estadisticas/', views.api_estadisticas, name='api_estadisticas'),
]
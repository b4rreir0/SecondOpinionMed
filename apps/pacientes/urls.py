# pacientes/urls.py
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # Dashboard del paciente
    path('dashboard/', views.dashboard_paciente, name='dashboard'),

    # Gestión de solicitudes
    path('solicitudes/', views.SolicitudListView.as_view(), name='solicitud_list'),
    path('solicitudes/crear/', views.SolicitudCreateView.as_view(), name='solicitud_create'),
    path('solicitudes/<int:pk>/', views.SolicitudDetailView.as_view(), name='solicitud_detail'),
    path('solicitudes/<int:pk>/editar/', views.SolicitudUpdateView.as_view(), name='solicitud_update'),
    path('solicitudes/<int:pk>/cancelar/', views.cancelar_solicitud, name='cancelar_solicitud'),

    # Gestión de documentos
    path('solicitudes/<int:pk>/documentos/', views.documentos_solicitud, name='documentos_solicitud'),
    path('solicitudes/<int:pk>/documentos/agregar/', views.agregar_documento, name='agregar_documento'),
    path('documentos/<int:pk>/eliminar/', views.eliminar_documento, name='eliminar_documento'),

    # Seguimiento de casos
    path('seguimiento/', views.seguimiento_casos, name='seguimiento'),

    # API endpoints
    path('api/solicitudes/estado/<str:codigo>/', views.estado_solicitud_api, name='estado_solicitud_api'),
]
# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # API endpoints para AJAX
    path('api/especialidades/', views.especialidades_api, name='especialidades_api'),
    path('api/instituciones/', views.instituciones_api, name='instituciones_api'),

    # Gestión de especialidades
    path('especialidades/', views.EspecialidadListView.as_view(), name='especialidad_list'),
    path('especialidades/crear/', views.EspecialidadCreateView.as_view(), name='especialidad_create'),
    path('especialidades/<int:pk>/', views.EspecialidadDetailView.as_view(), name='especialidad_detail'),
    path('especialidades/<int:pk>/editar/', views.EspecialidadUpdateView.as_view(), name='especialidad_update'),
    path('especialidades/<int:pk>/eliminar/', views.EspecialidadDeleteView.as_view(), name='especialidad_delete'),

    # Gestión de instituciones
    path('instituciones/', views.InstitucionListView.as_view(), name='institucion_list'),
    path('instituciones/crear/', views.InstitucionCreateView.as_view(), name='institucion_create'),
    path('instituciones/<int:pk>/', views.InstitucionDetailView.as_view(), name='institucion_detail'),
    path('instituciones/<int:pk>/editar/', views.InstitucionUpdateView.as_view(), name='institucion_update'),
    path('instituciones/<int:pk>/eliminar/', views.InstitucionDeleteView.as_view(), name='institucion_delete'),

    # Perfil de usuario
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/cambiar-password/', views.cambiar_password, name='cambiar_password'),
]
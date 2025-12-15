# medicos/urls.py
from django.urls import path
from . import views

app_name = 'medicos'

urlpatterns = [
    # Dashboard del médico
    path('dashboard/', views.dashboard_medico, name='dashboard'),

    # Gestión de casos asignados
    path('casos/', views.CasoListView.as_view(), name='caso_list'),
    path('casos/<int:pk>/', views.CasoDetailView.as_view(), name='caso_detail'),
    path('casos/<int:pk>/aceptar/', views.aceptar_caso, name='aceptar_caso'),
    path('casos/<int:pk>/rechazar/', views.rechazar_caso, name='rechazar_caso'),

    # Creación y gestión de informes
    path('casos/<int:pk>/informe/crear/', views.crear_informe, name='crear_informe'),
    path('casos/<int:pk>/informe/editar/', views.editar_informe, name='editar_informe'),
    path('casos/<int:pk>/informe/finalizar/', views.finalizar_informe, name='finalizar_informe'),

    # Comentarios en casos
    path('casos/<int:pk>/comentarios/', views.comentarios_caso, name='comentarios_caso'),
    path('casos/<int:pk>/comentarios/agregar/', views.agregar_comentario, name='agregar_comentario'),

    # Reportes y estadísticas
    path('reportes/', views.reportes_medico, name='reportes'),
    path('estadisticas/', views.estadisticas_medico, name='estadisticas'),

    # API endpoints
    path('api/casos/estadisticas/', views.casos_estadisticas_api, name='casos_estadisticas_api'),
]
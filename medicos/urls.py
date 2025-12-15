from django.urls import path
from . import views

app_name = 'medicos'

urlpatterns = [
    # Dashboard - EXCLUSIVAMENTE casos asignados
    path('dashboard/', views.dashboard, name='dashboard'),

    # Gestión de casos asignados
    path('casos/', views.mis_casos, name='mis_casos'),
    path('casos/filtrar/<str:filtro>/', views.casos_filtrados, name='casos_filtrados'),

    # Detalle y gestión de caso individual
    path('casos/<int:caso_id>/', views.detalle_caso, name='detalle_caso'),
    path('casos/<int:caso_id>/revisar/', views.revisar_documentacion, name='revisar_documentacion'),
    path('casos/<int:caso_id>/validar/', views.validar_documentacion, name='validar_documentacion'),
    path('casos/<int:caso_id>/solicitar-info/', views.solicitar_informacion, name='solicitar_informacion'),
    path('casos/<int:caso_id>/rechazar/', views.rechazar_caso, name='rechazar_caso'),

    # Envío a comité multidisciplinario
    path('casos/<int:caso_id>/enviar-comite/', views.enviar_a_comite, name='enviar_a_comite'),
    path('casos/<int:caso_id>/seleccionar-comite/', views.seleccionar_comite, name='seleccionar_comite'),

    # Contacto con paciente (solo durante fase MDT)
    path('casos/<int:caso_id>/contactar/', views.contactar_paciente, name='contactar_paciente'),
    path('casos/<int:caso_id>/registrar-llamada/', views.registrar_llamada, name='registrar_llamada'),
    path('casos/<int:caso_id>/enviar-mensaje/', views.enviar_mensaje_paciente, name='enviar_mensaje_paciente'),

    # Comités multidisciplinarios
    path('comites/', views.mis_comites, name='mis_comites'),
    path('comites/<int:comite_id>/', views.detalle_comite, name='detalle_comite'),
    path('comites/<int:comite_id>/unirse/', views.unirse_comite, name='unirse_comite'),

    # Análisis de caso en comité
    path('comites/<int:comite_id>/casos/<int:caso_id>/', views.analizar_caso_comite, name='analizar_caso_comite'),
    path('comites/<int:comite_id>/casos/<int:caso_id>/votar/', views.votar_tratamiento, name='votar_tratamiento'),
    path('comites/<int:comite_id>/casos/<int:caso_id>/comentar/', views.agregar_comentario, name='agregar_comentario'),
    path('comites/<int:comite_id>/casos/<int:caso_id>/consensuar/', views.definir_consenso, name='definir_consenso'),

    # Redacción de informes
    path('informes/pendientes/', views.informes_pendientes, name='informes_pendientes'),
    path('informes/nuevo/<int:caso_id>/', views.redactar_informe, name='redactar_informe'),
    path('informes/<int:informe_id>/editar/', views.editar_informe, name='editar_informe'),
    path('informes/<int:informe_id>/previsualizar/', views.previsualizar_informe, name='previsualizar_informe'),

    # Gestión de firmas
    path('informes/<int:informe_id>/firmar/', views.firmar_informe, name='firmar_informe'),
    path('informes/<int:informe_id>/solicitar-firmas/', views.solicitar_firmas, name='solicitar_firmas'),
    path('informes/<int:informe_id>/enviar/', views.enviar_informe_paciente, name='enviar_informe_paciente'),

    # Perfil y herramientas
    path('perfil/', views.perfil_medico, name='perfil_medico'),
    path('plantillas/', views.mis_plantillas, name='mis_plantillas'),
    path('plantillas/nueva/', views.nueva_plantilla, name='nueva_plantilla'),
    path('plantillas/<int:plantilla_id>/', views.editar_plantilla, name='editar_plantilla'),

    # Calendario y agenda
    path('calendario/', views.calendario, name='calendario'),
    path('calendario/comites/', views.calendario_comites, name='calendario_comites'),

    # Estadísticas personales
    path('estadisticas/', views.estadisticas_personales, name='estadisticas_personales'),
]
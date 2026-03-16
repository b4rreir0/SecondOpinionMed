from django.urls import path
from . import portal_views
from . import views

app_name = 'administracion'

urlpatterns = [
    # Dashboard principal
    path('', portal_views.AdminDashboardView.as_view(), name='portal_dashboard'),
    
    # Gestión de Casos
    path('casos/', portal_views.GestionCasosView.as_view(), name='portal_casos'),
    path('casos/<str:case_id>/', portal_views.CasoDetalleView.as_view(), name='portal_caso_detalle'),
    path('casos/<str:case_id>/asignar/', portal_views.AsignarCasoView.as_view(), name='portal_caso_asignar'),
    
    # Gestión de Médicos
    path('medicos/', portal_views.GestionMedicosView.as_view(), name='portal_medicos'),
    path('medicos/<int:medico_id>/', portal_views.MedicoDetalleView.as_view(), name='portal_medico_detalle'),
    
    # Gestión de Pacientes
    path('pacientes/', portal_views.GestionPacientesView.as_view(), name='portal_pacientes'),
    path('pacientes/<int:paciente_id>/', portal_views.PacienteDetalleView.as_view(), name='portal_paciente_detalle'),
    
    # Gestión de Comités MDT (Grupos Médicos)
    path('comites/', portal_views.GestionComitesView.as_view(), name='portal_comites'),
    
    # Gestión de Tipos de Cancer
    path('tipos-cancer/', portal_views.GestionTiposCancerView.as_view(), name='portal_tipos_cancer'),
    path('tipos-cancer/crear/', portal_views.TipoCancerCrearView.as_view(), name='portal_tipo_cancer_crear'),
    path('tipos-cancer/<int:tipo_id>/editar/', portal_views.TipoCancerEditarView.as_view(), name='portal_tipo_cancer_editar'),
    path('tipos-cancer/<int:tipo_id>/eliminar/', portal_views.TipoCancerEliminarView.as_view(), name='portal_tipo_cancer_eliminar'),
    
    # Gestión de Grupos Médicos
    path('grupos/', portal_views.GestionGruposView.as_view(), name='portal_grupos'),
    path('grupos/crear/', portal_views.GrupoCrearView.as_view(), name='portal_grupo_crear'),
    path('grupos/<int:grupo_id>/', portal_views.GrupoDetalleView.as_view(), name='portal_grupo_detalle'),
    path('grupos/<int:grupo_id>/editar/', portal_views.GrupoEditarView.as_view(), name='portal_grupo_editar'),
    path('grupos/<int:grupo_id>/eliminar/', portal_views.GrupoEliminarView.as_view(), name='portal_grupo_eliminar'),
    path('grupos/<int:grupo_id>/agregar-miembro/', portal_views.GrupoAgregarMiembroView.as_view(), name='portal_grupo_agregar_miembro'),
    path('grupos/<int:grupo_id>/eliminar-miembro/', portal_views.GrupoEliminarMiembroView.as_view(), name='portal_grupo_eliminar_miembro'),
    path('grupos/<int:grupo_id>/asignar-tipo/', portal_views.GrupoAsignarTipoCancerView.as_view(), name='portal_grupo_asignar_tipo'),
    path('grupos/<int:grupo_id>/quitar-tipo/', portal_views.GrupoQuitarTipoCancerView.as_view(), name='portal_grupo_quitar_tipo'),
    
    # Invitar doctores
    path('invite/', portal_views.InviteDoctorView.as_view(), name='portal_invite'),
    
    # Configuración
    path('configuracion/', portal_views.ConfiguracionView.as_view(), name='portal_configuracion'),
    
    # Panel de Gestión (desde views.py)
    path('gestion/', views.panel_gestion, name='panel_gestion'),
]

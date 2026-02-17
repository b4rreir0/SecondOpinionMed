from django.urls import path
from . import portal_views

app_name = 'administracion'

urlpatterns = [
    # Login/Logout
    path('login/', portal_views.AdminLoginView.as_view(), name='portal_login'),
    path('logout/', portal_views.AdminLogoutView.as_view(), name='portal_logout'),
    
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
    
    # Gestión de Comités MDT
    path('comites/', portal_views.GestionComitesView.as_view(), name='portal_comites'),
    
    # Invitar doctores
    path('invite/', portal_views.InviteDoctorView.as_view(), name='portal_invite'),
    
    # Configuración
    path('configuracion/', portal_views.ConfiguracionView.as_view(), name='portal_configuracion'),
]

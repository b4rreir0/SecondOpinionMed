from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    # Dashboard de control total
    path('dashboard/', views.dashboard, name='dashboard'),
    path('estado-sistema/', views.estado_sistema, name='estado_sistema'),

    # ==================== GESTIÓN DE USUARIOS (CRUD COMPLETO) ====================
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo/', views.nuevo_usuario, name='nuevo_usuario'),
    path('usuarios/<int:usuario_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/<int:usuario_id>/deshabilitar/', views.deshabilitar_usuario, name='deshabilitar_usuario'),
    path('usuarios/<int:usuario_id>/habilitar/', views.habilitar_usuario, name='habilitar_usuario'),
    path('usuarios/<int:usuario_id>/reset-password/', views.reset_password, name='reset_password'),

    # Permisos granulares
    path('usuarios/<int:usuario_id>/permisos/', views.gestionar_permisos, name='gestionar_permisos'),
    path('usuarios/<int:usuario_id>/permisos/agregar/', views.agregar_permiso, name='agregar_permiso'),
    path('usuarios/<int:usuario_id>/permisos/remover/<int:permiso_id>/', views.remover_permiso, name='remover_permiso'),

    # Simulación de acceso
    path('usuarios/<int:usuario_id>/simular/', views.simular_acceso, name='simular_acceso'),

    # Roles y grupos
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/nuevo/', views.nuevo_rol, name='nuevo_rol'),
    path('roles/<int:rol_id>/', views.detalle_rol, name='detalle_rol'),
    path('roles/<int:rol_id>/editar/', views.editar_rol, name='editar_rol'),
    path('roles/<int:rol_id>/eliminar/', views.eliminar_rol, name='eliminar_rol'),

    # ==================== GESTIÓN DE MÓDULOS (ACTIVAR/DESACTIVAR) ====================
    path('modulos/', views.lista_modulos, name='lista_modulos'),
    path('modulos/<str:modulo_nombre>/', views.detalle_modulo, name='detalle_modulo'),
    path('modulos/<str:modulo_nombre>/activar/', views.activar_modulo, name='activar_modulo'),
    path('modulos/<str:modulo_nombre>/desactivar/', views.desactivar_modulo, name='desactivar_modulo'),
    path('modulos/<str:modulo_nombre>/eliminar/', views.eliminar_modulo, name='eliminar_modulo'),
    path('modulos/<str:modulo_nombre>/configurar/', views.configurar_modulo, name='configurar_modulo'),

    # Crear nuevos módulos
    path('modulos/nuevo/', views.crear_modulo, name='crear_modulo'),
    path('modulos/nuevo/desde-plantilla/', views.crear_modulo_plantilla, name='crear_modulo_plantilla'),

    # Dependencias entre módulos
    path('modulos/<str:modulo_nombre>/dependencias/', views.gestionar_dependencias, name='gestionar_dependencias'),
    path('modulos/<str:modulo_nombre>/dependencias/agregar/', views.agregar_dependencia, name='agregar_dependencia'),

    # ==================== CONFIGURACIÓN DE ALGORITMOS ====================
    path('algoritmos/', views.lista_algoritmos, name='lista_algoritmos'),
    path('algoritmos/asignacion/', views.configurar_algoritmo_asignacion, name='configurar_algoritmo_asignacion'),
    path('algoritmos/asignacion/probar/', views.probar_algoritmo_asignacion, name='probar_algoritmo_asignacion'),
    path('algoritmos/asignacion/resetear/', views.resetear_algoritmo_asignacion, name='resetear_algoritmo_asignacion'),

    # Configuración de algoritmos específicos
    path('algoritmos/rotacion/', views.configurar_rotacion, name='configurar_rotacion'),
    path('algoritmos/prioridad/', views.configurar_prioridad, name='configurar_prioridad'),
    path('algoritmos/notificaciones/', views.configurar_notificaciones, name='configurar_notificaciones'),

    # ==================== GESTIÓN TOTAL DE CASOS ====================
    path('casos/', views.lista_casos_completa, name='lista_casos_completa'),
    path('casos/<int:caso_id>/', views.detalle_caso_admin, name='detalle_caso_admin'),
    path('casos/<int:caso_id>/reasignar/', views.reasignar_caso, name='reasignar_caso'),
    path('casos/<int:caso_id>/forzar-estado/', views.forzar_estado_caso, name='forzar_estado_caso'),
    path('casos/<int:caso_id>/eliminar/', views.eliminar_caso, name='eliminar_caso'),
    path('casos/<int:caso_id>/restaurar/', views.restaurar_caso, name='restaurar_caso'),

    # Acciones masivas
    path('casos/acciones-masivas/', views.acciones_masivas_casos, name='acciones_masivas_casos'),
    path('casos/reasignar-masivo/', views.reasignar_masivo, name='reasignar_masivo'),
    path('casos/cambiar-estado-masivo/', views.cambiar_estado_masivo, name='cambiar_estado_masivo'),

    # ==================== CONFIGURACIÓN DEL SISTEMA ====================
    path('configuracion/', views.configuracion_general, name='configuracion_general'),
    path('configuracion/general/', views.configuracion_general, name='configuracion_general'),
    path('configuracion/documentos/', views.configuracion_documentos, name='configuracion_documentos'),
    path('configuracion/notificaciones/', views.configuracion_notificaciones, name='configuracion_notificaciones'),
    path('configuracion/plantillas/', views.configuracion_plantillas, name='configuracion_plantillas'),
    path('configuracion/backup/', views.configuracion_backup, name='configuracion_backup'),
    path('configuracion/integraciones/', views.configuracion_integraciones, name='configuracion_integraciones'),

    # ==================== MONITORIZACIÓN Y AUDITORÍA ====================
    path('monitor/', views.monitor_tiempo_real, name='monitor_tiempo_real'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('auditoria/accesos/', views.auditoria_accesos, name='auditoria_accesos'),
    path('auditoria/acciones/', views.auditoria_acciones, name='auditoria_acciones'),
    path('auditoria/cambios/', views.auditoria_cambios, name='auditoria_cambios'),
    path('auditoria/exportar/', views.exportar_auditoria, name='exportar_auditoria'),

    # Logs del sistema
    path('logs/', views.logs_sistema, name='logs_sistema'),
    path('logs/servidor/', views.logs_servidor, name='logs_servidor'),
    path('logs/aplicacion/', views.logs_aplicacion, name='logs_aplicacion'),
    path('logs/base-datos/', views.logs_base_datos, name='logs_base_datos'),
    path('logs/<str:log_id>/', views.detalle_log, name='detalle_log'),

    # ==================== MANTENIMIENTO DEL SISTEMA ====================
    path('mantenimiento/', views.mantenimiento, name='mantenimiento'),
    path('mantenimiento/backup/', views.crear_backup, name='crear_backup'),
    path('mantenimiento/backup/restaurar/', views.restaurar_backup, name='restaurar_backup'),
    path('mantenimiento/optimizar/', views.optimizar_sistema, name='optimizar_sistema'),
    path('mantenimiento/limpiar/', views.limpiar_sistema, name='limpiar_sistema'),
    path('mantenimiento/pruebas/', views.ejecutar_pruebas, name='ejecutar_pruebas'),
    path('mantenimiento/actualizar/', views.actualizar_sistema, name='actualizar_sistema'),

    # Modo mantenimiento
    path('mantenimiento/modo/', views.activar_modo_mantenimiento, name='activar_modo_mantenimiento'),
    path('mantenimiento/modo/desactivar/', views.desactivar_modo_mantenimiento, name='desactivar_modo_mantenimiento'),

    # ==================== REPORTES Y ANALYTICS ====================
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/rendimiento/', views.reporte_rendimiento, name='reporte_rendimiento'),
    path('reportes/usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('reportes/casos/', views.reporte_casos, name='reporte_casos'),
    path('reportes/medicos/', views.reporte_medicos, name='reporte_medicos'),
    path('reportes/financieros/', views.reporte_financieros, name='reporte_financieros'),
    path('reportes/personalizados/', views.reportes_personalizados, name='reportes_personalizados'),
    path('reportes/exportar/<str:tipo>/', views.exportar_reporte, name='exportar_reporte'),

    # ==================== GESTIÓN DE COMITÉS ====================
    path('comites/', views.lista_comites_admin, name='lista_comites_admin'),
    path('comites/nuevo/', views.crear_comite, name='crear_comite'),
    path('comites/<int:comite_id>/', views.detalle_comite_admin, name='detalle_comite_admin'),
    path('comites/<int:comite_id>/editar/', views.editar_comite, name='editar_comite'),
    path('comites/<int:comite_id>/eliminar/', views.eliminar_comite, name='eliminar_comite'),

    # Miembros de comités
    path('comites/<int:comite_id>/miembros/', views.gestionar_miembros_comite, name='gestionar_miembros_comite'),
    path('comites/<int:comite_id>/miembros/agregar/', views.agregar_miembro_comite, name='agregar_miembro_comite'),
    path('comites/<int:comite_id>/miembros/<int:miembro_id>/remover/', views.remover_miembro_comite, name='remover_miembro_comite'),

    # ==================== EJECUCIÓN DE ACCIONES ====================
    path('acciones/ejecutar/', views.ejecutar_accion, name='ejecutar_accion'),
    path('acciones/programadas/', views.acciones_programadas, name='acciones_programadas'),
    path('acciones/programadas/nueva/', views.nueva_accion_programada, name='nueva_accion_programada'),
    path('acciones/programadas/<int:accion_id>/', views.detalle_accion_programada, name='detalle_accion_programada'),
    path('acciones/programadas/<int:accion_id>/ejecutar-ahora/', views.ejecutar_accion_ahora, name='ejecutar_accion_ahora'),

    # ==================== GESTIÓN DE RECURSOS ====================
    path('recursos/', views.gestion_recursos, name='gestion_recursos'),
    path('recursos/limitar/', views.limitar_recursos, name='limitar_recursos'),
    path('recursos/estado/', views.estado_recursos, name='estado_recursos'),
]
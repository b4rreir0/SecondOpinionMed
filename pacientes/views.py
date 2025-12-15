from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, 'pacientes/dashboard.html')

# Placeholder functions for all URL patterns
def perfil(request):
    return render(request, 'pacientes/perfil.html')

def editar_perfil(request):
    return render(request, 'pacientes/editar_perfil.html')

def configuracion(request):
    return render(request, 'pacientes/configuracion.html')

def lista_solicitudes(request):
    return render(request, 'pacientes/lista_solicitudes.html')

def nueva_solicitud(request):
    return render(request, 'pacientes/nueva_solicitud.html')

def nueva_solicitud_paso1(request):
    return render(request, 'pacientes/nueva_solicitud_paso1.html')

def nueva_solicitud_paso2(request, solicitud_id):
    return render(request, 'pacientes/nueva_solicitud_paso2.html')

def nueva_solicitud_paso3(request, solicitud_id):
    return render(request, 'pacientes/nueva_solicitud_paso3.html')

def completar_solicitud(request, solicitud_id):
    return render(request, 'pacientes/completar_solicitud.html')

def detalle_solicitud(request, solicitud_id):
    return render(request, 'pacientes/detalle_solicitud.html')

def editar_solicitud(request, solicitud_id):
    return render(request, 'pacientes/editar_solicitud.html')

def cancelar_solicitud(request, solicitud_id):
    return render(request, 'pacientes/cancelar_solicitud.html')

def agregar_documentos(request, solicitud_id):
    return render(request, 'pacientes/agregar_documentos.html')

def eliminar_documento(request, solicitud_id, documento_id):
    return render(request, 'pacientes/eliminar_documento.html')

def seguimiento(request, solicitud_id):
    return render(request, 'pacientes/seguimiento.html')

def timeline(request, solicitud_id):
    return render(request, 'pacientes/timeline.html')

def lista_informes(request):
    return render(request, 'pacientes/lista_informes.html')

def detalle_informe(request, informe_id):
    return render(request, 'pacientes/detalle_informe.html')

def descargar_informe(request, informe_id):
    return render(request, 'pacientes/descargar_informe.html')

def compartir_informe(request, informe_id):
    return render(request, 'pacientes/compartir_informe.html')

def lista_mensajes(request):
    return render(request, 'pacientes/lista_mensajes.html')

def nuevo_mensaje(request):
    return render(request, 'pacientes/nuevo_mensaje.html')

def detalle_mensaje(request, mensaje_id):
    return render(request, 'pacientes/detalle_mensaje.html')

def responder_mensaje(request, mensaje_id):
    return render(request, 'pacientes/responder_mensaje.html')

def notificaciones(request):
    return render(request, 'pacientes/notificaciones.html')

def marcar_notificacion_leida(request, notificacion_id):
    return render(request, 'pacientes/marcar_notificacion_leida.html')

def marcar_todas_leidas(request):
    return render(request, 'pacientes/marcar_todas_leidas.html')

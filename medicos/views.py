from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, 'medicos/dashboard.html')

# Placeholder functions for all URL patterns
def mis_casos(request):
    return render(request, 'medicos/mis_casos.html')

def casos_filtrados(request, filtro):
    return render(request, 'medicos/casos_filtrados.html')

def detalle_caso(request, caso_id):
    return render(request, 'medicos/detalle_caso.html')

def revisar_documentacion(request, caso_id):
    return render(request, 'medicos/revisar_documentacion.html')

def validar_documentacion(request, caso_id):
    return render(request, 'medicos/validar_documentacion.html')

def solicitar_informacion(request, caso_id):
    return render(request, 'medicos/solicitar_informacion.html')

def rechazar_caso(request, caso_id):
    return render(request, 'medicos/rechazar_caso.html')

def enviar_a_comite(request, caso_id):
    return render(request, 'medicos/enviar_a_comite.html')

def seleccionar_comite(request, caso_id):
    return render(request, 'medicos/seleccionar_comite.html')

def contactar_paciente(request, caso_id):
    return render(request, 'medicos/contactar_paciente.html')

def registrar_llamada(request, caso_id):
    return render(request, 'medicos/registrar_llamada.html')

def enviar_mensaje_paciente(request, caso_id):
    return render(request, 'medicos/enviar_mensaje_paciente.html')

def mis_comites(request):
    return render(request, 'medicos/mis_comites.html')

def detalle_comite(request, comite_id):
    return render(request, 'medicos/detalle_comite.html')

def unirse_comite(request, comite_id):
    return render(request, 'medicos/unirse_comite.html')

def analizar_caso_comite(request, comite_id, caso_id):
    return render(request, 'medicos/analizar_caso_comite.html')

def votar_tratamiento(request, comite_id, caso_id):
    return render(request, 'medicos/votar_tratamiento.html')

def agregar_comentario(request, comite_id, caso_id):
    return render(request, 'medicos/agregar_comentario.html')

def definir_consenso(request, comite_id, caso_id):
    return render(request, 'medicos/definir_consenso.html')

def informes_pendientes(request):
    return render(request, 'medicos/informes_pendientes.html')

def redactar_informe(request, caso_id):
    return render(request, 'medicos/redactar_informe.html')

def editar_informe(request, informe_id):
    return render(request, 'medicos/editar_informe.html')

def previsualizar_informe(request, informe_id):
    return render(request, 'medicos/previsualizar_informe.html')

def firmar_informe(request, informe_id):
    return render(request, 'medicos/firmar_informe.html')

def solicitar_firmas(request, informe_id):
    return render(request, 'medicos/solicitar_firmas.html')

def enviar_informe_paciente(request, informe_id):
    return render(request, 'medicos/enviar_informe_paciente.html')

def perfil_medico(request):
    return render(request, 'medicos/perfil_medico.html')

def mis_plantillas(request):
    return render(request, 'medicos/mis_plantillas.html')

def nueva_plantilla(request):
    return render(request, 'medicos/nueva_plantilla.html')

def editar_plantilla(request, plantilla_id):
    return render(request, 'medicos/editar_plantilla.html')

def calendario(request):
    return render(request, 'medicos/calendario.html')

def calendario_comites(request):
    return render(request, 'medicos/calendario_comites.html')

def estadisticas_personales(request):
    return render(request, 'medicos/estadisticas_personales.html')

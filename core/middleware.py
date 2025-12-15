from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class RoleRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si el usuario está autenticado
        if request.user.is_authenticated:
            # Redireccionar según el rol
            current_path = request.path

            # Si está en la raíz y ya está autenticado, redirigir según rol
            if current_path == '/':
                if request.user.groups.filter(name='Paciente').exists():
                    return redirect(reverse('pacientes:dashboard'))
                elif request.user.groups.filter(name='Medico').exists():
                    return redirect(reverse('medicos:dashboard'))
                elif request.user.groups.filter(name='Administrador').exists():
                    return redirect(reverse('administracion:dashboard'))

        response = self.get_response(request)
        return response

class ModuleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar acceso a módulos deshabilitados
        if request.user.is_authenticated:
            # Aquí iría la lógica para verificar si un módulo está activo
            # y si el usuario tiene permiso para acceder
            pass

        response = self.get_response(request)
        return response
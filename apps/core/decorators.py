# core/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth.decorators import login_required
from pacientes.models import Paciente
from medicos.models import Medico
from administracion.models import Administrador

def paciente_required(view_func):
    """Decorador que requiere que el usuario sea un paciente activo"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            paciente = request.user.paciente
            if paciente.activo:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Su cuenta de paciente está inactiva.')
                return redirect('public:login')
        except Paciente.DoesNotExist:
            messages.error(request, 'Acceso denegado. Se requiere cuenta de paciente.')
            return redirect('public:login')
    return _wrapped_view

def medico_required(view_func):
    """Decorador que requiere que el usuario sea un médico activo"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            medico = request.user.medico
            if medico.estado == 'activo':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Su cuenta de médico está inactiva.')
                return redirect('public:login')
        except Medico.DoesNotExist:
            messages.error(request, 'Acceso denegado. Se requiere cuenta de médico.')
            return redirect('public:login')
    return _wrapped_view

def admin_required(view_func):
    """Decorador que requiere que el usuario sea un administrador activo"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            admin = request.user.administrador
            if admin.estado == 'activo':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Su cuenta de administrador está inactiva.')
                return redirect('public:login')
        except Administrador.DoesNotExist:
            messages.error(request, 'Acceso denegado. Se requiere cuenta de administrador.')
            return redirect('public:login')
    return _wrapped_view

def role_required(*roles):
    """Decorador que requiere que el usuario tenga uno de los roles especificados"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Verificar roles
            has_role = False
            for role in roles:
                if role == 'paciente':
                    has_role = hasattr(user, 'paciente') and user.paciente.activo
                elif role == 'medico':
                    has_role = hasattr(user, 'medico') and user.medico.estado == 'activo'
                elif role == 'admin':
                    has_role = hasattr(user, 'administrador') and user.administrador.estado == 'activo'
                
                if has_role:
                    break
            
            if not has_role:
                messages.error(request, 'No tiene permisos para acceder a esta sección.')
                return redirect('public:login')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def module_access_required(module_name):
    """Decorador que verifica acceso a un módulo específico"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar si el módulo está activo
            from core.models import ModuloSistema
            try:
                modulo = ModuloSistema.objects.get(nombre=module_name)
                if not modulo.activa:
                    messages.error(request, f'El módulo {module_name} está temporalmente inactivo.')
                    return redirect('public:dashboard')
            except ModuloSistema.DoesNotExist:
                messages.error(request, f'Módulo {module_name} no encontrado.')
                return redirect('public:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def audit_action(action_type, model_name):
    """Decorador que registra acciones en el sistema de auditoría"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Ejecutar la vista
            response = view_func(request, *args, **kwargs)
            
            # Registrar en auditoría
            from core.services import AuditoriaService
            descripcion = f"Acción {action_type} en {model_name}"
            
            AuditoriaService.registrar_accion(
                usuario=request.user,
                tipo_accion=action_type,
                modelo_afectado=model_name,
                descripcion=descripcion,
                ip_address=get_client_ip(request)
            )
            
            return response
        return _wrapped_view
    return decorator

def get_client_ip(request):
    """Obtiene la IP del cliente desde la request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
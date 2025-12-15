from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from functools import wraps

def paciente_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.groups.filter(name='Paciente').exists():
            return redirect('unauthorized')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def medico_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.groups.filter(name='Medico').exists():
            return redirect('unauthorized')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.groups.filter(name='Administrador').exists():
            return redirect('unauthorized')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def module_active_required(module_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verificar si el módulo está activo
            # (esto requeriría un modelo de configuración)
            from administracion.models import ModuloConfig

            try:
                modulo = ModuloConfig.objects.get(nombre=module_name)
                if not modulo.activo:
                    return redirect('modulo_deshabilitado')
            except ModuloConfig.DoesNotExist:
                pass

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
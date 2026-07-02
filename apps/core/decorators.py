from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from administracion.models import Administrador


def admin_required(view_func):
    """Requiere administrador activo o superuser (portal /admin-portal/)."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if getattr(request.user, 'is_superuser', False):
            return view_func(request, *args, **kwargs)

        try:
            admin = request.user.administrador
            if admin.estado == 'activo':
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Su cuenta de administrador está inactiva.')
        except Administrador.DoesNotExist:
            messages.error(request, 'Acceso denegado. Se requiere cuenta de administrador.')

        return redirect('auth:login')

    return _wrapped_view

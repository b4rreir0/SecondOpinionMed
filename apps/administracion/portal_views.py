from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
import os

from authentication.models import CustomUser
from authentication.services import DoctorService


def _get_admin_credentials():
    email = getattr(settings, 'ADMIN_PORTAL_EMAIL', None)
    password = getattr(settings, 'ADMIN_PORTAL_PASSWORD', None)
    # Fallback: try reading ADMIN_CREDENTIALS.txt in project root
    if not email or not password:
        cred_path = os.path.join(settings.BASE_DIR, 'ADMIN_CREDENTIALS.txt')
        try:
            with open(cred_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ADMIN_EMAIL='):
                        email = email or line.strip().split('=', 1)[1]
                    if line.startswith('ADMIN_PASSWORD='):
                        password = password or line.strip().split('=', 1)[1]
        except Exception:
            pass
    return email, password


class AdminLoginView(View):
    template_name = 'administracion/portal_login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        admin_email, admin_password = _get_admin_credentials()
        if admin_email and admin_password and email == admin_email and password == admin_password:
            request.session['is_custom_admin'] = True
            return redirect(reverse('administracion:portal_panel'))
        messages.error(request, 'Credenciales inválidas')
        return render(request, self.template_name)


class AdminLogoutView(View):
    def get(self, request):
        request.session.pop('is_custom_admin', None)
        return redirect(reverse('administracion:portal_login'))


from functools import wraps


def admin_required_portal(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        # args may be (request, ...) for function-based views
        # or (self, request, ...) for class-based view methods
        request = None
        if len(args) >= 1 and hasattr(args[0], 'session'):
            request = args[0]
        elif len(args) >= 2 and hasattr(args[1], 'session'):
            request = args[1]

        if request is None:
            return redirect(reverse('administracion:portal_login'))

        if not request.session.get('is_custom_admin'):
            return redirect(reverse('administracion:portal_login'))

        return view_func(*args, **kwargs)

    return wrapped


class AdminPanelView(View):
    template_name = 'administracion/portal_panel.html'

    @admin_required_portal
    def get(self, request):
        # Only one section: Invitar doctores
        return render(request, self.template_name, {'section': 'invite'})


class InviteDoctorView(View):
    @admin_required_portal
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Introduce un correo válido')
            return redirect(reverse('administracion:portal_panel'))

        # Try to find admin user as invited_by
        invited_by = None
        admin_email, _ = _get_admin_credentials()
        if admin_email:
            try:
                invited_by = CustomUser.objects.filter(email=admin_email).first()
            except Exception:
                invited_by = None

        DoctorService.invite_doctor(email, invited_by)
        messages.success(request, f'Invitación enviada a {email} (en cola)')
        return redirect(reverse('administracion:portal_panel'))

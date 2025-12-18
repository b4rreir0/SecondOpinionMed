from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from authentication.models import CustomUser
from .models import DoctorInvitation, PatientVerification


class DoctorRegisterView(View):
    template_name = 'registration/doctor_registration_form.html'

    def get(self, request, token):
        try:
            invite = DoctorInvitation.objects.get(token=token)
        except DoctorInvitation.DoesNotExist:
            return render(request, 'registration/invalid_invite.html', {'reason': 'no_exist'})

        if not invite.is_valid():
            return render(request, 'registration/invalid_invite.html', {'reason': 'expired'})

        return render(request, self.template_name, {'invite': invite})

    def post(self, request, token):
        # Simple registration: create user and doctor profile minimal fields
        try:
            invite = DoctorInvitation.objects.get(token=token)
        except DoctorInvitation.DoesNotExist:
            messages.error(request, 'Invitación inválida')
            return redirect('home')

        if not invite.is_valid():
            messages.error(request, 'Invitación expirada')
            return redirect('home')

        email = invite.invited_email
        password = request.POST.get('password')
        full_name = request.POST.get('full_name', '')

        if not password:
            messages.error(request, 'Password requerida')
            return render(request, self.template_name, {'invite': invite})

        user = CustomUser.objects.create_user(username=email, email=email, password=password, role='doctor', is_active=True, email_verified=True)
        # Minimal profile creation if needed — avoid requiring more fields here
        invite.mark_used()

        messages.success(request, 'Registro completado. Ya puedes iniciar sesión.')
        return redirect(reverse('auth:login'))


class VerifyPatientView(View):
    template_name = 'auth/patient_activation.html'

    def get(self, request, token):
        try:
            pv = PatientVerification.objects.get(token=token)
        except PatientVerification.DoesNotExist:
            return render(request, self.template_name, {'success': False, 'message': 'Token inválido'})

        if not pv.is_valid():
            return render(request, self.template_name, {'success': False, 'message': 'Token inválido o expirado'})

        # Activate user
        user = pv.user
        user.is_active = True
        user.email_verified = True
        user.save(update_fields=['is_active', 'email_verified'])

        pv.mark_verified()

        return render(request, self.template_name, {'success': True, 'message': 'Cuenta activada correctamente'})

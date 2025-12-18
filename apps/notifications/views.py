from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from authentication.models import CustomUser
from authentication.services import DoctorService
from django.core.exceptions import ValidationError
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
        medical_license = request.POST.get('medical_license', '')
        specialty = request.POST.get('specialty', '')
        phone_number = request.POST.get('phone_number', '')
        institution = request.POST.get('institution', '')

        if not password:
            messages.error(request, 'Password requerida')
            return render(request, self.template_name, {'invite': invite})

        try:
            user, profile = DoctorService.complete_registration(
                token=token,
                password=password,
                full_name=full_name,
                medical_license=medical_license,
                specialty=specialty,
                phone_number=phone_number,
                institution=institution,
            )
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, self.template_name, {'invite': invite})
        except Exception as e:
            messages.error(request, 'Error al completar el registro')
            return render(request, self.template_name, {'invite': invite})

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

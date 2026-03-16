from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from authentication.models import CustomUser
from authentication.services import DoctorService
from django.core.exceptions import ValidationError
from medicos.models import TipoCancer
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

        # Obtener todos los tipos de cáncer disponibles para la selección
        tipos_cancer = TipoCancer.objects.filter(activo=True).select_related('grupo_medico')

        return render(request, self.template_name, {
            'invite': invite,
            'tipos_cancer': tipos_cancer
        })

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
        
        # Construir full_name desde nombres y apellidos
        nombres = request.POST.get('nombres', '')
        apellidos = request.POST.get('apellidos', '')
        full_name = f"{nombres} {apellidos}".strip()
        
        # Usar número de documento como registro médico
        numero_documento = request.POST.get('numero_documento', '')
        medical_license = numero_documento
        
        specialty = request.POST.get('specialty', '')
        phone_number = request.POST.get('phone_number', '')
        
        # Datos adicionales del médico
        tipo_documento = request.POST.get('tipo_documento', 'cc')
        fecha_nacimiento = request.POST.get('fecha_nacimiento', '')
        genero = request.POST.get('genero', 'otro')
        experiencia_anios_str = request.POST.get('experiencia_anios', '0')
        try:
            experiencia_anios = int(experiencia_anios_str)
        except ValueError:
            experiencia_anios = 0

        # Tipos de cáncer seleccionados
        tipos_cancer_ids = request.POST.getlist('tipos_cancer')

        if not password:
            messages.error(request, 'La contraseña es requerida')
            tipos_cancer = TipoCancer.objects.filter(activo=True)
            return render(request, self.template_name, {
                'invite': invite,
                'tipos_cancer': tipos_cancer
            })

        try:
            # Convertir fecha de nacimiento
            fecha_nac = None
            if fecha_nacimiento:
                from datetime import date
                try:
                    fecha_nac = date.fromisoformat(fecha_nacimiento)
                except ValueError:
                    pass

            print(f"[DEBUG] Intentando registro con: email={email}, nombres={nombres}, numero_doc={numero_documento}")
            
            user, profile, medico = DoctorService.complete_registration(
                token=token,
                password=password,
                full_name=full_name,
                medical_license=medical_license,
                specialty=specialty,
                phone_number=phone_number,
                institution='',
                tipos_cancer_ids=tipos_cancer_ids,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                nombres=nombres,
                apellidos=apellidos,
                fecha_nacimiento=fecha_nac,
                genero=genero,
                experiencia_anios=experiencia_anios,
            )
            
            print(f"[DEBUG] Registro exitoso: user={user.email}, medico={medico.id}")
            messages.success(request, 'Registro completado. Ya puedes iniciar sesión.')
            return redirect(reverse('auth:login'))
            
        except ValidationError as e:
            print(f"[DEBUG] ValidationError: {str(e)}")
            messages.error(request, str(e))
            tipos_cancer = TipoCancer.objects.filter(activo=True)
            return render(request, self.template_name, {
                'invite': invite,
                'tipos_cancer': tipos_cancer
            })
        except Exception as e:
            print(f"[DEBUG] Exception: {type(e).__name__}: {str(e)}")
            messages.error(request, f'Error al completar el registro: {str(e)}')
            tipos_cancer = TipoCancer.objects.filter(activo=True)
            return render(request, self.template_name, {
                'invite': invite,
                'tipos_cancer': tipos_cancer
            })


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

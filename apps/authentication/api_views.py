from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, AllowAny

from .api_serializers import DoctorInviteSerializer, CompleteRegistrationSerializer
from .services import DoctorService


class DoctorInviteAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = DoctorInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user, invite = DoctorService.invite_doctor(email, request.user)
            return Response({'detail': 'Invitación enviada', 'invite_token': str(invite.token)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CompleteRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompleteRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user, profile, medico = DoctorService.complete_registration(
                token=data['token'],
                password=data['password'],
                full_name=data['full_name'],
                medical_license=data['medical_license'],
                specialty=data['specialty'],
                phone_number=data['phone_number'],
                institution=data.get('institution', ''),
                tipos_cancer_ids=data.get('tipos_cancer_ids'),
                tipo_documento=data.get('tipo_documento', 'cc'),
                numero_documento=data.get('numero_documento', ''),
                nombres=data.get('nombres', ''),
                apellidos=data.get('apellidos', ''),
                fecha_nacimiento=data.get('fecha_nacimiento'),
                genero=data.get('genero', 'otro'),
                experiencia_anios=data.get('experiencia_anios', 0),
            )
            return Response({'detail': 'Registro completado. Cuenta activada.', 'medico_id': medico.id}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

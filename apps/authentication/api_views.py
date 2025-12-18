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
            user, profile = DoctorService.complete_registration(
                token=data['token'],
                password=data['password'],
                full_name=data['full_name'],
                medical_license=data['medical_license'],
                specialty=data['specialty'],
                phone_number=data['phone_number'],
                institution=data.get('institution', ''),
            )
            return Response({'detail': 'Registro completado. Cuenta activada.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

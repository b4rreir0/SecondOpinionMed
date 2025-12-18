from rest_framework import serializers


class DoctorInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()


class CompleteRegistrationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)
    medical_license = serializers.CharField(max_length=100)
    specialty = serializers.CharField(max_length=50)
    phone_number = serializers.CharField(max_length=20)
    institution = serializers.CharField(max_length=255, required=False, allow_blank=True)

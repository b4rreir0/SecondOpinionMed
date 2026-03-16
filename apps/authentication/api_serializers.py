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
    # Campos adicionales para el modelo Medico
    tipo_documento = serializers.CharField(max_length=20, required=False, default='cc')
    numero_documento = serializers.CharField(max_length=20, required=False, allow_blank=True)
    nombres = serializers.CharField(max_length=100, required=False, allow_blank=True)
    apellidos = serializers.CharField(max_length=100, required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    genero = serializers.CharField(max_length=20, required=False, default='otro')
    experiencia_anios = serializers.IntegerField(required=False, default=0)
    # Tipos de cáncer seleccionados
    tipos_cancer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

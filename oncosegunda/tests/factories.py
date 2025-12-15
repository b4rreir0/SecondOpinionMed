# tests/factories.py
import factory
from django.contrib.auth.models import User
from pacientes.models import Paciente, SolicitudSegundaOpinion, DocumentoPaciente
from medicos.models import Medico, AsignacionCaso, InformeSegundaOpinion
from core.models import ModuloSistema, Auditoria
from datetime import date, timedelta
import io

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('password123')

class PacienteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Paciente

    user = factory.SubFactory(UserFactory)
    fecha_nacimiento = date(1980, 1, 1)
    telefono_principal = '+34123456789'
    direccion = factory.Faker('address')
    ciudad = factory.Faker('city')
    codigo_postal = factory.Faker('postcode')
    acepta_contacto_whatsapp = True
    notificaciones_activas = True

class MedicoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Medico

    user = factory.SubFactory(UserFactory)
    especialidad = 'Oncología General'
    numero_colegiado = factory.Sequence(lambda n: f'COL-{n:06d}')
    hospital = 'Hospital Universitario'
    telefono_consultorio = '+34987654321'
    activo_en_rotacion = True
    max_casos_simultaneos = 10
    orden_rotacion = 0

class SolicitudSegundaOpinionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SolicitudSegundaOpinion

    paciente = factory.SubFactory(PacienteFactory)
    tipo_cancer = 'mama'
    fecha_diagnostico = date(2023, 6, 1)
    hospital_tratante = 'Hospital General'
    motivo_consulta = factory.Faker('text', max_nb_chars=200)
    estado = 'borrador'
    urgencia = 1

    @factory.lazy_attribute
    def codigo(self):
        from datetime import datetime
        fecha = datetime.now().strftime('%Y%m%d')
        return f'OP-{fecha}-{self.id:04d}'

class DocumentoPacienteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentoPaciente

    solicitud = factory.SubFactory(SolicitudSegundaOpinionFactory)
    tipo = 'patologia'
    nombre_original = 'informe_patologia.pdf'
    tamaño = 1024 * 1024  # 1MB
    hash_archivo = 'abc123def456'
    validado = True

    @factory.lazy_attribute
    def archivo(self):
        from django.core.files.base import ContentFile
        return ContentFile(b'Test document content', name='test_document.pdf')

class AsignacionCasoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AsignacionCaso

    medico = factory.SubFactory(MedicoFactory)
    solicitud = factory.SubFactory(SolicitudSegundaOpinionFactory)
    estado = 'asignado'

class InformeSegundaOpinionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformeSegundaOpinion

    asignacion = factory.SubFactory(AsignacionCasoFactory)
    resumen_caso = factory.Faker('text', max_nb_chars=500)
    diagnostico_confirmado = factory.Faker('text', max_nb_chars=300)
    recomendaciones_tratamiento = ['Quimioterapia', 'Radioterapia']
    seguimiento_recomendado = factory.Faker('text', max_nb_chars=200)
    estado = 'borrador'

class ModuloSistemaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ModuloSistema

    nombre = factory.Sequence(lambda n: f'modulo_{n}')
    descripcion = factory.Faker('text', max_nb_chars=100)
    estado = 'activo'
    version = '1.0.0'
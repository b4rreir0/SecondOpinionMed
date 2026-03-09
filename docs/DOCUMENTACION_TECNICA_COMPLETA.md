# 📋 DOCUMENTACIÓN TÉCNICA COMPLETA DEL SISTEMA

## Sistema de Segunda Opinión Oncológica - SecondOpinionMed

---

## ÍNDICE

1. [Visión General del Sistema](#1-visión-general-del-sistema)
2. [Arquitectura y Stack Tecnológico](#2-arquitectura-y-stack-tecnológico)
3. [Roles y Permisos](#3-roles-y-permisos)
4. [Modelos de Datos](#4-modelos-de-datos)
5. [Flujos de Datos - Casos de Uso Completos](#5-flujos-de-datos---casos-de-uso-completos)
6. [Sistema de Notificaciones](#6-sistema-de-notificaciones)
7. [Algoritmo de Asignación Automática](#7-algoritmo-de-asignación-automática)
8. [Sistema de Comités Multidisciplinarios (MDT)](#8-sistema-de-comités-multidisciplinarios-mdt)
9. [Estados de los Casos y Transiciones](#9-estados-de-los-casos-y-transiciones)
10. [Seguridad y Cumplimiento](#10-seguridad-y-cumplimiento)
11. [Endpoints Principales](#11-endpoints-principales)
12. [Resumen de Funcionalidades](#12-resumen-de-funcionalidades)

---

## 1. VISIÓN GENERAL DEL SISTEMA

El **Sistema de Segunda Opinión Oncológica** es una plataforma web profesional desarrollada en Django que permite a los pacientes solicitar evaluaciones médicas de sus casos oncológicos. El sistema coordina comités multidisciplinarios (MDT - Multidisciplinary Team) donde múltiples especialistas evalúan colaborativamente cada caso.

### Propósito Principal
- **Pacientes**: Solicitar segunda opinión médica sobre diagnósticos y tratamientos oncológicos
- **Médicos**: Evaluar casos asignados, participar en comités, emitir opiniones y consensuar recomendaciones
- **Administradores**: Gestionar la plataforma, usuarios, comités y configuración del sistema

### Características Clave
- ✅ Asignación automática de casos mediante algoritmo round-robin avanzado
- ✅ Comités multidisciplinarios especializados por tipo de cáncer
- ✅ Sistema de votación y consenso entre médicos
- ✅ Workflow de estados con transiciones controladas (FSM)
- ✅ Notificaciones en tiempo real (in-app + email)
- ✅ Auditoría completa de todas las acciones
- ✅ Cifrado de datos sensibles (PHI)
- ✅ API REST para integración

---

## 2. ARQUITECTURA Y STACK TECNOLÓGICO

### 2.1 Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Navegador)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Paciente  │  │   Médico    │  │    Admin    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼───────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     NGINX (Reverse Proxy)                       │
│                   Puerto 80/443 - SSL/TLS                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│               DJANGO + GUNICORN (Servidor WSGI)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    APLICACIONES Django                    │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────┐    │  │
│  │  │ Authentica- │ │   Pacientes │ │     Cases        │    │  │
│  │  │    tion     │ │             │ │   (Core MDT)     │    │  │
│  │  └─────────────┘ └─────────────┘ └───────────────────┘    │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────┐    │  │
│  │  │  Medicos   │ │   Admin     │ │   Notifications  │    │  │
│  │  │            │ │             │ │                   │    │  │
│  │  └─────────────┘ └─────────────┘ └───────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │  │     Redis     │  │  Almacenamiento│
│   (Datos)     │  │ (Caché/Cola)  │  │    Local/S3   │
└───────────────┘  └───────────────┘  └───────────────┘
                           │
                           ▼
                  ┌───────────────┐
                  │    Celery     │
                  │   Workers     │
                  │ (Tareas Async) │
                  └───────────────┘
```

### 2.2 Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|------------|---------|
| Backend | Django | 6.0 |
| Python | Python | 3.11+ |
| Base de Datos | PostgreSQL | 14+ |
| Cache/Cola | Redis | 7.0+ |
| Tareas Asíncronas | Celery | 5.3+ |
| Frontend | HTML5 + Tailwind CSS | 3.4+ |
| Servidor Web | Nginx + Gunicorn | - |
| Contenedores | Docker + Docker Compose | - |

### 2.3 Estructura de Aplicaciones

```
apps/
├── authentication/       # Gestión de usuarios y autenticación
│   ├── models.py         # CustomUser, PatientProfile, DoctorProfile
│   ├── views.py          # Login, register, password reset
│   ├── forms.py          # Formularios de autenticación
│   ├── services.py       # Lógica de verificación, invitación médicos
│   └── api_*.py          # Endpoints REST
│
├── pacientes/            # Gestión de pacientes
│   ├── models.py         # Paciente, CasoClinico
│   ├── views.py         # Dashboard paciente, crear solicitud
│   └── forms.py         # Formularios de solicitud
│
├── medicos/             # Gestión de médicos y comités
│   ├── models.py        # Medico, Especialidad, MedicalGroup, ComiteMultidisciplinario
│   ├── views.py         # Dashboard médico
│   └── forms.py         # Formularios médicos
│
├── cases/               # Sistema principal de casos y MDT
│   ├── models.py        # Case, CaseDocument, MedicalOpinion, FinalReport
│   ├── services.py      # CaseService, asignación básica
│   ├── mdt_services.py  # AssignmentService, ConsensusService, MDTMessageService
│   ├── mdt_models.py    # Modelos adicionales MDT (mensajes, presencia)
│   ├── views.py        # Vistas de casos
│   └── signals.py      # Señales Django para triggers
│
├── administracion/      # Panel de administración
│   ├── models.py       # Configuración del sistema
│   ├── views.py       # Dashboard admin
│   └── portal_views.py # Portal de administración
│
├── notifications/      # Sistema de notificaciones
│   ├── models.py       # Notification, EmailLog, DoctorInvitation
│   ├── services.py    # EmailService
│   └── tasks.py       # Tareas Celery para emails
│
├── documents/          # Gestión de documentos
│   ├── services.py    # Procesamiento de archivos
│   └── tasks.py       # Tareas de anonimización
│
└── core/              # Utilidades compartidas
    ├── models.py      # Modelos base (TimeStampedModel)
    ├── decorators.py  # Decoradores de permisos
    ├── middleware.py  # Middleware personalizado
    └── services.py    # Servicios globales
```

---

## 3. ROLES Y PERMISOS

### 3.1 Roles del Sistema

| Rol | Código | Descripción | Acceso Principal |
|-----|--------|-------------|------------------|
| **Paciente** | `patient` | Usuario que solicita segunda opinión | Portal Paciente |
| **Médico** | `doctor` | Especialista que evalúa casos | Portal Médico |
| **Administrador** | `staff` | Administrador de la plataforma | Panel Admin Django |

### 3.2 Implementación del Modelo de Usuario

El modelo [`CustomUser`](apps/authentication/models.py:14) extiende `AbstractUser` de Django:

```python
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Paciente'),
        ('doctor', 'Médico'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    is_active = models.BooleanField(default=False)  # Se activa tras verificación de email
    email_verified = models.BooleanField(default=False)
```

### 3.3 Perfiles de Usuario

#### PatientProfile ([`apps/authentication/models.py`](apps/authentication/models.py:66))
Almacena datos sensibles del paciente (cifrados):
- `full_name`: Nombre completo
- `identity_document`: Documento de identidad
- `phone_number`: Teléfono de contacto
- `date_of_birth`: Fecha de nacimiento
- `medical_history`: Historial médico
- `current_treatment`: Tratamiento actual

#### Medico ([`apps/medicos/models.py`](apps/medicos/models.py:49))
Perfil profesional del médico:
- `nombres`, `apellidos`: Datos personales
- `registro_medico`: Número de licencia médica
- `especialidades`: Especialidades médicas (M2M)
- `institucion_actual`: Institución donde trabaja
- `disponible_segundas_opiniones`: Disponibilidad
- `max_casos_mes`: Límite de casos mensuales
- `casos_actuales`: Contador de casos activos

---

## 4. MODELOS DE DATOS

### 4.1 Modelos Principales

#### Case ([`apps/cases/models.py`](apps/cases/models.py:24))
El modelo central del sistema representa una solicitud de segunda opinión:

```python
class Case(models.Model):
    # Relaciones
    patient = models.ForeignKey('authentication.CustomUser')  # Paciente solicitante
    doctor = models.ForeignKey('authentication.CustomUser', null=True)  # Médico asignado
    medical_group = models.ForeignKey('medicos.MedicalGroup', null=True)  # Grupo MDT asignado
    responsable = models.ForeignKey('medicos.Medico', null=True)  # Médico responsable
    
    # Datos del caso
    case_id = models.CharField(max_length=50, unique=True)  # "CASO-B28C7C3ABE7B"
    primary_diagnosis = EncryptedCharField()  # Diagnóstico primario (cifrado)
    specialty_required = models.CharField()  # Especialidad requerida
    tipo_cancer = models.ForeignKey('medicos.TipoCancer', null=True)  # Tipo de cáncer
    estadio = models.CharField(choices=ESTADIO_CHOICES)  # Estadio (I, II, III, IV)
    tratamiento_propuesto_original = models.TextField()  # Tratamiento propuesto
    description = EncryptedTextField()  # Descripción del caso (cifrada)
    diagnosis_date = models.DateField()  # Fecha del diagnóstico
    localidad = models.ForeignKey('medicos.Localidad', null=True)  # Localidad
    
    # Estado FSM
    status = FSMField(choices=STATUS_CHOICES, default='DRAFT')
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True)
    fecha_limite = models.DateField(null=True)
    completed_at = models.DateTimeField(null=True)
```

#### CaseDocument ([`apps/cases/models.py`](apps/cases/models.py:261))
Documentos médicos asociados a un caso:

```python
class CaseDocument(models.Model):
    case = models.ForeignKey(Case, related_name='documents')
    document_type = models.CharField(choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='cases/{case_id}/documents/')
    description = models.CharField(blank=True)
    is_anonymized = models.BooleanField(default=False)
    s3_file_path = models.CharField(blank=True)  # Ruta en S3 si se usa
    file_size = models.PositiveIntegerField(null=True)
    mime_type = models.CharField(blank=True)
    file_name = models.CharField()
    uploaded_by = models.ForeignKey('authentication.CustomUser')
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

#### MedicalOpinion ([`apps/cases/models.py`](apps/cases/models.py:437))
Opinión/voto de un médico miembro del comité:

```python
class MedicalOpinion(models.Model):
    case = models.ForeignKey(Case, related_name='opiniones')
    doctor = models.ForeignKey('medicos.Medico', related_name='opiniones_casos')
    voto = models.CharField(choices=VOTO_CHOICES)  # acuerdo/desacuerdo/abstencion
    comentario_privado = models.TextField(blank=True)  # Comentario solo para el grupo
    fecha_emision = models.DateTimeField(auto_now_add=True)
```

#### FinalReport ([`apps/cases/models.py`](apps/cases/models.py:490))
Informe final consolidado del caso:

```python
class FinalReport(models.Model):
    case = models.OneToOneField(Case, related_name='informe_final')
    contenido = models.TextField()
    recomendaciones = models.JSONField()  # Recomendaciones estructuradas
    conclusion = models.CharField()  # acuerdo/desacuerdo/consenso_parcial
    nivel_evidencia = models.CharField()  # Nivel de evidencia
    generado_por = models.ForeignKey('medicos.Medico')
    fecha_generacion = models.DateTimeField(auto_now_add=True)
```

### 4.2 Modelos de Médicos y Comités

#### Especialidad ([`apps/medicos/models.py`](apps/medicos/models.py:9))
```python
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
```

#### TipoCancer ([`apps/medicos/models.py`](apps/medicos/models.py:23))
```python
class TipoCancer(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)  # Ej: PULMON, MAMA
    especialidad_principal = models.ForeignKey(Especialidad)
    activo = models.BooleanField(default=True)
```

#### MedicalGroup ([`apps/medicos/models.py`](apps/medicos/models.py:206))
Grupo médico / Comité por tipo de cáncer:

```python
class MedicalGroup(models.Model):
    nombre = models.CharField(max_length=100)  # Ej: "Comité de Pulmón"
    tipo_cancer = models.ForeignKey(TipoCancer)
    responsable_por_defecto = models.ForeignKey(Medico, null=True)
    quorum_config = models.PositiveSmallIntegerField(default=3)  # Mínimo para决策
    activo = models.BooleanField(default=True)
```

#### DoctorGroupMembership ([`apps/medicos/models.py`](apps/medicos/models.py:265))
Membresía de médico en grupo:

```python
class DoctorGroupMembership(models.Model):
    medico = models.ForeignKey(Medico)
    grupo = models.ForeignKey(MedicalGroup)
    rol = models.CharField(choices=ROL_CHOICES)  # coordinador, miembro_senior, etc.
    es_responsable = models.BooleanField(default=False)
    puede_votar = models.BooleanField(default=True)
    disponible_asignacion_auto = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
```

#### ComiteMultidisciplinario ([`apps/medicos/models.py`](apps/medicos/models.py:162))
Comité multidisciplinario tradicional:

```python
class ComiteMultidisciplinario(models.Model):
    nombre = models.CharField(max_length=100)
    especialidades_requeridas = models.ManyToManyField(Especialidad)
    medicos_miembros = models.ManyToManyField(Medico)
    coordinador = models.ForeignKey(Medico, null=True)  # Jefe del comité
    min_medicos = models.PositiveIntegerField(default=3)
    max_casos_simultaneos = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)
```

### 4.3 Modelos de Notificaciones

#### Notification ([`apps/notifications/models.py`](apps/notifications/models.py:101))
```python
class Notification(models.Model):
    TIPO_CHOICES = [
        ('asignacion_caso', 'Nuevo caso asignado'),
        ('nueva_opinion', 'Nueva opinión en caso'),
        ('recordatorio_voto', 'Recordatorio de votación'),
        ('votacion_cerrada', 'Votación cerrada'),
        ('informe_disponible', 'Informe final disponible'),
        ('caso_actualizado', 'Caso actualizado'),
        ('documento_subido', 'Nuevo documento subido'),
    ]
    
    receptor = models.ForeignKey('authentication.CustomUser')
    tipo = models.CharField(choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    enlace = models.CharField(max_length=500, blank=True)
    leido = models.BooleanField(default=False)
    caso_id = models.CharField(max_length=50, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
```

---

## 5. FLUJOS DE DATOS - CASOS DE USO COMPLETOS

### 5.1 Flujo 1: Registro y Verificación de Paciente

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO: REGISTRO DE PACIENTE                              │
└─────────────────────────────────────────────────────────────────────────────┘

1. USUARIO VISITA PÁGINA
   └─> GET /accounts/register/

2. USUARIO COMPLETA FORMULARIO
    ├── Email (único)
    ├── Contraseña
    ├── Nombre completo
    ├── Teléfono
    └── Consentimiento T&C

3. DJANGO PROCESA REGISTRO
    │
    ├── CustomUser.objects.create(
    │       email="paciente@email.com",
    │       role="patient",
    │       is_active=False,        # ⚠️ Inactivo hasta verificación
    │       email_verified=False
    │   )
    │
    ├── PatientProfile.objects.create(
    │       user=user,
    │       full_name="Nombre Completo",  # ⚙️ CIFRADO
    │       phone_number="+1234567890"    # ⚙️ CIFRADO
    │   )
    │
    └── EmailVerificationToken.objects.create(
            user=user,
            token="abc123...",
            expires_at=timezone.now() + 24h
        )

4. SE ENVÍA EMAIL DE VERIFICACIÓN
    │
    └── Celery Task: send_email_task
            │
            ├── Renderiza template: emails/verify_email.html
            ├── Envia a: paciente@email.com
            └── Enlace: /accounts/verify/{token}/

5. USUARIO VERIFICA EMAIL
    │
    └── GET /accounts/verify/abc123.../
            │
            ├── Busca token en EmailVerificationToken
            ├── Verifica: not expired AND not used
            ├── user.is_active = True
            ├── user.email_verified = True
            ├── token.is_used = True
            └── Redirecciona a: /patients/dashboard/

VISUALIZACIÓN RESULTADO:
   ✅ Panel del Paciente accesible
   ✅ Puede crear solicitudes de segunda opinión
   ✅ Recibe notificaciones por email
```

### 5.2 Flujo 2: Creación de Solicitud de Segunda Opinión

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            FLUJO: CREACIÓN DE SOLICITUD DE SEGUNDA OPINIÓN                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. PACIENTE ACCEDE A CREAR SOLICITUD
   └─> GET /patients/solicitud/nueva/

2. FORMULARIO MULTI-PASO (Session-based)

   ╔═══════════════════════════════════════════════════════════════════════╗
   ║  PASÓ 1: Datos del Paciente                                         ║
   ╠═══════════════════════════════════════════════════════════════════════╣
   ║  • Nombre completo (cifrado)                                         ║
   ║  • Documento de identidad (cifrado)                                  ║
   ║  • Fecha de nacimiento                                               ║
   ║  • Teléfono de contacto (cifrado)                                    ║
   ║  • Consentimiento informado                                         ║
   ╚═══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
   ╔═══════════════════════════════════════════════════════════════════════╗
   ║  PASÓ 2: Información Clínica                                         ║
   ╠═══════════════════════════════════════════════════════════════════════╣
   ║  • Diagnóstico primario (cifrado)                                   ║
   ║  • Tipo de cáncer (selección)                                        ║
   ║  • Estadio (I, II, III, IV, N/A)                                     ║
   ║  • Fecha del diagnóstico                                             ║
   ║  • Tratamiento propuesto original                                    ║
   ║  • Objetivo de la consulta                                           ║
   ╚═══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
   ╔═══════════════════════════════════════════════════════════════════════╗
   ║  PASÓ 3: Documentos Médicos                                          ║
   ╠═══════════════════════════════════════════════════════════════════════╣
   ║  • Upload de archivos (múltiples)                                    ║
   ║  • Tipos: Informe diagnóstico, Biopsia, Imágenes, Laboratorio       ║
   ║  • Validación: PDF, JPG, PNG, DICOM (máx 50MB por archivo)           ║
   ║  • Almacenamiento: /media/cases/{case_id}/documents/                 ║
   ╚═══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
   ╔═══════════════════════════════════════════════════════════════════════╗
   ║  PASÓ 4: Revisión y Confirmación                                      ║
   ╠═══════════════════════════════════════════════════════════════════════╣
   ║  • Resumen de todos los datos                                         ║
   ║  • Checkbox: Consentimiento explícito (OBLIGATORIO)                  ║
   ║  • Botón: "Enviar Solicitud"                                          ║
   ╚═══════════════════════════════════════════════════════════════════════╝

3. PROCESAMIENTO DEL ENVÍO (CaseService.finalize_submission)
   │
   ├── GUARDA DATOS EN SESIÓN
   │   └── session['solicitud_data'] = {patient_profile, case_draft, documents}
   │
   ├── CREA EL CASO (transacción atómica)
   │   │
   │   ├── case_id = f"CASO-{uuid.uuid4().hex[:12].upper()}"  # Ej: CASO-B28C7C3ABE7B
   │   │
   │   └── Case.objects.create(
   │           patient=user,
   │           case_id=case_id,
   │           primary_diagnosis=...,     # ⚙️ CIFRADO
   │           tipo_cancer=...,
   │           estadio=...,
   │           tratamiento_propuesto_original=...,
   │           description=...,           # ⚙️ CIFRADO
   │           status='SUBMITTED'
   │       )
   │
   ├── CREA REGISTROS DE DOCUMENTOS
   │   └── CaseDocument.objects.create(
   │           case=case,
   │           document_type=...,
   │           file=archivo_subido,
   │           uploaded_by=user
   │       )
   │
   ├── TRANSICIÓN FSM: DRAFT → SUBMITTED
   │   └── case.submit_case()
   │
   ├── REGISTRA AUDITORÍA
   │   └── CaseAuditLog.objects.create(
   │           case=case,
   │           user=user,
   │           action='create',
   │           description='Caso enviado desde flujo SOP'
   │       )
   │
   └── ASIGNA PERMISOS (django-guardian)
       └── assign_perm('view_case', user, case)

4. TRIGGER: SEÑAL POST_SAVE (apps/cases/signals.py)
   │
   └── case_post_save(sender=Case, instance=case, created=True)
           │
           └── asignar_caso_automatico(case)
                   │
                   ├── AssignmentService.asignar_caso(caso)
                   │       │
                   │       ├── Obtiene MedicalGroup según tipo_cancer
                   │       ├── Filtra miembros activos y disponibles
                   │       ├── Calcula scores (carga + antigüedad)
                   │       ├── Selecciona mejor candidato
                   │       └── Registra en AsignacionAuditLog
                   │
                   ├── Asigna al caso:
                   │       ├── caso.doctor = medico.usuario
                   │       ├── caso.responsable = medico
                   │       ├── caso.medical_group = grupo
                   │       └── caso.assign_to_group()  # FSM: SUBMITTED → ASSIGNED
                   │
                   └── Notificaciones:
                           ├── Notifica al médico asignado
                           └── Notifica al coordinador del grupo MDT

5. ENVÍO DE NOTIFICACIONES
   │
   ├── EmailService.create_and_queue_email(
   │       recipient=medico.email,
   │       template_name='nuevo_caso_asignado',
   │       context={'case': case, 'paciente': ...}
   │   )
   │
   └── Notification.objects.create(
           receptor=medico.usuario,
           tipo='asignacion_caso',
           titulo='Nuevo caso asignado',
           mensaje=f'Se le ha asignado el caso {case.case_id}',
           enlace=f'/doctors/casos/{case.case_id}/',
           caso_id=case.case_id
       )

VISUALIZACIÓN RESULTADO:
   ┌─────────────────────────────────────────────────────────┐
   │              DASHBOARD PACIENTE                         │
   ├─────────────────────────────────────────────────────────┤
   │  Estado: "ENVIADO"  →  "ASIGNADO"  →  "EN_PROCESO"    │
   │                                                         │
   │  └─> Caso CASO-B28C7C3ABE7B                           │
   │       ├── Estado: Asignado                             │
   │       ├── Especialidad: Oncología Pulmón             │
   │       ├── Responsable: Dr. Juan Pérez                 │
   │       └── Fecha límite: [calculada]                   │
   └─────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────┐
   │              DASHBOARD MÉDICO                           │
   ├─────────────────────────────────────────────────────────┤
   │  └─> Nuevo caso en lista                              │
   │       ├── Diagnóstico: Carcinoma Pulmón Estadio III   │
   │       ├── Paciente: [Nombre cifrado]                  │
   │       └── Acciones: [Revisar Caso]                    │
   └─────────────────────────────────────────────────────────┘
```

### 5.3 Flujo 3: Revisión del Médico y Análisis MDT

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               FLUJO: REVISIÓN DEL MÉDICO Y ANÁLISIS MDT                    │
└─────────────────────────────────────────────────────────────────────────────┘

1. MÉDICO RECIBE NOTIFICACIÓN
   │
   ├── Notificación in-app en dashboard
   ├── Email con enlace al caso
   └── Acceso: GET /doctors/casos/{case_id}/

2. MÉDICO REVISA EL CASO
   │
   ├── Ver datos del paciente (descriptados)
   ├── Descargar/anexar documentos médicos
   ├── Ver historial de cambios (audit log)
   └── Acciones disponibles según estado

3. TRANSICIÓN: ASSIGNED → PROCESSING
   │
   └── case.process_documents()  # FSM: ASSIGNED → PROCESSING
           │
           ├── status = 'PROCESSING'
           └── assigned_at = timezone.now()

4. MÉDICO PUEDE SOLICITAR INFORMACIÓN ADICIONAL
   │
   └── POST /doctors/casos/{case_id}/solicitar-info/
           │
           ├── Motivo de la solicitud
           ├── Notifica al paciente
           └── Estado: 'CLARIFICATION_NEEDED' (opcional)

5. INICIAR DISCUSIÓN MDT (si es necesario)
   │
   └── POST /doctors/casos/{case_id}/iniciar-mdt/
           │
           ├── case.iniciar_discusion_mdt()  # FSM: PROCESSING → MDT_IN_PROGRESS
           ├── Crea ConsensusWorkflow (fase='DISCUSION')
           ├── Notifica a todos los miembros del MedicalGroup
           └── Habilita chat/mensajería MDT

6. FLUJO DE CONSENSO MDT
   │
   │  ╔═══════════════════════════════════════════════════════════════════╗
   │  ║  FASE 1: DISCUSIÓN                                                  ║
   │  ╠═══════════════════════════════════════════════════════════════════╣
   │  ║  • Todos los miembros ven el caso                                  ║
   │  ║  • Chat/mensajería grupal (MDTMessage)                             ║
   │  ║  • Comentarios privados entre miembros                             ║
   │  ║  • El sistema registra presencia en tiempo real                    ║
   │  ╚═══════════════════════════════════════════════════════════════════╝
   │                              │
   │                              ▼
   │  ╔═══════════════════════════════════════════════════════════════════╗
   │  ║  FASE 2: PROPUESTA                                                 ║
   │  ╠═══════════════════════════════════════════════════════════════════╣
   │  ║  • Coordinador redacta propuesta de consenso                       ║
   │  ║  • ConsensusService.redactar_propuesta()                           ║
   │  ║  • Se crean versiones (ConsensusVersion)                          ║
   │  ╚═══════════════════════════════════════════════════════════════════╝
   │                              │
   │                              ▼
   │  ╔═══════════════════════════════════════════════════════════════════╗
   │  ║  FASE 3: VOTACIÓN                                                   ║
   │  ╠═══════════════════════════════════════════════════════════════════╣
   │  ║  • Cada miembro vota:                                               ║
   │  ║    - 'acuerdo' (De acuerdo con tratamiento propuesto)               ║
   │  ║    - 'desacuerdo' (En desacuerdo)                                   ║
   │  ║    - 'abstencion' (Se abstiene)                                     ║
   │  ║  • Cada voto incluye justificación (OpinionDisidente si en contra)  ║
   │  ║  • El sistema calcula niveles de evidencia                         ║
   │  ╚═══════════════════════════════════════════════════════════════════╝
   │                              │
   │                              ▼
   │  ╔═══════════════════════════════════════════════════════════════════╗
   │  ║  FASE 4: CONSENSO/DISENSO                                          ║
   │  ╠═══════════════════════════════════════════════════════════════════╣
   │  ║  • ConsensusService.cerrar_votacion()                              ║
   │  ║  • Si hay consenso: fase = 'CONSENSO'                              ║
   │  ║  • Si no: fase = 'DISENSO' + opiniones disidentes registradas     ║
   │  ║  • Transición: MDT_IN_PROGRESS → MDT_COMPLETED                    ║
   │  ╚═══════════════════════════════════════════════════════════════════╝

7. EMISIÓN DE OPINIÓN INDIVIDUAL
   │
   └── POST /doctors/casos/{case_id}/opinion/
           │
           └── MedicalOpinion.objects.create(
                   case=case,
                   doctor=medico,
                   voto=...,
                   comentario_privado=...
               )

8. REDACCIÓN DEL INFORME FINAL
   │
   └── POST /doctors/casos/{case_id}/informe/
           │
           ├── case.iniciar_informe()  # FSM: MDT_COMPLETED → REPORT_DRAFT
           │
           ├── FinalReport.objects.create(
                   case=case,
                   contenido=...,
                   recomendaciones={...},  # JSON estructurado
                   conclusion=...,
                   nivel_evidencia=...,
                   generado_por=medico
               )
           │
           └── case.completar_informe()  # FSM: REPORT_DRAFT → REPORT_COMPLETED

9. CIERRE DEL CASO
   │
   └── POST /doctors/casos/{case_id}/cerrar/
           │
           └── case.cerrar_caso()  # FSM: REPORT_COMPLETED → CLOSED
                   │
                   ├── completed_at = timezone.now()
                   ├── Notifica al paciente por email
                   ├── Notificación in-app
                   └── Caso archivado

VISUALIZACIÓN SEGÚN ROL:
   
   ┌─────────────────────────────────────────────────────────────┐
   │               VISUALIZACIÓN PACIENTE                        │
   ├─────────────────────────────────────────────────────────────┤
   │  Estado: COMPLETADO ✓                                       │
   │                                                             │
   │  📋 Caso CASO-B28C7C3ABE7B                                 │
   │  ─────────────────────────────────────────                  │
   │  Estado: CERRADO                                            │
   │  Diagnóstico: Carcinoma de Pulmón Estadio III               │
   │  Tipo de cáncer: Pulmón                                     │
   │  Estadio: III                                               │
   │                                                             │
   │  📎 Documentos subidos: 3 archivos                          │
   │                                                             │
   │  📄 INFORME FINAL DISPONIBLE                               │
   │  ─────────────────────────────────────────                  │
   │  Conclusión: ACUERDO con tratamiento propuesto              │
   │  Nivel de evidencia: ALTO                                    │
   │                                                             │
   │  [Descargar Informe PDF]                                    │
   └─────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────┐
   │               VISUALIZACIÓN ADMINISTRADOR                   │
   ├─────────────────────────────────────────────────────────────┤
   │  Panel → Casos → CASO-B28C7C3ABE7B                         │
   │  ─────────────────────────────────────────                 │
   │  Estado: CERRADO                                            │
   │  Paciente: [CIFRADO]                                       │
   │  Médico responsable: Dr. Juan Pérez                         │
   │  Medical Group: Comité de Pulmón                           │
   │  Votos: 5 a favor, 0 en contra, 0 abstenciones             │
   │  Fecha completado: 15/02/2025                              │
   │  Tiempo total: 5 días                                       │
   └─────────────────────────────────────────────────────────────┘
```

### 5.4 Flujo 4: Algoritmo de Asignación Automática (Detallado)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            FLUJO: ALGORITMO DE ASIGNACIÓN ROUND-ROBIN AVANZADO              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     DIAGRAMA DE FLUJO DEL ALGORITMO                         │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────┐
    │     CASO NUEVO RECIBIDO                  │
    │     (Status: SUBMITTED)                  │
    └────────────────────┬─────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────┐
    │  ¿Tipo de cáncer especificado?          │
    └────────────────────┬─────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                          │
          SÍ                         NO
           │                          │
           ▼                          ▼
    ┌──────────────┐         ┌────────────────┐
    │ Obtener      │         │ Asignar a     │
    │ MedicalGroup │         │ Coordinador   │
    │ por          │         │ General o      │
    │ tipo_cancer  │         │ Encola        │
    └──────┬───────┘         └────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │  ¿MedicalGroup existe y está activo?    │
    └────────────────────┬─────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                          │
          SÍ                         NO
           │                          │
           ▼                          ▼
    ┌──────────────┐         ┌────────────────┐
    │ Continuar    │         │ Estado:        │
    │ con          │         │ "PENDIENTE"    │
    │ asignación   │         │ Notificar a    │
    │              │         │ coordinación   │
    └──────┬───────┘         └────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │  Obtener lista de candidatos             │
    │  (DoctorGroupMembership activos)         │
    │  • disponible_asignacion_auto = True     │
    │  • medico.estado = 'activo'              │
    │  • medico.disponible = True               │
    │  • casos_actuales < limite_mensual       │
    └────────────────────┬─────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────┐
    │  ¿Hay candidatos disponibles?            │
    └────────────────────┬─────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                          │
          SÍ                         NO
           │                          │
           ▼                          ▼
    ┌──────────────┐         ┌────────────────┐
    │ Calcular     │         │ Estado:        │
    │ scores para  │         │ "PENDIENTE"    │
    │ cada         │         │ Notificar a    │
    │ candidato    │         │ coordinación   │
    └──────┬───────┘         └────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │  SELECCIONAR MEJOR CANDIDATO              │
    │  (Score menor = mejor)                   │
    │                                           │
    │  Score = (ponderación × carga) -          │
    │          ((1-ponderación) × antigüedad)   │
    │                                           │
    │  Si modo_estricto:                        │
    │  Score = -antigüedad                      │
    └────────────────────┬─────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────┐
    │  ASIGNAR CASO                            │
    │  • caso.doctor = medico.usuario          │
    │  • caso.responsable = medico              │
    │  • caso.medical_group = grupo            │
    │  • caso.status = 'ASSIGNED'              │
    │  • caso.assigned_at = now()               │
    └────────────────────┬─────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────┐
    │  REGISTRAR AUDITORÍA                     │
    │  AsignacionAuditLog.objects.create(       │
    │      caso=caso,                          │
    │      medico_seleccionado=medico,         │
    │      decision='asignado',                │
    │      score_final=...,                    │
    │      ...                                 │
    │  )                                       │
    └────────────────────┬─────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────┐
    │  ENVIAR NOTIFICACIONES                  │
    │  • Email al médico asignado             │
    │  • Notificación in-app                   │
    │  • Notificar coordinador del grupo      │
    └──────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    CÁLCULO DE SCORES                                       │
└─────────────────────────────────────────────────────────────────────────────┘

Para cada médico candidato, se calculan los siguientes scores:

1. SCORE DE CARGA (0-1, menor es mejor)
   ─────────────────────────────────────
   score_carga = casos_actuales / max_casos_mes
   
   Ejemplo:
   • Dr. Pérez: 3 casos / 10 máx = 0.30
   • Dr. García: 7 casos / 10 máx = 0.70
   • Dr. López:  0 casos / 10 máx = 0.00  ← MEJOR

2. SCORE DE ANTIGÜEDAD (0-1, mayor es mejor)
   ─────────────────────────────────────────
   dias_activo = (hoy - fecha_ingreso).days
   score_antiguedad = min(1.0, dias_activo / 1825)  # 5 años máx
   
   Ejemplo:
   • Dr. Pérez: 1500 días = 0.82
   • Dr. García: 800 días  = 0.44
   • Dr. López:  200 días  = 0.11

3. SCORE COMPUESTO (configurable)
   ───────────────────────────────
   ponderacion = config.ponderacion_carga  # Default: 50%
   
   score_final = (ponderacion × score_carga) - ((1-ponderacion) × score_antiguedad)
   
   Ejemplo con ponderación 50%:
   • Dr. Pérez: (0.5 × 0.30) - (0.5 × 0.82) = 0.15 - 0.41 = -0.26
   • Dr. García: (0.5 × 0.70) - (0.5 × 0.44) = 0.35 - 0.22 = +0.13
   • Dr. López:  (0.5 × 0.00) - (0.5 × 0.11) = 0.00 - 0.06 = -0.06
   
   → Dr. Pérez tiene el score más bajo = MEJOR CANDIDATO

4. MODO ESTRICTO ROUND-ROBIN
   ──────────────────────────
   Si config.modo_estricto = True:
   
   score_final = -score_antiguedad  # Solo considera antigüedad
   
   → El más antiguo recibe el caso (orden de llegada)

CONFIGURACIÓN (AlgoritmoConfig):
────────────────────────────────
• ponderacion_carga: 50 (porcentaje)
• modo_estricto: False
• limite_mensual_por_medico: 10
• respetar_disponibilidad: True
```

### 5.5 Flujo 5: Cancelación de Caso

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FLUJO: CANCELACIÓN DE CASO                             │
└─────────────────────────────────────────────────────────────────────────────┘

1. SOLICITUD DE CANCELACIÓN
   │
   ├── Por Paciente: /patients/casos/{case_id}/cancelar/
   ├── Por Administrador: /admin/casos/{case_id}/cancelar/
   │
   └── REQUISITOS:
        ├── Estado actual != 'CLOSED'
        ├── Estado actual != 'CANCELLED'
        └── Razón de cancelación (obligatoria)

2. PROCESAMIENTO
   │
   └── case.cancelar_caso()  # FSM: * → CANCELLED
           │
           ├── status = 'CANCELLED'
           ├── Motivo guardado en CaseAuditLog
           └── Notifica a todas las partes

3. NOTIFICACIONES
   │
   ├── Si estaba asignado: Notificar al médico
   ├── Si estaba en MDT: Notificar a miembros del comité
   └── Si tenía documentos: Archivar (no eliminar)

VISUALIZACIÓN:
   • Estado: "CANCELLED" con motivo
   • Paciente puede ver pero no modificar
   • Administrador mantiene historial
```

---

## 6. SISTEMA DE NOTIFICACIONES

### 6.1 Tipos de Notificaciones

| Tipo | Destinatario | Trigger | Canal |
|------|--------------|---------|-------|
| `asignacion_caso` | Médico | Caso asignado automáticamente | In-app + Email |
| `nueva_opinion` | Coordinator | Nueva opinión de miembro MDT | In-app |
| `recordatorio_voto` | Miembros MDT | Votación abierta, miembros sin votar | In-app + Email |
| `votacion_cerrada` | Todos MDT | Coordinator cierra votación | In-app |
| `informe_disponible` | Paciente | Informe final generado | In-app + Email |
| `caso_actualizado` | Médico/Paciente | Cambio de estado | In-app |
| `documento_subido` | Médico/Paciente | Nuevo documento añadido | In-app |

### 6.2 Flujo de Notificaciones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO: ENVÍO DE NOTIFICACIONES                           │
└─────────────────────────────────────────────────────────────────────────────┘

1. EVENTO DISPARA NOTIFICACIÓN
   │
   ├── Signals Django (post_save, post_delete)
   ├── Vistas Django (al completar acciones)
   └── Tareas Celery (programadas)
   │
   ▼
2. CREACIÓN DE NOTIFICACIÓN IN-APP
   │
   └── Notification.objects.create(
           receptor=user,
           tipo='...',
           titulo='...',
           mensaje='...',
           enlace='/ruta/a/accion/',
           caso_id=case.case_id
       )
   │
   ▼
3. CREACIÓN DE EMAIL (cola)
   │
   └── EmailService.create_and_queue_email(
           recipient=user.email,
           template_name='...',
           context={...},
           subject='...'
       )
       │
       ├── Crea EmailLog (status='PENDING')
       ├── Encola tarea Celery: send_email_task.delay(email_log.id)
       └── Return email_log
   │
   ▼
4. PROCESAMIENTO POR CELERY
   │
   └── send_email_task(email_log_id)
           │
           ├── Obtiene EmailLog
           ├── Renderiza template Django
           ├── Envía via SMTP (configurado en settings)
           │
           ├── Si éxito:
           │       └── email_log.mark_sent()
           │
           └── Si error:
                   ├── email_log.mark_failed(error)
                   └── Retry (hasta 3 intentos)

5. VISUALIZACIÓN EN INTERFAZ
   │
   ├── Navbar: Campana de notificaciones con contador
   ├── Bell icon: /notifications/
   └── Notificaciones leídas: Se marcar automáticamente al hacer clic
```

### 6.3 Plantillas de Email

El sistema usa Django templates para emails:

| Template | Uso |
|----------|-----|
| `emails/verify_email.html` | Verificación de email |
| `emails/password_reset.html` | Recuperación de contraseña |
| `emails/nuevo_caso_asignado.html` | Caso asignado a médico |
| `emails/informe_disponible.html` | Informe final disponible |
| `emails/doctor_invite.html` | Invitación a médico |

---

## 7. ALGORITMO DE ASIGNACIÓN AUTOMÁTICA

### 7.1 Configuración del Algoritmo

El algoritmo se configura mediante el modelo [`AlgoritmoConfig`](apps/cases/mdt_models.py):

```python
class AlgoritmoConfig(models.Model):
    nombre = models.CharField(max_length=100)
    ponderacion_carga = models.PositiveIntegerField(default=50)  # % peso carga
    modo_estricto = models.BooleanField(default=False)  # Round-robin puro
    limite_mensual_por_medico = models.PositiveIntegerField(default=10)
    respetar_disponibilidad = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
```

### 7.2 Criterios de Selección

1. **Disponibilidad del médico**: `disponible_segundas_opiniones = True`
2. **Estado activo**: `estado = 'activo'`
3. **Límite mensual**: `casos_actuales < max_casos_mes`
4. **Membresía activa**: En MedicalGroup con `disponible_asignacion_auto = True`

### 7.3 Override Manual

El administrador puede asignar manualmente un caso a un médico específico:

```python
AssignmentService.asignar_caso(
    caso=case,
    override_medico=medico,
    override_por=admin_user,
    override_justificacion='Caso especial requiere especialista específico'
)
```

---

## 8. SISTEMA DE COMITÉS MULTIDISCIPLINARIOS (MDT)

### 8.1 Estructura de Comités

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  ESTRUCTURA JERÁRQUICA DE COMITÉS                           │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌───────────────────────┐
                         │   INSTITUCIÓN         │
                         │   (Hospital/Centro)   │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
         ┌──────────────────┐ ┌─────────────┐ ┌─────────────┐
         │ Comité de Pulmón │ │ Comité Mama │ │ Comité ...  │
         │ (MedicalGroup)   │ │ (Medical-   │ │ (Medical-   │
         │                  │ │  Group)     │ │  Group)     │
         └────────┬─────────┘ └──────┬──────┘ └──────┬──────┘
                  │                   │                │
         ┌────────┴─────────┐ ┌──────┴──────┐ ┌──────┴──────┐
         │   Miembros MDT    │ │  Miembros   │ │  Miembros   │
         │                   │ │    MDT      │ │    MDT      │
         │ ┌───────────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │
         │ │ Coordinador   │ │ │ │ Coord.  │ │ │ │ Coord.  │ │
         │ │ (Dr. Pérez)   │ │ │ │         │ │ │ │         │ │
         │ └───────────────┘ │ └─────────┘ │ └─────────┘ │
         │ ┌───────────────┐ │ ┌─────────┐ │ ┌─────────┐ │
         │ │ Miembro Senior│ │ │ Miembro  │ │ │ Miembro  │ │
         │ │ (Dr. García)  │ │ │ Senior   │ │ │ Senior   │ │
         │ └───────────────┘ │ └─────────┘ │ └─────────┘ │
         │ ┌───────────────┐ │ ┌─────────┐ │ ┌─────────┐ │
         │ │ Miembro Regular│ │ │Regular  │ │ │Regular  │ │
         │ │ (Dr. López)   │ │ │         │ │ │         │ │
         │ └───────────────┘ │ └─────────┘ │ └─────────┘ │
         └──────────────────┘ └─────────────┘ └─────────────┘
```

### 8.2 Roles en el Comité

| Rol | Código | Permisos |
|-----|--------|----------|
| Coordinador | `coordinador` | Iniciar/cerrar votación, redactar propuesta, asignar casos |
| Miembro Senior | `miembro_senior` | Votar, comentar, proponer |
| Miembro Regular | `miembro_regular` | Votar, comentar |
| Residente | `residente` | Solo observación (no vota) |
| Invitado | `invitado` | Voto consultivo (configurable) |

### 8.3 Workflow de Consenso Formal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW DE CONSENSO MDT                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   INICIO     │
    │ (Caso nuevo  │
    │ asignado)    │
    └──────┬───────┘
           │
           ▼
    ┌─────────────────────────────────────────────┐
    │              FASE: DISCUSIÓN               │
    │  ┌───────────────────────────────────────┐ │
    │  │ • Chat grupal MDT                     │ │
    │  │ • Documentos compartidos              │ │
    │  │ • Presencia en tiempo real            │ │
    │  │ • Comentarios privados entre miembros │ │
    │  └───────────────────────────────────────┘ │
    └────────────────────┬──────────────────────┘
                         │
                         │ [Coordinador inicia propuesta]
                         ▼
    ┌─────────────────────────────────────────────┐
    │              FASE: PROPUESTA               │
    │  ┌───────────────────────────────────────┐ │
    │  │ • Coordinador redacta borrador        │ │
    │  │ • Versiones numeradas                 │ │
    │  │ • Miembros pueden comentar            │ │
    │  └───────────────────────────────────────┘ │
    └────────────────────┬──────────────────────┘
                         │
                         │ [Coordinador abre votación]
                         ▼
    ┌─────────────────────────────────────────────┐
    │              FASE: VOTACIÓN                │
    │  ┌───────────────────────────────────────┐ │
    │  │ • Votos: Aprueba / Aprueba mod       │ │
    │  │           Contraindicado / Alternativa │ │
    │  │           Abstiene                    │ │
    │  │ • Justificación obligatoria           │ │
    │  │ • Votos visibles tras cerrar           │ │
    │  └───────────────────────────────────────┘ │
    └────────────────────┬──────────────────────┘
                         │
                         │ [Conteo de votos]
                         ▼
              ┌──────────┴──────────┐
              │                     │
          ¿MAYORÍA?            ¿MAYORÍA?
              │                     │
             SÍ                    NO
              │                     │
              ▼                     ▼
    ┌─────────────────┐   ┌─────────────────────┐
    │    CONSENSO     │   │      DISENSO        │
    │ (fase=CONSENSO) │   │  (fase=DISENSO)     │
    └────────┬────────┘   └──────────┬──────────┘
             │                      │
             │                      ├──────────────────┐
             │                      │ OpinionDisidente  │
             │                      │ registrada para   │
             │                      │ cada disidente    │
             │                      └──────────────────┘
             ▼
    ┌─────────────────────────────────────────────┐
    │  ✓ Nivel de evidencia calculado            │
    │  ✓ Informe final generado                  │
    │  ✓ Caso cerrado                            │
    └─────────────────────────────────────────────┘
```

---

## 9. ESTADOS DE LOS CASOS Y TRANSICIONES

### 9.1 Máquina de Estados Finitos (FSM)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DIAGRAMA DE ESTADOS DEL CASO                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │    DRAFT    │
                              │  (Borrador) │
                              └──────┬──────┘
                                     │
                                     │ [Paciente envía]
                                     ▼
                              ┌─────────────┐
         ┌────────────────────│  SUBMITTED  │◄─────────────────┐
         │                    │  (Enviado)  │                  │
         │                    └──────┬──────┘                  │
         │                           │                         │
         │                           │ [Algoritmo asigna]       │
         │                           ▼                         │
         │                    ┌─────────────┐                  │
         │                    │  ASSIGNED   │                  │
         │                    │ (Asignado)  │                  │
         │                    └──────┬──────┘                  │
         │                           │                         │
         │                           │ [Médico acepta]         │
         │                           ▼                         │
         │                    ┌─────────────┐                  │
         │                    │ PROCESSING   │                  │
         │                    │(Procesando) │                  │
         │                    └──────┬──────┘                  │
         │                           │                         │
         │            ┌──────────────┼──────────────┐         │
         │            │              │              │         │
         │            ▼              ▼              ▼         │
         │    ┌────────────┐ ┌───────────┐ ┌─────────────┐   │
         │    │ Solicitar  │ │  Iniciar  │ │  Cerrar sin │   │
         │    │ info       │ │   MDT     │ │  MDT        │   │
         │    └─────┬──────┘ └─────┬─────┘ └──────┬──────┘   │
         │          │              │              │          │
         │          ▼              ▼              ▼          │
         │   ┌────────────┐ ┌─────────────┐ ┌────────────┐  │
         │   │CLARIFICATION│ │MDT_IN_PROGRESS│ │OPINION_   │  │
         │   │  _NEEDED   │ │(En análisis) │ │ COMPLETE   │  │
         │   └─────┬──────┘ └──────┬──────┘ └──────┬─────┘  │
         │         │                │              │        │
         │         │    ┌───────────┴───────────┐  │        │
         │         │    │                       │  │        │
         │         │    ▼                       ▼  │        │
         │         │ ┌──────────────────┐ ┌──────────┐    │
         │         └──│  MDT_COMPLETED   │ │CLARIFIED │    │
         │            │ (Discusión MDT   │ │(Info     │    │
         │            │   cerrada)        │ │recibida) │    │
         │            └────────┬─────────┘ └────┬─────┘    │
         │                     │                 │          │
         │                     │ [Iniciar informe]          │
         │                     ▼                         │
         │            ┌─────────────────┐                 │
         │            │   REPORT_DRAFT  │                 │
         │            │ (Informe en     │                 │
         │            │  redacción)      │                 │
         │            └────────┬─────────┘                 │
         │                     │                            │
         │                     │ [Completar informe]        │
         │                     ▼                            │
         │            ┌────────────────────┐               │
         └────────────►│  REPORT_COMPLETED │               │
         │            │ (Informe completado)│               │
         │            └──────────┬──────────┘               │
         │                      │                           │
         │                      │ [Cerrar caso]              │
         │                      ▼                           │
         │            ┌──────────────────┐                  │
         │            │      CLOSED      │◄─────────────────┘
         │            │     (Cerrado)    │
         │            └──────────────────┘
         │
         │ [Cancelar en cualquier momento]
         ▼
   ┌─────────────┐
   │ CANCELLED   │
   │(Cancelado)  │
   └─────────────┘
```

### 9.2 Tabla de Estados

| Estado | Código FSM | Fase MDT | Significado | Acciones Permitidas |
|--------|------------|----------|-------------|---------------------|
| Borrador | `DRAFT` | - | Caso en creación | Editar, Eliminar |
| Enviado | `SUBMITTED` | - | Caso enviado, esperando asignación | Ver, Asignar |
| Asignado | `ASSIGNED` | - | Asignado a médico | Revisar, Iniciar MDT |
| Procesando | `PROCESSING` | - | Médico revisando documentos | Solicitar info, Emitir opinión |
| Esperando Info | `CLARIFICATION_NEEDED` | - | Paciente debe enviar más docs | Subir docs, Cancelar |
| En Análisis MDT | `MDT_IN_PROGRESS` | DISCUSIÓN/PROPUESTA/VOTACIÓN | Comité en discusión | Votar, Chat, Proponer |
| MDT Cerrado | `MDT_COMPLETED` | CONSENSO/DISENSO | Votación terminada | Redactar informe |
| Informe Redacción | `REPORT_DRAFT` | - | Responsable redactando | Editar informe |
| Informe Completado | `REPORT_COMPLETED` | - | Informe listo | Descargar, Cerrar caso |
| Opinion Completa | `OPINION_COMPLETE` | - | (Legacy) Opinión simple | Cerrar caso |
| Cerrado | `CLOSED` | - | Caso archivado | Solo ver |
| Cancelado | `CANCELLED` | - | Cancelado por usuario/admin | Solo ver |

---

## 10. SEGURIDAD Y CUMPLIMIENTO

### 10.1 Medidas de Seguridad Implementadas

| Aspecto | Implementación |
|---------|----------------|
| **Autenticación** | Django Auth con verificación de email obligatoria |
| **Contraseñas** | Hashing PBKDF2 ( Django default) |
| **Cifrado PHI** | `django-fernet-fields` en campos sensibles |
| **Permisos a nivel objeto** | `django-guardian` |
| **Auditoría** | `django-auditlog` en modelos críticos |
| **Protección CSRF** | Middleware nativo Django |
| **Headers de seguridad** | `django.middleware.security.SecurityMiddleware` |
| **Rate Limiting** | Configurable en vistas |

### 10.2 Datos Cifrados (PHI)

Los siguientes campos almacenan datos cifrados usando Fernet:

```python
# En PatientProfile
full_name = EncryptedCharField(max_length=255)
identity_document = EncryptedCharField(max_length=50)
phone_number = EncryptedCharField(max_length=20)
medical_history = EncryptedTextField()
current_treatment = EncryptedTextField()

# En Case
primary_diagnosis = EncryptedCharField(max_length=255)
description = EncryptedTextField()
```

### 10.3 Auditoría

Todas las acciones críticas se registran:

```python
CaseAuditLog.objects.create(
    case=case,
    user=user,
    action='create' | 'read' | 'update' | 'delete' | 
           'document_upload' | 'opinion_added' | 'clarification_requested',
    description='...',
    ip_address='192.168.1.1'
)
```

---

## 11. ENDPOINTS PRINCIPALES

### 11.1 Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/accounts/login/` | Página de login |
| POST | `/accounts/login/` | Procesar login |
| GET | `/accounts/register/` | Registro de usuario |
| POST | `/accounts/register/` | Crear cuenta |
| GET | `/accounts/verify/{token}/` | Verificar email |
| POST | `/accounts/password/reset/` | Solicitar reset |
| GET | `/accounts/logout/` | Cerrar sesión |

### 11.2 Portal Paciente

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/patients/dashboard/` | Dashboard del paciente |
| GET/POST | `/patients/solicitud/nueva/` | Crear solicitud |
| GET | `/patients/casos/` | Lista de casos |
| GET | `/patients/casos/{case_id}/` | Detalle de caso |
| POST | `/patients/casos/{case_id}/documentos/` | Subir documento |
| GET | `/patients/casos/{case_id}/descargar/{doc_id}/` | Descargar documento |

### 11.3 Portal Médico

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/doctors/dashboard/` | Dashboard del médico |
| GET | `/doctors/casos/` | Casos asignados |
| GET | `/doctors/casos/{case_id}/` | Detalle de caso |
| POST | `/doctors/casos/{case_id}/opinion/` | Emitir opinión |
| POST | `/doctors/casos/{case_id}/iniciar-mdt/` | Iniciar análisis MDT |
| POST | `/doctors/casos/{case_id}/votar/` | Emitir voto |
| POST | `/doctors/casos/{case_id}/cerrar-votacion/` | Cerrar votación |
| POST | `/doctors/casos/{case_id}/informe/` | Generar informe final |

### 11.4 Administración

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/administracion/dashboard/` | Panel admin |
| GET | `/administracion/casos/` | Lista de casos global |
| POST | `/administracion/casos/{case_id}/asignar/` | Asignar manualmente |
| GET/POST | `/administracion/medicos/` | Gestionar médicos |
| GET/POST | `/administracion/comites/` | Gestionar comités |
| GET/POST | `/administracion/configuracion/` | Configuración sistema |

### 11.5 API REST

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login API |
| GET | `/api/cases/` | Listar casos |
| POST | `/api/cases/` | Crear caso |
| GET | `/api/cases/{id}/` | Ver caso |
| GET | `/api/medicos/casos/` | Casos del médico |
| GET | `/api/notifications/` | Notificaciones |

---

## 12. RESUMEN DE FUNCIONALIDADES

### 12.1 Para Pacientes

| Funcionalidad | Descripción |
|---------------|-------------|
| ✅ Registro y verificación por email | Crear cuenta, verificar email antes de acceder |
| ✅ Perfil de paciente | Datos personales y médicos cifrados |
| ✅ Crear solicitud de segunda opinión | Formulario multi-paso con carga de documentos |
| ✅ Subir documentos médicos | PDFs, imágenes, resultados de laboratorio |
| ✅ Seguimiento de casos | Ver estado actual de cada solicitud |
| ✅ Descargar informe final | PDF con recomendaciones del comité |
| ✅ Notificaciones | Email y in-app sobre avances del caso |

### 12.2 Para Médicos

| Funcionalidad | Descripción |
|---------------|-------------|
| ✅ Invitación por administrador | Email de invitación con token |
| ✅ Perfil profesional | Especialidades, registro médico, disponibilidad |
| ✅ Dashboard de casos | Lista de casos asignados |
| ✅ Revisión de casos | Ver datos y documentos del paciente |
| ✅ Emitir opinión individual | Voto y comentario sobre el caso |
| ✅ Participar en MDT | Chat grupal, propuestas, votación |
| ✅ Coordinar comités | Iniciar/cerrar votaciones, redactar informes |
| ✅ Generar informe final | Consenso estructurado con recomendaciones |
| ✅ Configuración de disponibilidad | Límites de casos, estados |

### 12.3 Para Administradores

| Funcionalidad | Descripción |
|---------------|-------------|
| ✅ Panel de control | Vista general del sistema |
| ✅ Gestión de usuarios | Crear, editar, desactivar usuarios |
| ✅ Gestión de médicos | Especialidades, comités, disponibilidad |
| ✅ Crear/editar comités MDT | MedicalGroup, miembros, configuraciones |
| ✅ Configuración del algoritmo | Ponderación, límites, modo estricto |
| ✅ Asignación manual | Override del algoritmo automático |
| ✅ Ver todos los casos | Acceso global a la plataforma |
| ✅ Reportes y estadísticas | Casos por estado, médicos, comités |
| ✅ Logs de auditoría | Historial de todas las acciones |

### 12.4 Características Técnicas

| Característica | Descripción |
|----------------|-------------|
| 🔐 **Cifrado de datos PHI** | Campos sensibles cifrados con Fernet |
| 📊 **Auditoría completa** | Registro de todas las acciones |
| 🔄 **Tareas asíncronas** | Celery para emails y procesamiento |
| 📱 **Diseño responsive** | Tailwind CSS compatible con móviles |
| 📨 **Sistema de notificaciones** | In-app + Email con templates |
| 🔔 **WebSocket (preparado)** | Presencia en tiempo real |
| 📄 **Generación de PDFs** | Informes finales en PDF |
| 🔍 **Búsqueda y filtros** | Casos por estado, fecha, médico |
| 📈 **Métricas** | Casos activos, tiempos de resolución |

---

## ANEXO: Glosario de Términos

| Término | Definición |
|---------|------------|
| **MDT** | Multidisciplinary Team - Comité multidisciplinario |
| **PHI** | Protected Health Information - Información de salud protegida |
| **FSM** | Finite State Machine - Máquina de estados finitos |
| **M2M** | Many-to-Many - Relación muchos a muchos |
| **FK** | Foreign Key - Clave foránea |
| **SOP** | Segunda Opinión Profesional |

---

*Documento generado automáticamente. Última actualización: 2026-03-09*

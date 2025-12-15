from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    responsibles = models.ManyToManyField(User, related_name='specialties', blank=True)
    current_index = models.PositiveIntegerField(default=0)  # For round robin

    def __str__(self):
        return self.name

    def get_next_responsible(self):
        responsibles = list(self.responsibles.all())
        if not responsibles:
            return None
        responsible = responsibles[self.current_index % len(responsibles)]
        self.current_index = (self.current_index + 1) % len(responsibles)
        self.save()
        return responsible

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('responsable', 'Responsable del Caso'),
        ('mdt_member', 'Miembro del MDT'),
        ('coordinator', 'Coordinador'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    specialties = models.ManyToManyField(Specialty, related_name='profiles', blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Case(models.Model):
    STATUS_CHOICES = [
        ('pending_assignment', 'Pendiente de Asignación'),
        ('assigned', 'Asignado'),
        ('waiting_info', 'Esperando Info del Paciente'),
        ('mdt_analysis', 'En Análisis por MDT'),
        ('report_drafting', 'Informe en Redacción'),
        ('concluded', 'Concluido – Informe Enviado'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_assignment')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new and self.status == 'pending_assignment':
            responsible = self.specialty.get_next_responsible()
            if responsible:
                self.assigned_to = responsible
                self.status = 'assigned'
        super().save(*args, **kwargs)
        if is_new and self.assigned_to:
            Assignment.objects.create(case=self, assigned_to=self.assigned_to)

    def assign_responsible(self):
        if self.status == 'pending_assignment':
            responsible = self.specialty.get_next_responsible()
            if responsible:
                self.assigned_to = responsible
                self.status = 'assigned'
                self.save()
                return True
        return False

class Assignment(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Asignación {self.case} a {self.assigned_to}"

class CallLog(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    caller = models.ForeignKey(User, on_delete=models.CASCADE)
    call_date = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()

    def __str__(self):
        return f"Llamada {self.caller} - {self.case} ({self.call_date})"

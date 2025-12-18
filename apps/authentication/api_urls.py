from django.urls import path
from . import api_views

urlpatterns = [
    path('admin/doctors/invite/', api_views.DoctorInviteAPIView.as_view(), name='api_doctor_invite'),
    path('auth/complete_registration/', api_views.CompleteRegistrationAPIView.as_view(), name='api_complete_registration'),
]

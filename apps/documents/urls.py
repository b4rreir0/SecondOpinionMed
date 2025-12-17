from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('presigned-upload/', views.get_presigned_upload, name='presigned_upload'),
]

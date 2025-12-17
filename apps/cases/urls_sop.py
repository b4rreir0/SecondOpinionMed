from django.urls import path
from . import views_sop

urlpatterns = [
    path('sop/start/', views_sop.start_sop, name='sop_start'),
    path('sop/step-1/', views_sop.sop_step1, name='sop_step1'),
    path('sop/step-2/', views_sop.sop_step2, name='sop_step2'),
    path('sop/step-3/', views_sop.sop_step3, name='sop_step3'),
    path('sop/step-4/', views_sop.sop_step4, name='sop_step4'),
]

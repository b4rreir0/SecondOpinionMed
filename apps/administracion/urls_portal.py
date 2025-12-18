from django.urls import path
from . import portal_views

app_name = 'administracion'

urlpatterns = [
    path('login/', portal_views.AdminLoginView.as_view(), name='portal_login'),
    path('logout/', portal_views.AdminLogoutView.as_view(), name='portal_logout'),
    path('', portal_views.AdminPanelView.as_view(), name='portal_panel'),
    path('invite/', portal_views.InviteDoctorView.as_view(), name='portal_invite'),
]

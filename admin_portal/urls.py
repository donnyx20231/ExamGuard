from django.urls import path
from . import views

app_name = 'admin_portal'

urlpatterns = [
    path('login/', views.admin_login_page, name='admin_login_page'),
    path('dashboard/', views.admin_dashboard_page, name='admin_dashboard_page'),
    path('generate_code/', views.generate_code, name='generate_code'),
    path('add_user/', views.add_user, name='add_user'),
] 
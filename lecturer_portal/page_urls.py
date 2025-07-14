from django.urls import path
from . import views

app_name = 'lecturer_portal'

urlpatterns = [
    path('login/', views.lecturer_login_page, name='lecturer_login_page'),
    path('dashboard/', views.lecturer_dashboard_page, name='lecturer_dashboard_page'),
] 
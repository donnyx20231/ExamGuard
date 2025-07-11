from django.urls import path
from . import views

app_name = 'lecturer_portal_api' # Using a distinct app_name for clarity if you have web views too

urlpatterns = [
    path('login/', views.lecturer_code_login_api, name='lecturer_login_api'),
    path('logout/', views.lecturer_logout_api, name='lecturer_logout_api'),
    # We will add more paths for other functionalities here
]
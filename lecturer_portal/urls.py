from django.urls import path
from . import views

app_name = 'lecturer_portal_api' # Using a distinct app_name for clarity if you have web views too

urlpatterns = [
    path('login/', views.lecturer_code_login_api, name='lecturer_login_api'),
    path('logout/', views.lecturer_logout_api, name='lecturer_logout_api'),
    # We will add more paths for other functionalities here
]

urlpatterns += [
    path('upload-questions/', views.upload_questions_api, name='upload_questions_api'),
    path('exam/<int:exam_id>/update/', views.update_exam_details_api, name='update_exam_details_api'),
    path('exam/<int:exam_id>/attempts/', views.get_exam_attempts_api, name='get_exam_attempts_api'),
    path('attempt/<int:attempt_id>/grant-grace/', views.grant_grace_login_api, name='grant_grace_login_api'),
]
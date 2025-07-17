from django.urls import path
from . import views

app_name = 'lecturer_portal_api'

urlpatterns = [
    path('login/', views.lecturer_code_login_api, name='lecturer_login_api'),
    path('logout/', views.lecturer_logout_api, name='lecturer_logout_api'),
    path('upload-questions/', views.upload_questions_api, name='upload_questions_api'),
    path('exam/<int:exam_id>/update/', views.update_exam_details_api, name='update_exam_details_api'),
    path('exam/<int:exam_id>/attempts/', views.get_exam_attempts_api, name='get_exam_attempts_api'),
    path('exam/<int:exam_id>/download-results/', views.download_results_excel_api, name='download_results_excel_api'),
    path('exam/<int:exam_id>/', views.delete_exam_api, name='delete_exam_api'),
    path('attempt/<int:attempt_id>/grant-grace/', views.grant_grace_login_api, name='grant_grace_login_api'),
]
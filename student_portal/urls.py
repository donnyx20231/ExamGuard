from django.urls import path
from .views import student_login, fetch_exam_questions, submit_answers, log_cheating_attempt

app_name = 'student_portal'

urlpatterns = [
    path('login/', student_login, name='student_login'),
    path('exam/<str:course_code>/questions/', fetch_exam_questions, name='fetch_exam_questions'),
    path('exam/<str:course_code>/submit/', submit_answers, name='submit_answers'),
    path('exam/<str:course_code>/log_cheating_attempt/', log_cheating_attempt, name='log_cheating_attempt'),
]
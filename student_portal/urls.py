from django.urls import path
from .views import student_login_page, student_login, fetch_exam_questions, submit_answers, log_cheating_attempt
from django.shortcuts import render

app_name = 'student_portal'

urlpatterns = [
    path('login/', student_login_page, name='student_login_page'),
    path('api/login/', student_login, name='student_login_api'),
    path('exam/<str:course_code>/', lambda request, course_code: render(request, 'student_portal/exam.html', {'course_code': course_code}), name='exam_page'),
    path('api/exam/<str:course_code>/questions/', fetch_exam_questions, name='fetch_exam_questions'),
    path('api/exam/<str:course_code>/submit/', submit_answers, name='submit_answers'),
    path('api/exam/<str:course_code>/log_cheating_attempt/', log_cheating_attempt, name='log_cheating_attempt'),
]
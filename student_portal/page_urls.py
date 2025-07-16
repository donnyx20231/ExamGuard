from django.urls import path
from .views import student_login_page
from django.shortcuts import render

app_name = 'student_portal_pages'

urlpatterns = [
    path('login/', student_login_page, name='student_login_page'),
    path('exam/<str:course_code>/<int:attempt_id>/', lambda request, course_code, attempt_id: render(request, 'student_portal/exam.html', {'course_code': course_code, 'attempt_id': attempt_id}), name='exam_page'),
] 
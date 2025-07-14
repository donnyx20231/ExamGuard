from django.contrib import admin
from .models import Student, ExamAttempt, StudentAnswer

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'matric_number')
    search_fields = ('name', 'matric_number')

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_info', 'exam_info', 'start_time', 'submission_time', 'score', 'grace_login_granted')
    list_filter = ('exam__title', 'grace_login_granted', 'submission_time')
    search_fields = ('student__name', 'student__matric_number', 'exam__title')
    raw_id_fields = ('student', 'exam') # For easier selection

    def student_info(self, obj):
        return f"{obj.student.name} ({obj.student.matric_number})"
    student_info.short_description = 'Student'

    def exam_info(self, obj):
        return obj.exam.title
    exam_info.short_description = 'Exam'

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam_attempt_info', 'question_text_preview', 'marks_awarded')
    raw_id_fields = ('exam_attempt', 'question')
    list_filter = ('exam_attempt__exam__title',)
    search_fields = (
        'exam_attempt__student__name', 
        'exam_attempt__student__matric_number', 
        'question__question_text'
    )

    def exam_attempt_info(self, obj):
        return f"Attempt ID: {obj.exam_attempt.id} by {obj.exam_attempt.student.matric_number}"
    exam_attempt_info.short_description = "Exam Attempt"

    def question_text_preview(self, obj):
        return obj.question.question_text[:50] + "..." if obj.question else "N/A"
    question_text_preview.short_description = "Question Preview"

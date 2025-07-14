from django.contrib import admin
from .models import Exam, Question, Option

class OptionInline(admin.TabularInline):
    model = Option
    extra = 3

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'exam', 'question_type', 'marks')
    list_filter = ('question_type', 'exam__title')
    search_fields = ('question_text', 'exam__title')
    inlines = [OptionInline]
    fieldsets = (
        (None, {'fields': ('exam', 'question_text', 'question_type', 'marks')}),
        ('Answer Key (for non-MCQ)', {'fields': ('lecturer_answer_key',)}),
    )

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_code', 'lecturer_user', 'start_time', 'end_time', 'duration_minutes', 'is_active')
    list_filter = ('is_active', 'lecturer_user', 'start_time')
    search_fields = ('title', 'course_code', 'lecturer_user__username')
    raw_id_fields = ('lecturer_user',)


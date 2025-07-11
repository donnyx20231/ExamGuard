from django.db import models
from django.contrib.auth.models import User
# If LecturerCode is in admin_portal, you might need this import if you decide to link directly
# from admin_portal.models import LecturerCode 

class Exam(models.Model):
    title = models.CharField(max_length=255)
    # Assuming a User account is created for the lecturer by an admin
    # and this lecturer_user is then associated with teaching/managing this exam.
    lecturer_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams_managed', limit_choices_to={'is_staff': False, 'is_superuser': False})
    course_code = models.CharField(max_length=100, help_text="Course code, e.g., CS101. Used by students to find the exam.")
    
    # Exam window: when the exam can be started
    start_time = models.DateTimeField(help_text="When the exam becomes available for students to start.")
    end_time = models.DateTimeField(help_text="When the exam is no longer available for students to start.")
    
    duration_minutes = models.PositiveIntegerField(help_text="Duration of the exam in minutes once a student starts.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=False, help_text="Lecturer activates this to make it visible/takeable by students (within start/end time).")

    def __str__(self):
        return f"{self.title} ({self.course_code}) - Lecturer: {self.lecturer_user.username}"

    class Meta:
        verbose_name = "Exam"
        verbose_name_plural = "Exams"
        # A lecturer shouldn't have two active exams with the same course code simultaneously
        # However, this might be too restrictive if old exams need to be kept with same course code.
        # Consider deactivating old exams or adding a semester/year field if course codes are reused.
        # For now, this ensures an active exam for a course code by a lecturer is unique.
        # unique_together = [['lecturer_user', 'course_code', 'is_active']] # This might be too complex, let's simplify for now.
        # Let's ensure that a course_code for an *active* exam is unique system-wide or per lecturer.
        # For simplicity, let's assume course_code should be fairly unique for active exams.


class Question(models.Model):
    EXAM_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('fill_in_the_blanks', 'Fill in the Blanks'),
        ('essay', 'Essay / Short Answer'),
    )
    exam = models.ForeignKey(Exam, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField(help_text="For 'Fill in the Blanks', use underscores for blank spaces, e.g., 'The capital of France is __Paris__.')")
    question_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPES,
        default='multiple_choice'
    )
    marks = models.PositiveIntegerField(default=1)
    lecturer_answer_key = models.TextField(blank=True, null=True, help_text="Correct answer for fill-in-the-blanks or keywords/ideal answer for essays.")

    def __str__(self):
        return f"{self.get_question_type_display()}: {self.question_text[:50]}... (Exam: {self.exam.title})"

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"

class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.option_text} ({'Correct' if self.is_correct else 'Incorrect'}) for QID: {self.question.id}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['question'], condition=models.Q(is_correct=True), name='unique_correct_option_per_question')
        ]
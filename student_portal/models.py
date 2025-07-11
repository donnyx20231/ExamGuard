from django.db import models
from django.contrib.auth.models import User # Not directly used for Student model here, but good to have if needed later
from lecturer_portal.models import Exam, Question # Import from other apps

class Student(models.Model):
    matric_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    # email = models.EmailField(unique=True, blank=True, null=True) # Optional, as per earlier discussion

    def __str__(self):
        return f"{self.name} ({self.matric_number})"

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

class ExamAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    
    start_time = models.DateTimeField(auto_now_add=True, help_text="Actual time student started this attempt.")
    submission_time = models.DateTimeField(null=True, blank=True, help_text="Actual time student submitted.")
    score = models.IntegerField(null=True, blank=True, help_text="Total score for this attempt.")
    
    grace_login_granted = models.BooleanField(default=False, help_text="Set by lecturer to allow re-entry or late start.")
    # last_active_time = models.DateTimeField(auto_now=True, help_text="Last time any activity was registered for this attempt.") # Useful for monitoring
    
    # This field will store the precise moment the student's time for this attempt will expire.
    # It will be calculated as: student_start_time + exam.duration_minutes.
    attempt_deadline = models.DateTimeField(null=True, blank=True, help_text="Calculated deadline for this specific attempt.")

    def __str__(self):
        return f"Attempt by {self.student.matric_number} for {self.exam.title} - Score: {self.score if self.score is not None else 'Pending'}"

    class Meta:
        verbose_name = "Exam Attempt"
        verbose_name_plural = "Exam Attempts"
        unique_together = [['student', 'exam']] # A student should only have one main attempt per exam

class StudentAnswer(models.Model):
    exam_attempt = models.ForeignKey(ExamAttempt, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    answer_text = models.TextField(blank=True, null=True)
    marks_awarded = models.IntegerField(default=0, help_text="Marks awarded for this specific answer.")

    def __str__(self):
        return f"Answer by {self.exam_attempt.student.matric_number} for Q: {self.question.id} - Marks: {self.marks_awarded}"

    class Meta:
        verbose_name = "Student Answer"
        verbose_name_plural = "Student Answers"
        unique_together = [['exam_attempt', 'question']] # One answer per question per attempt

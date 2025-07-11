from django.db import models
from django.contrib.auth.models import User
import uuid

class LecturerCode(models.Model):
    code = models.CharField(max_length=50, unique=True, blank=True)
    associated_admin = models.ForeignKey(User, related_name='generated_lecturer_codes', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_staff': True})
    lecturer_user = models.OneToOneField(User, related_name='access_code', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_staff': False, 'is_superuser': False})
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this code will no longer be valid for initial activation/login.")
    is_active = models.BooleanField(default=True, help_text="Overall status of this code/lecturer slot.")

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Code: {self.code} for {self.lecturer_user.username if self.lecturer_user else 'Unassigned Lecturer'}"

    class Meta:
        verbose_name = "Lecturer Access Code"
        verbose_name_plural = "Lecturer Access Codes"
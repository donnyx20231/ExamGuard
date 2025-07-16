from django.contrib import admin
from .models import LecturerCode
# from django.contrib.auth.models import User # Not strictly needed for basic registration
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # For more advanced User admin customization

@admin.register(LecturerCode)
class LecturerCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'get_lecturer_username', 'get_associated_admin_username', 'created_at', 'expires_at', 'is_active')
    search_fields = ('code', 'lecturer_user__username', 'associated_admin__username')
    list_filter = ('is_active', 'created_at', 'expires_at')
    raw_id_fields = ('lecturer_user', 'associated_admin') # Makes selecting users easier
    readonly_fields = ('created_at',)
    # If 'code' is always auto-generated on save and shouldn't be edited:
    # readonly_fields = ('created_at', 'code') 

    fieldsets = (
        (None, {'fields': ('code', 'is_active')}),
        ('User Association', {'fields': ('lecturer_user', 'associated_admin')}),
        ('Timestamps', {'fields': ('created_at', 'expires_at')}),
    )

    @admin.display(description='Lecturer User')
    def get_lecturer_username(self, obj):
        return obj.lecturer_user.username if obj.lecturer_user else "N/A"

    @admin.display(description='Associated Admin')
    def get_associated_admin_username(self, obj):
        return obj.associated_admin.username if obj.associated_admin else "N/A"

    # If you want the 'code' field to be pre-filled when adding a new LecturerCode in admin
    # and your model's save() method handles blank codes, this isn't strictly necessary here.
    # The model's save() method is a more robust place for auto-generation.

# Instructions for Admin User Management (for your reference):
# 1. To create an initial admin (superuser):
#    Run `python manage.py createsuperuser` in your terminal.
#    Follow the prompts.
#
# 2. To manage other admins/users:
#    - Log into the admin site (e.g., /admin/).
#    - Go to the "Users" section.
#    - You can add new users or edit existing ones.
#    - To make a user an admin:
#      - Set "Staff status" to checked (allows login to admin).
#      - Set "Superuser status" to checked (grants all permissions).
#      - Alternatively, assign them to an "Admin" group with specific permissions (more granular control).
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseBadRequest
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from admin_portal.models import LecturerCode
# We will need these models later for other functions
# from .models import Exam, Question
# from student_portal.models import ExamAttempt, StudentAnswer

# Attempt to import libraries for Word and Excel, handle if not found
try:
    from docx import Document
except ImportError:
    Document = None

try:
    import openpyxl
    from openpyxl.writer.excel import save_virtual_workbook # For sending Excel in HTTP response
except ImportError:
    openpyxl = None
    save_virtual_workbook = None


@csrf_exempt # For API endpoints, be mindful of CSRF implications if also serving web forms
def lecturer_code_login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code_value = data.get('code')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

        if not code_value:
            return JsonResponse({'error': 'Code is required.'}, status=400)

        try:
            lecturer_code_obj = LecturerCode.objects.get(code=code_value, is_active=True)
        except LecturerCode.DoesNotExist:
            return JsonResponse({'error': 'Invalid or inactive code.'}, status=403) # 403 Forbidden

        if lecturer_code_obj.expires_at and lecturer_code_obj.expires_at < timezone.now():
            lecturer_code_obj.is_active = False # Optionally deactivate expired codes
            lecturer_code_obj.save()
            return JsonResponse({'error': 'Code has expired.'}, status=403)

        if not lecturer_code_obj.lecturer_user:
            return JsonResponse({'error': 'Lecturer account not properly configured for this code.'}, status=500)
        
        if not lecturer_code_obj.lecturer_user.is_active:
            return JsonResponse({'error': 'Associated lecturer account is inactive.'}, status=403)

        # Log in the lecturer. This uses Django's session framework.
        # The user object must be authenticated by a backend or passed directly.
        # Since we trust the code here, we directly log in the associated user.
        login(request, lecturer_code_obj.lecturer_user)
        
        return JsonResponse({
            'message': 'Login successful.',
            'username': lecturer_code_obj.lecturer_user.username,
            'user_id': lecturer_code_obj.lecturer_user.id
        })
    
    return HttpResponseNotAllowed(['POST'])

@csrf_exempt # Ensure this is also a POST request if it modifies state
def lecturer_logout_api(request):
    if request.method == 'POST': # Good practice for logout to be a POST
        logout(request)
        return JsonResponse({'message': 'Logout successful.'})
    return HttpResponseNotAllowed(['POST'])

# We'll add more views for other functionalities later.

# Authentication check for other lecturer views
# This is a helper, actual protection will be via a decorator or middleware
def is_lecturer_authenticated(request):
    # A basic check: is the user authenticated and NOT a superuser/staff?
    # This implies they are a regular user, which in our context is a lecturer.
    # For more robust role checking, Django Groups are recommended.
    if request.user.is_authenticated:
        if not request.user.is_staff and not request.user.is_superuser:
            return True
    return False

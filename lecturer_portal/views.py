from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseBadRequest
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import traceback

from admin_portal.models import LecturerCode
from .models import Exam, Question, Option
from student_portal.models import ExamAttempt
from django.db import transaction
import re

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

@csrf_exempt
def upload_questions_api(request):
    if not is_lecturer_authenticated(request): # Make sure is_lecturer_authenticated is defined
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    if request.method == 'POST':
        if not Document:
            return JsonResponse({'error': 'MS Word parsing library (python-docx) not installed or not found.'}, status=500)

        exam_id = request.POST.get('exam_id')
        word_file = request.FILES.get('word_file')

        if not exam_id:
            return JsonResponse({'error': 'exam_id is required.'}, status=400)
        if not word_file:
            return JsonResponse({'error': 'Word file (word_file) is required.'}, status=400)

        try:
            exam = Exam.objects.get(id=exam_id, lecturer_user=request.user)
        except Exam.DoesNotExist:
            return JsonResponse({'error': 'Exam not found or you do not have permission to modify it.'}, status=404)

        print("--- Starting Question Parsing ---_DEBUG_EMAIL_REMOVED_") # DEBUG START
        try:
            document = Document(word_file)
            parsed_questions = 0
            with transaction.atomic():
                exam.questions.all().delete()

                current_question_text = None
                current_options = []
                current_answer_letter = None
                current_lecturer_answer_key = None
                question_type = 'multiple_choice' # This is the general default for the parser state
                is_next_question_essay = False # <--- ADD THIS NEW FLAG
                is_next_question_fill_in_the_blanks = False # <--- ADD THIS NEW FLAG

                for para_idx, para in enumerate(document.paragraphs):
                    text = para.text.strip()
                    print(f"DEBUG [{para_idx}]: Processing paragraph: '{text}'")

                    if not text:
                        continue

                    q_match = re.match(r"^\d+\.\s*(?:\d+\.\s*)?(.*)", text)
                    option_match = re.match(r"^([A-Za-z])\.\s+(.*)", text)
                    answer_match = re.match(r"^Answer:\s*([A-Za-z])", text, re.IGNORECASE)

                    # Header detection for question type switching
                    if text.lower() == 'fill in the blanks':
                        if current_question_text: # Save any previous question
                            _save_parsed_question(exam, current_question_text, question_type, current_options, current_answer_letter, current_lecturer_answer_key)
                            parsed_questions += 1
                            # Reset state for the header itself
                            current_question_text = None; current_options = []; current_answer_letter = None; current_lecturer_answer_key = None;
                        print("DEBUG: Header 'Fill In The Blanks' detected.")
                        is_next_question_fill_in_the_blanks = True
                        is_next_question_essay = False
                        question_type = 'fill_in_the_blanks' # Set current type expectation
                        continue
                    elif text.lower() == 'essay question':
                        if current_question_text: # Save any previous question
                            _save_parsed_question(exam, current_question_text, question_type, current_options, current_answer_letter, current_lecturer_answer_key)
                            parsed_questions += 1
                            current_question_text = None; current_options = []; current_answer_letter = None; current_lecturer_answer_key = None;
                        print("DEBUG: Header 'Essay Question' detected.")
                        is_next_question_essay = True
                        is_next_question_fill_in_the_blanks = False
                        question_type = 'essay' # Set current type expectation
                        continue

                    # Main parsing logic
                    if q_match:
                        if current_question_text: # This means a previous question was being built, save it.
                            print(f"DEBUG: Saving previous Q (type {question_type}): '{current_question_text}'")
                            _save_parsed_question(exam, current_question_text, question_type, current_options, current_answer_letter, current_lecturer_answer_key)
                            parsed_questions += 1
                        
                        # Start new question
                        current_question_text = q_match.group(1).strip()
                        current_options = []
                        current_answer_letter = None
                        current_lecturer_answer_key = None

                        if is_next_question_essay:
                            question_type = 'essay'
                            print(f"DEBUG: Matched QUESTION: '{current_question_text}' (type set by Essay header: {question_type})")
                            is_next_question_essay = False # Reset flag after using it
                        elif is_next_question_fill_in_the_blanks:
                            question_type = 'fill_in_the_blanks'
                            # Check for inline fill-in-the-blank keyword if needed, or just use the text
                            if "fill in the blank:" in current_question_text.lower():
                                 current_question_text = re.split("fill in the blank:", current_question_text, flags=re.IGNORECASE, maxsplit=1)[1].strip()
                            print(f"DEBUG: Matched QUESTION: '{current_question_text}' (type set by FillBlanks header: {question_type})")
                            is_next_question_fill_in_the_blanks = False # Reset flag
                        else:
                            # Default to MCQ if no header flag was set for it, but also check for inline essay/fill keywords
                            essay_keyword_inline = "essay question:"
                            fill_blank_keyword_inline = "fill in the blank:"
                            temp_text_lower = current_question_text.lower()

                            if essay_keyword_inline in temp_text_lower:
                                question_type = 'essay'
                                current_question_text = re.split(essay_keyword_inline, current_question_text, flags=re.IGNORECASE, maxsplit=1)[1].strip()
                                print(f"DEBUG: Matched QUESTION: '{current_question_text}' (inline essay keyword: {question_type})")
                            elif fill_blank_keyword_inline in temp_text_lower or "____" in current_question_text:
                                question_type = 'fill_in_the_blanks'
                                if fill_blank_keyword_inline in temp_text_lower:
                                    current_question_text = re.split(fill_blank_keyword_inline, current_question_text, flags=re.IGNORECASE, maxsplit=1)[1].strip()
                                print(f"DEBUG: Matched QUESTION: '{current_question_text}' (inline fill/blank keyword: {question_type})")
                            else:
                                question_type = 'multiple_choice' # True default
                                print(f"DEBUG: Matched QUESTION: '{current_question_text}' (defaulting to MCQ type: {question_type})")
                        continue # Added continue here
                    elif option_match and question_type == 'multiple_choice':
                        option_letter = option_match.group(1).upper()
                        option_text = option_match.group(2).strip()
                        current_options.append({'letter': option_letter, 'text': option_text})
                        print(f"DEBUG: Matched OPTION: Letter='{option_letter}', Text='{option_text}'. current_options now: {current_options}")
                    elif answer_match and question_type == 'multiple_choice':
                        current_answer_letter = answer_match.group(1).upper()
                        print(f"DEBUG: Matched ANSWER for MCQ: Letter='{current_answer_letter}'")
                        # MCQ is saved when the next question starts or at the end of the document
                    elif (question_type == 'essay' or question_type == 'fill_in_the_blanks') and text.lower().startswith('answer:'):
                        current_lecturer_answer_key = text.split(':', 1)[1].strip()
                        print(f"DEBUG: Matched Text Answer for {question_type}: '{current_lecturer_answer_key}' for Q: '{current_question_text}'")
                        _save_parsed_question(exam, current_question_text, question_type, [], None, current_lecturer_answer_key)
                        parsed_questions += 1
                        current_question_text = None # Reset
                        # Reset question_type to default or let next header/q_match decide
                        question_type = 'multiple_choice' 
                        is_next_question_essay = False # Reset flags
                        is_next_question_fill_in_the_blanks = False
                        continue
                
                # Save the last question after the loop finishes
                if current_question_text:
                    print(f"DEBUG: Saving LAST question (type: {question_type}): '{current_question_text}' Options: {current_options} Ans: {current_answer_letter}")
                    _save_parsed_question(exam, current_question_text, question_type, current_options, current_answer_letter, current_lecturer_answer_key)
                    parsed_questions += 1

            print("--- Question Parsing Finished ---_DEBUG_EMAIL_REMOVED_") # DEBUG END
            return JsonResponse({'message': f'Successfully parsed and saved {parsed_questions} questions for exam "{exam.title}".'}, status=201)

        except Exception as e:
            print(f"ERROR during parsing: {str(e)} traceback: {traceback.format_exc()}") # DEBUG: Print full traceback
            return JsonResponse({'error': f'Error processing file: {str(e)}'}, status=500)
    
    return HttpResponseNotAllowed(['POST'])


@csrf_exempt
def update_exam_details_api(request, exam_id):
    if not is_lecturer_authenticated(request):
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    # Ensure the exam exists and belongs to the logged-in lecturer
    try:
        exam = Exam.objects.get(id=exam_id, lecturer_user=request.user)
    except Exam.DoesNotExist:
        return JsonResponse({'error': 'Exam not found or you do not have permission to modify it.'}, status=404)

    if request.method == 'POST': # Using POST for simplicity, PUT is also common for updates
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

        # Fields that a lecturer can update
        updated_fields_count = 0

        if 'title' in data:
            exam.title = data['title']
            updated_fields_count += 1
        
        if 'course_code' in data: # Should lecturers change this? Potentially risky if students use it to find exams.
            exam.course_code = data['course_code'] # Let's allow it for now, but be mindful.
            updated_fields_count += 1

        if 'start_time' in data:
            try:
                # Assuming incoming time is ISO 8601 format e.g., "2025-07-15T10:00:00Z"
                exam.start_time = timezone.datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
                updated_fields_count += 1
            except ValueError:
                return JsonResponse({'error': 'Invalid start_time format. Use ISO 8601.'}, status=400)
        
        if 'end_time' in data:
            try:
                exam.end_time = timezone.datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
                updated_fields_count += 1
            except ValueError:
                return JsonResponse({'error': 'Invalid end_time format. Use ISO 8601.'}, status=400)

        if 'duration_minutes' in data:
            try:
                duration = int(data['duration_minutes'])
                if duration <= 0:
                    return JsonResponse({'error': 'Duration must be positive.'}, status=400)
                exam.duration_minutes = duration
                updated_fields_count += 1
            except ValueError:
                return JsonResponse({'error': 'Invalid duration_minutes format. Must be an integer.'}, status=400)
        
        if 'is_active' in data:
            if isinstance(data['is_active'], bool):
                exam.is_active = data['is_active']
                updated_fields_count += 1
            else:
                return JsonResponse({'error': 'is_active must be a boolean (true/false).'}, status=400)

        if updated_fields_count > 0:
            # Validation: Ensure end_time is after start_time if both are present or being updated
            if exam.start_time and exam.end_time and exam.end_time <= exam.start_time:
                return JsonResponse({'error': 'End time must be after start time.'}, status=400)
            
            exam.save()
            return JsonResponse({'message': 'Exam details updated successfully.'})
        else:
            return JsonResponse({'message': 'No update data provided or no changes made.'}, status=200) # Or 304 Not Modified

    return HttpResponseNotAllowed(['POST']) # Or ['POST', 'PUT']


@csrf_exempt
def get_exam_attempts_api(request, exam_id):
    if not is_lecturer_authenticated(request):
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    try:
        exam = Exam.objects.get(id=exam_id, lecturer_user=request.user)
    except Exam.DoesNotExist:
        return JsonResponse({'error': 'Exam not found or you do not have permission to view it.'}, status=404)

    if request.method == 'GET':
        attempts = ExamAttempt.objects.filter(exam=exam).select_related('student').order_by('-start_time')

        attempts_data = []
        for attempt in attempts:
            student_data = {
                'name': attempt.student.name,
                'matric_number': attempt.student.matric_number
            }
            attempts_data.append({
                'attempt_id': attempt.id,
                'student': student_data,
                'start_time': attempt.start_time.isoformat() if attempt.start_time else None,
                'submission_time': attempt.submission_time.isoformat() if attempt.submission_time else None,
                'score': attempt.score,
                'grace_login_granted': attempt.grace_login_granted,
                'attempt_deadline': attempt.attempt_deadline.isoformat() if attempt.attempt_deadline else None,
            })

        return JsonResponse({'exam_title': exam.title, 'attempts': attempts_data})

    return HttpResponseNotAllowed(['GET'])


@csrf_exempt
def grant_grace_login_api(request, attempt_id):
    if not is_lecturer_authenticated(request):
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    
    if request.method == 'POST':
        try:
            # Ensure the attempt exists and that the exam it belongs to is owned by the logged-in lecturer
            exam_attempt = ExamAttempt.objects.select_related('exam').get(
                id=attempt_id,
                exam__lecturer_user=request.user
            )
        except ExamAttempt.DoesNotExist:
            return JsonResponse({'error': 'Exam attempt not found or you do not have permission to modify it.'}, status=404)

        # Update the grace login field
        exam_attempt.grace_login_granted = True
        exam_attempt.save(update_fields=['grace_login_granted'])

        return JsonResponse({
            'message': 'Grace login has been successfully granted.',
            'attempt_id': exam_attempt.id,
            'grace_login_granted': exam_attempt.grace_login_granted
        })

    return HttpResponseNotAllowed(['POST'])


def _save_parsed_question(exam_obj, q_text, q_type, options_list, correct_letter, lecturer_answer_key_text):
    if not q_text:
        print("DEBUG_SAVE: q_text is empty, not saving question.")
        return

    print(f"DEBUG_SAVE: Creating Question: exam_id={exam_obj.id}, text='{q_text[:30]}...', type='{q_type}', answer_key='{lecturer_answer_key_text}'")
    question = Question.objects.create(
        exam=exam_obj,
        question_text=q_text,
        question_type=q_type,
        lecturer_answer_key=lecturer_answer_key_text if lecturer_answer_key_text is not None else ""
    )

    if q_type == 'multiple_choice':
        print(f"DEBUG_SAVE: MCQ options_list: {options_list}, correct_letter: {correct_letter}")
        for opt_idx, opt in enumerate(options_list):
            is_correct_option = (opt['letter'] == correct_letter)
            print(f"DEBUG_SAVE: Creating Option {opt_idx}: text='{opt['text']}', is_correct={is_correct_option}")
            Option.objects.create(
                question=question,
                option_text=opt['text'],
                is_correct=is_correct_option
            )
    print(f"DEBUG_SAVE: Question {question.id} saved.")

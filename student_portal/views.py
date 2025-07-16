from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from lecturer_portal.models import Exam, Question, Option
from .models import Student, ExamAttempt, StudentAnswer
import json
from urllib.parse import unquote
import random

def student_login_page(request):
    return render(request, 'student_portal/login.html')

def auto_submit_exam(attempt):
    attempt.score = 0
    attempt.submission_time = timezone.now()
    attempt.save()

@csrf_exempt
def student_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matric_number = data.get('matric_number')
            name = data.get('name')
            course_code = data.get('course_code')

            if not all([matric_number, name, course_code]):
                return JsonResponse({'error': 'Matric number, name, and course code are required.'}, status=400)

            # Find the exam
            try:
                exam = Exam.objects.get(course_code=course_code, is_active=True)
            except Exam.DoesNotExist:
                return JsonResponse({'error': 'No active exam found for this course code.'}, status=404)

            # Check if exam is within the valid time window (with a 5-minute grace period)
            now = timezone.now()
            grace_period_start = exam.start_time - timezone.timedelta(minutes=5)
            if not (grace_period_start <= now <= exam.end_time):
                return JsonResponse({'error': 'This exam is not available at this time.'}, status=403)

            # Get or create student
            student, created = Student.objects.get_or_create(
                matric_number=matric_number,
                defaults={'name': name}
            )

            # Check for existing attempt
            attempt, created = ExamAttempt.objects.get_or_create(
                student=student,
                exam=exam,
                defaults={
                    'attempt_deadline': now + timezone.timedelta(minutes=exam.duration_minutes + 2) # Add 2 minutes
                }
            )

            if not created:
                if now > attempt.exam.end_time:
                    return JsonResponse({'error': 'Your time for this exam has expired.'}, status=403)
                if attempt.submission_time:
                    return JsonResponse({'error': 'You have already submitted this exam.'}, status=403)

            # Store student and attempt info in session
            request.session['student_id'] = student.id
            request.session['exam_attempt_id'] = attempt.id

            return JsonResponse({
                'message': 'Login successful.',
                'student_id': student.id,
                'exam_attempt_id': attempt.id,
                'exam_title': exam.title,
                'exam_duration_minutes': exam.duration_minutes,
                'attempt_deadline': attempt.attempt_deadline.isoformat()
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)


def fetch_exam_questions(request, course_code):
    if request.method == 'GET':
        attempt_id = request.GET.get('attempt_id')
        decoded_course_code = unquote(course_code)

        if not attempt_id:
            return JsonResponse({'error': 'Missing attempt ID.'}, status=400)

        try:
            attempt = ExamAttempt.objects.select_related('exam', 'student').get(id=attempt_id)
            
            # Security check: ensure the course code in URL matches the exam
            if attempt.exam.course_code != decoded_course_code:
                return JsonResponse({'error': 'Mismatch in course code.'}, status=403)

            # Check if deadline has passed
            if timezone.now() > attempt.attempt_deadline:
                return JsonResponse({'error': 'Your time for this exam has expired.'}, status=403)

            questions = list(attempt.exam.questions.all().prefetch_related('options'))
            random.shuffle(questions) # Shuffle the questions
            
            questions_data = []
            for q in questions:
                question_info = {
                    'id': q.id,
                    'question_text': q.question_text,
                    'question_type': q.question_type,
                    'marks': q.marks,
                    'options': []
                }
                if q.question_type == 'multiple_choice':
                    options = list(q.options.all())
                    random.shuffle(options) # Shuffle the options
                    for option in options:
                        question_info['options'].append({
                            'id': option.id,
                            'option_text': option.option_text
                        })
                questions_data.append(question_info)

            return JsonResponse({
                'exam_title': attempt.exam.title,
                'questions': questions_data,
                'attempt_deadline': attempt.attempt_deadline.isoformat()
            })

        except ExamAttempt.DoesNotExist:
            return JsonResponse({'error': 'Invalid session. Please log in again.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only GET method is allowed.'}, status=405)


@csrf_exempt
def submit_answers(request, course_code):
    if request.method == 'POST':
        attempt_id = request.GET.get('attempt_id') # Get attempt_id from query params
        decoded_course_code = unquote(course_code)

        if not attempt_id:
            return JsonResponse({'error': 'Missing attempt ID.'}, status=400)

        try:
            attempt = ExamAttempt.objects.select_related('exam').get(id=attempt_id)

            if attempt.exam.course_code != decoded_course_code:
                return JsonResponse({'error': 'Invalid course code for this attempt.'}, status=403)

            if attempt.submission_time:
                return JsonResponse({'error': 'You have already submitted this exam.'}, status=400)

            if timezone.now() > attempt.attempt_deadline:
                return JsonResponse({'error': 'The deadline for submission has passed.'}, status=403)

            try:
                answers_data = json.loads(request.body).get('answers', [])
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

            total_score = 0
            
            for answer_item in answers_data:
                question_id = answer_item.get('question_id')
                answer_text = answer_item.get('answer_text', '').strip()
                selected_option_id = answer_item.get('selected_option_id')

                try:
                    question = Question.objects.get(id=question_id, exam=attempt.exam)
                except Question.DoesNotExist:
                    continue # Ignore answers for questions not in this exam

                marks_awarded = 0
                if question.question_type == 'multiple_choice' and selected_option_id:
                    try:
                        correct_option = Option.objects.get(question=question, is_correct=True)
                        if correct_option.id == selected_option_id:
                            marks_awarded = question.marks
                    except Option.DoesNotExist:
                        pass # No correct option set for this question
                
                elif question.question_type == 'fill_in_the_blanks':
                    correct_answers = [ans.strip() for ans in (question.lecturer_answer_key or "").split(',')]
                    student_answers = [ans.strip() for ans in answer_text.split(',')]
                    
                    if len(correct_answers) > 0:
                        correct_count = 0
                        for i in range(min(len(correct_answers), len(student_answers))):
                            student_answer = student_answers[i]
                            correct_answer = correct_answers[i]
                            
                            if not question.case_sensitive:
                                student_answer = student_answer.lower()
                                correct_answer = correct_answer.lower()

                            if student_answer == correct_answer:
                                correct_count += 1
                        
                        marks_awarded = (correct_count / len(correct_answers)) * question.marks
                
                elif question.question_type == 'essay':
                    keywords = [kw.strip().lower() for kw in (question.lecturer_answer_key or "").split(',')]
                    student_answer_text = answer_text.lower()
                    
                    if len(keywords) > 0:
                        found_keywords = 0
                        for keyword in keywords:
                            if keyword in student_answer_text:
                                found_keywords += 1
                        
                        marks_awarded = (found_keywords / len(keywords)) * question.marks


                StudentAnswer.objects.create(
                    exam_attempt=attempt,
                    question=question,
                    answer_text=answer_text if question.question_type != 'multiple_choice' else str(selected_option_id),
                    marks_awarded=marks_awarded
                )
                total_score += marks_awarded

            attempt.score = total_score
            attempt.submission_time = timezone.now()
            attempt.save()

            # Clear the session to prevent resubmission
            request.session.flush()

            return JsonResponse({
                'message': 'Exam submitted successfully.',
                'final_score': total_score,
                'total_marks_possible': sum(q.marks for q in attempt.exam.questions.all())
            })

        except ExamAttempt.DoesNotExist:
            return JsonResponse({'error': 'Invalid session or attempt not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)


@csrf_exempt
def log_cheating_attempt(request, course_code):
    if request.method == 'POST':
        attempt_id = request.GET.get('attempt_id') # Get attempt_id from query params
        decoded_course_code = unquote(course_code)

        if not attempt_id:
            return JsonResponse({'error': 'Missing attempt ID.'}, status=400)

        try:
            attempt = ExamAttempt.objects.get(id=attempt_id)

            if attempt.exam.course_code != decoded_course_code:
                return JsonResponse({'error': 'Invalid course code for this attempt.'}, status=403)

            if attempt.submission_time:
                return JsonResponse({'error': 'You have already submitted this exam.'}, status=400)

            attempt.cheating_attempts += 1
            attempt.save()

            if attempt.cheating_attempts >= 3:
                # Automatically submit the exam if the cheating limit is reached
                auto_submit_exam(attempt)
                return JsonResponse({'error': 'You have exceeded the maximum number of cheating attempts. Your exam has been submitted.'}, status=403)

            return JsonResponse({'message': 'Cheating attempt logged.', 'cheating_attempts': attempt.cheating_attempts})

        except ExamAttempt.DoesNotExist:
            return JsonResponse({'error': 'Invalid session or attempt not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)

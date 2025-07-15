from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from lecturer_portal.models import Exam, Question, Option
from .models import Student, ExamAttempt
import json

class StudentPortalAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.lecturer_user = User.objects.create_user(username='lecturer', password='password')
        self.exam = Exam.objects.create(
            title="Test Exam",
            course_code="CS101",
            start_time=timezone.now() - timezone.timedelta(hours=1),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            duration_minutes=60,
            is_active=True,
            lecturer_user=self.lecturer_user
        )
        self.mcq_question = Question.objects.create(exam=self.exam, question_text="What is 2+2?", question_type='multiple_choice', marks=10)
        self.mcq_option1 = Option.objects.create(question=self.mcq_question, option_text="3", is_correct=False)
        self.mcq_option2 = Option.objects.create(question=self.mcq_question, option_text="4", is_correct=True)

        self.fib_question = Question.objects.create(
            exam=self.exam,
            question_text="The colors of the flag are __, __, and __.",
            question_type='fill_in_the_blanks',
            marks=15,
            lecturer_answer_key="red, white, blue"
        )
        
        self.fib_case_sensitive_question = Question.objects.create(
            exam=self.exam,
            question_text="What is the abbreviation for Hyper Text Markup Language?",
            question_type='fill_in_the_blanks',
            marks=10,
            lecturer_answer_key="HTML",
            case_sensitive=True
        )

        self.essay_question = Question.objects.create(
            exam=self.exam,
            question_text="Explain the concept of Object-Oriented Programming.",
            question_type='essay',
            marks=20,
            lecturer_answer_key="class, object, inheritance, polymorphism"
        )

    def test_student_login(self):
        url = reverse('student_portal_api:student_login')
        data = {
            "name": "Test Student",
            "matric_number": "12345",
            "course_code": "CS101"
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('student_id', response.json())

    def test_fetch_exam_questions(self):
        # First, log in the student
        login_url = reverse('student_portal_api:student_login')
        login_data = {
            "name": "Test Student",
            "matric_number": "12345",
            "course_code": "CS101"
        }
        self.client.post(login_url, data=json.dumps(login_data), content_type='application/json')

        # Now, fetch the questions
        fetch_url = reverse('student_portal_api:fetch_exam_questions', kwargs={'course_code': 'CS101'})
        response = self.client.get(fetch_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['questions']), 4)

    def test_submit_answers_full_marks(self):
        # Log in the student
        login_url = reverse('student_portal_api:student_login')
        login_data = {
            "name": "Test Student",
            "matric_number": "12345",
            "course_code": "CS101"
        }
        self.client.post(login_url, data=json.dumps(login_data), content_type='application/json')

        # Submit answers
        submit_url = reverse('student_portal_api:submit_answers', kwargs={'course_code': 'CS101'})
        answers = {
            "answers": [
                {
                    "question_id": self.mcq_question.id,
                    "selected_option_id": self.mcq_option2.id
                },
                {
                    "question_id": self.fib_question.id,
                    "answer_text": "red, white, blue"
                },
                {
                    "question_id": self.fib_case_sensitive_question.id,
                    "answer_text": "HTML"
                },
                {
                    "question_id": self.essay_question.id,
                    "answer_text": "Object-Oriented Programming involves the use of classes and objects. Inheritance and polymorphism are key concepts."
                }
            ]
        }
        response = self.client.post(submit_url, data=json.dumps(answers), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['final_score'], 55) # 10 + 15 + 10 + 20

    def test_submit_answers_partial_marks(self):
        # Log in the student
        login_url = reverse('student_portal_api:student_login')
        login_data = {
            "name": "Test Student",
            "matric_number": "12345",
            "course_code": "CS101"
        }
        self.client.post(login_url, data=json.dumps(login_data), content_type='application/json')

        # Submit answers
        submit_url = reverse('student_portal_api:submit_answers', kwargs={'course_code': 'CS101'})
        answers = {
            "answers": [
                {
                    "question_id": self.mcq_question.id,
                    "selected_option_id": self.mcq_option1.id # Incorrect answer
                },
                {
                    "question_id": self.fib_question.id,
                    "answer_text": "red, green, blue" # One incorrect answer
                },
                {
                    "question_id": self.fib_case_sensitive_question.id,
                    "answer_text": "html" # Incorrect case
                },
                {
                    "question_id": self.essay_question.id,
                    "answer_text": "OOP uses classes and objects." # Missing some keywords
                }
            ]
        }
        response = self.client.post(submit_url, data=json.dumps(answers), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['final_score'], 20) # 0 + 10 + 0 + 10

    def test_log_cheating_attempt(self):
        # Log in the student
        login_url = reverse('student_portal_api:student_login')
        login_data = {
            "name": "Test Student",
            "matric_number": "12345",
            "course_code": "CS101"
        }
        self.client.post(login_url, data=json.dumps(login_data), content_type='application/json')

        # Log two cheating attempts
        log_url = reverse('student_portal_api:log_cheating_attempt', kwargs={'course_code': 'CS101'})
        response = self.client.post(log_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cheating_attempts'], 1)

        response = self.client.post(log_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cheating_attempts'], 2)

        # Log the third cheating attempt, which should trigger an automatic submission
        response = self.client.post(log_url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('You have exceeded the maximum number of cheating attempts', response.json()['error'])

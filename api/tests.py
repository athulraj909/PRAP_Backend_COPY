from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient


class StudentRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient(HTTP_USER_AGENT='Mozilla/5.0 registration-tests')
        self.registration_data = {
            'studentName': 'Test Student',
            'email': 'student@example.com',
            'mobile': '9876543210',
            'passoutYear': '2026',
        }

    @patch('api.views.send_welcome_email', return_value=True)
    def test_register_student_returns_json_success(self, send_welcome_email):
        response = self.client.post(
            '/api/student/register/',
            self.registration_data,
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['success'], True)
        send_welcome_email.assert_called_once()

    def test_register_student_returns_json_validation_error(self):
        response = self.client.post(
            '/api/student/register/',
            {'email': 'invalid-email'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)
        self.assertIn('message', response.json())

    @patch('api.views.StudentRegisterSerializer.save', side_effect=RuntimeError('test failure'))
    def test_register_student_returns_json_for_unexpected_failure(self, save):
        with self.assertLogs('api.views', level='ERROR'):
            response = self.client.post(
                '/api/student/register/',
                self.registration_data,
                format='json',
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['success'], False)
        self.assertEqual(
            response.json()['message'],
            'Registration could not be completed. Please try again later.',
        )

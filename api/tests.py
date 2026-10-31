from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from .middleware.rate_limit import RateLimitMiddleware
from .models import Course, StudentProfile


class RateLimitMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()

    @override_settings(
        RATE_LIMIT_ANON='1/hour',
        RATE_LIMIT_PUBLIC_ENDPOINTS='101/hour',
    )
    def test_api_prefixed_public_endpoint_uses_public_limit(self):
        middleware = RateLimitMiddleware(lambda request: None)
        request = self.factory.get(
            '/api/public/districts/',
            REMOTE_ADDR='192.0.2.1',
        )
        request.user = AnonymousUser()

        for _ in range(101):
            self.assertTrue(middleware._check_rate_limit(request, '192.0.2.1'))

        self.assertFalse(middleware._check_rate_limit(request, '192.0.2.1'))

    @override_settings(
        RATE_LIMIT_ANON='1/hour',
        RATE_LIMIT_LOGIN='101/hour',
    )
    def test_login_has_a_separate_limit_from_general_anonymous_requests(self):
        middleware = RateLimitMiddleware(lambda request: None)
        request = self.factory.post(
            '/api/student/login/',
            REMOTE_ADDR='192.0.2.2',
        )
        request.user = AnonymousUser()

        for _ in range(101):
            self.assertTrue(middleware._check_rate_limit(request, '192.0.2.2'))

        self.assertFalse(middleware._check_rate_limit(request, '192.0.2.2'))

    @override_settings(RATE_LIMIT_ANON='1/hour'    )
    def test_bearer_requests_use_drf_throttling_not_shared_ip_middleware_limit(self):
        middleware = RateLimitMiddleware(lambda request: HttpResponse())
        request = self.factory.get(
            '/api/student/profile/',
            HTTP_AUTHORIZATION='Bearer test-token',
            REMOTE_ADDR='192.0.2.3',
        )
        request.user = AnonymousUser()

        self.assertEqual(middleware(request).status_code, 200)
        self.assertEqual(middleware(request).status_code, 200)

    @override_settings(RATE_LIMIT_LOGIN='100/hour')
    def test_login_view_uses_its_dedicated_drf_throttle(self):
        client = APIClient(HTTP_USER_AGENT='Mozilla/5.0 login-throttle-tests')
        with patch(
            'rest_framework.throttling.ScopedRateThrottle.THROTTLE_RATES',
            {'login': '2/hour'},
        ):
            first = client.post(
                '/api/student/login/',
                {'mobile': '', 'password': ''},
                format='json',
            )
            second = client.post(
                '/api/student/login/',
                {'mobile': '', 'password': ''},
                format='json',
            )
            third = client.post(
                '/api/student/login/',
                {'mobile': '', 'password': ''},
                format='json',
            )

        self.assertEqual(first.status_code, 400)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(third.status_code, 429, third.content.decode())


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

    def test_register_student_uses_selected_course(self):
        course = Course.objects.create(
            course_name='Computer Science',
            duration='4 Years',
        )
        self.registration_data['course'] = str(course.id)

        with patch('api.views.send_welcome_email', return_value=True):
            response = self.client.post(
                '/api/student/register/',
                self.registration_data,
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudentProfile.objects.get().course, course)
        self.assertEqual(Course.objects.count(), 1)

    def test_register_student_accepts_legacy_course_name(self):
        course = Course.objects.create(
            course_name='Computer Science',
            duration='4 Years',
        )
        self.registration_data['course'] = course.course_name

        with patch('api.views.send_welcome_email', return_value=True):
            response = self.client.post(
                '/api/student/register/',
                self.registration_data,
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudentProfile.objects.get().course, course)
        self.assertEqual(Course.objects.count(), 1)

    def test_register_student_rejects_unavailable_course_without_creating_it(self):
        self.registration_data['course'] = 'Course that is no longer available'

        response = self.client.post(
            '/api/student/register/',
            self.registration_data,
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Selected course is unavailable', response.json()['message'])
        self.assertEqual(Course.objects.count(), 0)
        self.assertEqual(StudentProfile.objects.count(), 0)

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

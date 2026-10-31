from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpResponse
from django.db import connection
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from django.db.migrations.executor import MigrationExecutor
from rest_framework_simplejwt.tokens import RefreshToken

from .middleware.rate_limit import RateLimitMiddleware
from .models import AssessmentResult, Course, StudentProfile, User
from .serializers import CourseSerializer


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


class CourseClassificationTests(TestCase):
    def test_course_serializer_accepts_it_and_non_it_only(self):
        for classification in ('IT', 'NON_IT'):
            serializer = CourseSerializer(data={
                'courseName': f'{classification} course',
                'duration': '4 Years',
                'applicableTo': classification,
            })

            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_course_serializer_rejects_both_classification(self):
        serializer = CourseSerializer(data={
            'courseName': 'Legacy course',
            'duration': '4 Years',
            'applicableTo': 'BOTH',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('applicableTo', serializer.errors)


class CourseClassificationMigrationTests(TransactionTestCase):
    migrate_from = ('api', '0006_studentprofile_passout_year_and_more')
    migrate_to = ('api', '0007_course_it_or_non_it')

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps

        Course = old_apps.get_model('api', 'Course')
        StudentProfile = old_apps.get_model('api', 'StudentProfile')
        AssessmentResult = old_apps.get_model('api', 'AssessmentResult')

        legacy_course = Course.objects.create(
            course_name='Legacy course',
            duration='4 Years',
            applicable_to='BOTH',
        )
        profile = StudentProfile.objects.create(
            student_name='Migration Test Student',
            email='migration-test@example.com',
            mobile='9876543210',
            course=legacy_course,
        )
        AssessmentResult.objects.create(
            student_id=profile.pk,
            student_mobile='9876543210',
            student_name='Migration Test Student',
            college='Test College',
            course='Legacy course',
            score=8,
            total_marks=10,
            category_breakdown={'reasoning': 8},
            answers={'question1': 'A'},
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.new_apps = executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate([self.migrate_to])
        super().tearDown()

    def test_existing_course_profile_and_assessment_history_are_preserved(self):
        Course = self.new_apps.get_model('api', 'Course')
        StudentProfile = self.new_apps.get_model('api', 'StudentProfile')
        AssessmentResult = self.new_apps.get_model('api', 'AssessmentResult')

        course = Course.objects.get(course_name='Legacy course')
        profile = StudentProfile.objects.get(mobile='9876543210')
        result = AssessmentResult.objects.get(student_mobile='9876543210')

        self.assertEqual(course.applicable_to, 'NON_IT')
        self.assertEqual(profile.course_id, course.id)
        self.assertEqual(AssessmentResult.objects.count(), 1)
        self.assertEqual(result.course, 'Legacy course')
        self.assertEqual(result.score, 8)
        self.assertEqual(result.category_breakdown, {'reasoning': 8})
        self.assertEqual(result.answers, {'question1': 'A'})


class StudentExamResultsAuthorizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='8383483456',
            mobile='8383483456',
            password='test-password',
            role='student',
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            student_name='History Test Student',
            email='history-test@example.com',
            mobile='8383483456',
        )
        self.result = AssessmentResult.objects.create(
            student=self.profile,
            student_mobile=self.profile.mobile,
            student_name=self.profile.student_name,
            college='Test College',
            course='Computer Science',
            score=8,
            total_marks=10,
            category_breakdown={'reasoning': 8},
            answers={'question1': 'A'},
        )
        self.client = APIClient(HTTP_USER_AGENT='Mozilla/5.0 history-tests')
        self.url = f'/api/student/exam/results/?mobile={self.profile.mobile}'
        self.token = str(RefreshToken.for_user(self.user).access_token)

    def test_assessment_history_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertIn(response.status_code, (401, 403))

    def test_student_can_fetch_own_assessment_history_with_bearer_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['id'], self.result.id)

    def test_student_cannot_fetch_another_students_assessment_history(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(
            '/api/student/exam/results/?mobile=9876543210',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['results'] if 'results' in response.json() else [], [])


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

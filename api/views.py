from rest_framework import status, generics, permissions, pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db import models
from django.core.cache import cache
from .models import District, College, Course, StudentProfile, AssessmentCategory, Question, ExamSettings
from .serializers import (
    DistrictSerializer,
    CollegeSerializer,
    CourseSerializer,
    StudentProfileSerializer,
    StudentRegisterSerializer,
    StudentLoginSerializer,
    AssessmentCategorySerializer,
    QuestionSerializer,
    ExamSettingsSerializer
)
from .utils import send_welcome_email


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class DistrictPublicListView(generics.ListAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = District.objects.all()
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class DistrictListCreateView(generics.ListCreateAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = District.objects.all()
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class DistrictDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAdminUser]


class CollegePublicListView(generics.ListAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = College.objects.all()
        district_param = self.request.query_params.get('district', None)
        status_param = self.request.query_params.get('status', None)
        if district_param:
            queryset = queryset.filter(district__district_name__iexact=district_param)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class CollegeListCreateView(generics.ListCreateAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = College.objects.all()
        district_param = self.request.query_params.get('district', None)
        status_param = self.request.query_params.get('status', None)
        if district_param:
            queryset = queryset.filter(district__district_name__iexact=district_param)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class CollegeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer
    permission_classes = [IsAdminUser]


class CoursePublicListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Course.objects.all()
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Course.objects.all()
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminUser]


class AssessmentCategoryPublicListView(generics.ListAPIView):
    queryset = AssessmentCategory.objects.all()
    serializer_class = AssessmentCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = AssessmentCategory.objects.all()
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class AssessmentCategoryListCreateView(generics.ListCreateAPIView):
    queryset = AssessmentCategory.objects.all()
    serializer_class = AssessmentCategorySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = AssessmentCategory.objects.all()
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class AssessmentCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AssessmentCategory.objects.all()
    serializer_class = AssessmentCategorySerializer
    permission_classes = [IsAdminUser]


class QuestionListCreateView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Question.objects.all()
        category_param = self.request.query_params.get('category', None)
        status_param = self.request.query_params.get('status', None)
        if category_param:
            queryset = queryset.filter(category__category_name__iexact=category_param)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]


class QuestionBatchImportView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        questions_data = request.data.get('questions', [])
        
        if not questions_data:
            return Response({
                'success': False,
                'message': 'No questions provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_questions = []
        created_categories = []
        errors = []

        for idx, question_data in enumerate(questions_data):
            try:
                # Get category by name
                category_name = question_data.get('category') or question_data.get('categoryName')
                if not category_name:
                    errors.append(f"Row {idx + 1}: Category is required")
                    continue

                category = AssessmentCategory.objects.filter(category_name__iexact=category_name).first()
                
                # Auto-create category if it doesn't exist
                if not category:
                    category = AssessmentCategory.objects.create(
                        category_name=category_name,
                        description=f"Auto-created category for {category_name}",
                        applicable_to='BOTH',
                        status='Active'
                    )
                    created_categories.append(category_name)

                # Create question with category ID
                question = Question.objects.create(
                    category=category,
                    question=question_data.get('question', ''),
                    option_a=question_data.get('optionA', ''),
                    option_b=question_data.get('optionB', ''),
                    option_c=question_data.get('optionC', ''),
                    option_d=question_data.get('optionD', ''),
                    correct_answer=question_data.get('correctAnswer', 'A'),
                    explanation=question_data.get('explanation', ''),
                    marks=question_data.get('marks', 1),
                    negative_marks=question_data.get('negativeMarks', 0),
                    status=question_data.get('status', 'Active')
                )
                created_questions.append(QuestionSerializer(question).data)

            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")

        message = f"Imported {len(created_questions)} questions"
        if created_categories:
            message += f". Created {len(created_categories)} new categories: {', '.join(created_categories)}"

        return Response({
            'success': True,
            'created': len(created_questions),
            'created_categories': created_categories,
            'errors': errors,
            'questions': created_questions,
            'message': message
        }, status=status.HTTP_201_CREATED if created_questions else status.HTTP_400_BAD_REQUEST)


class QuestionBatchDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({
                'success': False,
                'message': 'No question IDs provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = Question.objects.filter(id__in=ids).delete()[0]

        return Response({
            'success': True,
            'deleted': deleted_count,
            'message': f'Successfully deleted {deleted_count} questions'
        }, status=status.HTTP_200_OK)


class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if user.role != 'admin':
            return Response({
                'success': False,
                'message': 'Access denied. Admin only.'
            }, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'token': str(refresh.access_token),
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'name': user.first_name,
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)


class StudentRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentRegisterSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            user = profile.user
            refresh = RefreshToken.for_user(user) if user else RefreshToken()
            
            student_data = StudentProfileSerializer(profile).data

            # Send welcome email with credentials
            district_name = profile.district.district_name if profile.district else 'N/A'
            college_name = profile.college.college_name if profile.college else 'N/A'
            course_name = profile.course.course_name if profile.course else 'N/A'
            
            # Get the password for email (from temporary field or generated)
            provided_password = profile.password if hasattr(profile, 'password') and profile.password else f"PRAP@{profile.mobile[-4:]}"
            
            send_welcome_email(
                student_name=profile.student_name,
                student_email=profile.email,
                student_mobile=profile.mobile,
                password=provided_password,
                district=district_name,
                college=college_name,
                course=course_name
            )

            return Response({
                'success': True,
                'message': 'Registration successful! Account & password created. Welcome email sent.',
                'token': str(refresh.access_token),
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': student_data,
                'student': student_data
            }, status=status.HTTP_201_CREATED)
        
        # Return first error message clearly for frontend
        error_msg = "Validation failed"
        if serializer.errors:
            for field, errors in serializer.errors.items():
                if isinstance(errors, list) and len(errors) > 0:
                    error_msg = str(errors[0])
                    break
                elif isinstance(errors, str):
                    error_msg = errors
                    break
        return Response({
            'success': False,
            'message': error_msg,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        error_msg = "Invalid mobile number or password"
        if serializer.errors:
            if 'non_field_errors' in serializer.errors:
                error_msg = str(serializer.errors['non_field_errors'][0])
            else:
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list) and len(errors) > 0:
                        error_msg = str(errors[0])
                        break
        return Response({
            'success': False,
            'message': error_msg,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.student_profile
            serializer = StudentProfileSerializer(profile)
            return Response({'success': True, 'student': serializer.data})
        except StudentProfile.DoesNotExist:
            return Response({'success': False, 'message': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            profile = request.user.student_profile
            # Partial update supported
            serializer = StudentProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'student': serializer.data})
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except StudentProfile.DoesNotExist:
            return Response({'success': False, 'message': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)


class StudentListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = StudentProfileSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        college_name = self.request.query_params.get('college')
        search = self.request.query_params.get('search', '')
        
        # Optimize queries with select_related for foreign keys
        queryset = StudentProfile.objects.select_related(
            'district', 'college', 'course', 'user'
        ).all()
        
        if college_name:
            queryset = queryset.filter(college__college_name__iexact=college_name)
        
        if search:
            queryset = queryset.filter(
                student_name__icontains=search
            ).filter(
                models.Q(email__icontains=search) |
                models.Q(mobile__icontains=search)
            )
        
        return queryset.order_by('-registered_at')


class StudentPerformanceBulkView(APIView):
    """
    Bulk endpoint to get performance data for multiple students in a single request
    to avoid N+1 query problems
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .models import AssessmentResult
        
        mobiles = request.query_params.get('mobiles', '').split(',')
        mobiles = [m.strip() for m in mobiles if m.strip()]
        
        if not mobiles:
            return Response({
                'success': False,
                'message': 'No mobile numbers provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cache key for this request
        cache_key = f'student_performance_bulk_{"_".join(sorted(mobiles))}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response({
                'success': True,
                'cached': True,
                'data': cached_data
            })
        
        try:
            # Get all assessment results for these students in a single query
            results = AssessmentResult.objects.filter(
                student_mobile__in=mobiles
            ).order_by('-completed_at')
            
            # Group results by student mobile
            performance_data = {}
            for mobile in mobiles:
                student_results = [r for r in results if r.student_mobile == mobile]
                
                if student_results:
                    total_score = sum(r.score for r in student_results)
                    total_possible = sum(r.total_marks for r in student_results)
                    avg_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0
                    
                    performance_data[mobile] = {
                        'totalAssessments': len(student_results),
                        'totalScore': total_score,
                        'totalPossible': total_possible,
                        'avgPercentage': avg_percentage,
                        'latestPercentage': round((student_results[0].score / student_results[0].total_marks) * 100) if student_results[0].total_marks > 0 else 0,
                        'latestDate': student_results[0].completed_at.isoformat(),
                        'categoryPerformance': student_results[0].category_breakdown or [],
                    }
                else:
                    performance_data[mobile] = {
                        'totalAssessments': 0,
                        'totalScore': 0,
                        'totalPossible': 0,
                        'avgPercentage': 0,
                        'latestPercentage': 0,
                        'latestDate': None,
                        'categoryPerformance': [],
                    }
            
            # Cache for 5 minutes
            cache.set(cache_key, performance_data, 300)
            
            return Response({
                'success': True,
                'cached': False,
                'data': performance_data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to fetch performance data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .models import AssessmentResult
        
        # Calculate statistics
        total_students = StudentProfile.objects.count()
        total_assessments = AssessmentResult.objects.count()
        total_colleges = College.objects.count()
        
        # Calculate hireability score (average percentage of all assessments)
        hireability_score = 0
        if total_assessments > 0:
            total_score = AssessmentResult.objects.aggregate(
                total=models.Sum('score')
            )['total'] or 0
            total_possible = AssessmentResult.objects.aggregate(
                total=models.Sum('total_marks')
            )['total'] or 0
            if total_possible > 0:
                hireability_score = round((total_score / total_possible) * 100)
        
        return Response({
            'total_students': total_students,
            'total_assessments': total_assessments,
            'total_colleges': total_colleges,
            'hireability_score': f"{hireability_score}%"
        })


class RecentActivityView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .models import AssessmentResult
        
        # Get recent assessment results (last 10)
        recent_results = AssessmentResult.objects.order_by('-completed_at')[:10]
        
        activity_data = []
        for result in recent_results:
            activity_data.append({
                'student_name': result.student_name,
                'student_mobile': result.student_mobile,
                'assessment': 'Placement Assessment',
                'status': 'Completed',
                'score': f"{round((result.score / result.total_marks) * 100)}%" if result.total_marks > 0 else "0%",
                'completed_at': result.completed_at.isoformat()
            })
        
        return Response(activity_data)


class ExamSettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Get or create exam settings (singleton pattern)
        settings, created = ExamSettings.objects.get_or_create(
            pk=1,
            defaults={
                'question_count': 100,
                'exam_duration_minutes': 100
            }
        )
        serializer = ExamSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        # Get or create exam settings
        settings, created = ExamSettings.objects.get_or_create(
            pk=1,
            defaults={
                'question_count': 100,
                'exam_duration_minutes': 100
            }
        )
        serializer = ExamSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExamSettingsPublicView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Public endpoint for students to fetch exam settings
        settings, created = ExamSettings.objects.get_or_create(
            pk=1,
            defaults={
                'question_count': 100,
                'exam_duration_minutes': 100
            }
        )
        serializer = ExamSettingsSerializer(settings)
        return Response(serializer.data)


class StudentExamSubmitView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .models import AssessmentResult, StudentProfile
        import secrets
        
        student_data = request.data.get('student')
        answers = request.data.get('answers', {})
        total_questions = request.data.get('totalQuestions', 0)
        score = request.data.get('score', 0)
        percentage = request.data.get('percentage', 0)
        time_taken = request.data.get('timeTaken', 0)
        category_performance = request.data.get('categoryPerformance', [])
        review = request.data.get('review', [])
        reason = request.data.get('reason', 'Submitted by student')
        resume_token = request.data.get('resumeToken')
        
        if not student_data or not student_data.get('mobile'):
            return Response({
                'success': False,
                'message': 'Student information is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get student profile
            student_profile = StudentProfile.objects.filter(mobile=student_data['mobile']).first()
            if not student_profile:
                return Response({
                    'success': False,
                    'message': 'Student not found. Please register first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify resume token if provided (optional security layer)
            if resume_token and hasattr(student_profile, 'resume_token'):
                if student_profile.resume_token != resume_token:
                    return Response({
                        'success': False,
                        'message': 'Invalid resume token'
                    }, status=status.HTTP_403_FORBIDDEN)

            # Create assessment result
            result = AssessmentResult.objects.create(
                student=student_profile,
                student_mobile=student_data['mobile'],
                student_name=student_data.get('name', student_profile.student_name),
                college=student_data.get('college', student_profile.college.college_name if student_profile.college else ''),
                course=student_data.get('course', student_profile.course.course_name if student_profile.course else ''),
                score=score,
                total_marks=total_questions,
                category_breakdown=category_performance,
                answers={
                    'answers': answers,
                    'review': review,
                    'reason': reason,
                    'timeTaken': time_taken
                }
            )
            
            return Response({
                'success': True,
                'message': 'Exam submitted successfully',
                'result_id': result.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to submit exam: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentExamResultsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .models import AssessmentResult
        
        mobile = request.query_params.get('mobile')
        if not mobile:
            return Response({
                'success': False,
                'message': 'Mobile number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify that the mobile number belongs to a registered student
            student_profile = StudentProfile.objects.filter(mobile=mobile).first()
            if not student_profile:
                return Response({
                    'success': False,
                    'message': 'Student not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            results = AssessmentResult.objects.filter(student_mobile=mobile).order_by('-completed_at')
            results_data = []
            
            for result in results:
                results_data.append({
                    'id': result.id,
                    'student_name': result.student_name,
                    'student_mobile': result.student_mobile,
                    'college': result.college,
                    'course': result.course,
                    'score': result.score,
                    'total_marks': result.total_marks,
                    'percentage': round((result.score / result.total_marks) * 100, 2) if result.total_marks > 0 else 0,
                    'category_breakdown': result.category_breakdown,
                    'answers': result.answers,
                    'completed_at': result.completed_at.isoformat()
                })
            
            return Response({
                'success': True,
                'results': results_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to fetch results: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

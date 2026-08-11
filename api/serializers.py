from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import District, College, Course, StudentProfile, AssessmentCategory, Question

User = get_user_model()


class DistrictSerializer(serializers.ModelSerializer):
    districtName = serializers.CharField(source='district_name', required=True)

    class Meta:
        model = District
        fields = ['id', 'districtName', 'state', 'status']
        extra_kwargs = {
            'district_name': {'write_only': True}
        }


class CollegeSerializer(serializers.ModelSerializer):
    collegeName = serializers.CharField(source='college_name', required=True)
    districtName = serializers.CharField(source='district.district_name', read_only=True)

    class Meta:
        model = College
        fields = ['id', 'collegeName', 'district', 'districtName', 'status']
        extra_kwargs = {
            'college_name': {'write_only': True},
            'district': {'write_only': True}
        }


class CourseSerializer(serializers.ModelSerializer):
    courseName = serializers.CharField(source='course_name', required=True)
    applicableTo = serializers.CharField(source='applicable_to', required=True)

    class Meta:
        model = Course
        fields = ['id', 'courseName', 'duration', 'applicableTo', 'status']
        extra_kwargs = {
            'course_name': {'write_only': True},
            'applicable_to': {'write_only': True}
        }


class AssessmentCategorySerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(source='category_name', required=True)
    applicableTo = serializers.CharField(source='applicable_to', required=True)

    class Meta:
        model = AssessmentCategory
        fields = ['id', 'categoryName', 'description', 'applicableTo', 'status']
        extra_kwargs = {
            'category_name': {'write_only': True},
            'applicable_to': {'write_only': True}
        }


class QuestionSerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(source='category.category_name', read_only=True)
    categoryId = serializers.IntegerField(source='category.id', read_only=False)
    optionA = serializers.CharField(source='option_a', required=True)
    optionB = serializers.CharField(source='option_b', required=True)
    optionC = serializers.CharField(source='option_c', required=True)
    optionD = serializers.CharField(source='option_d', required=True)
    correctAnswer = serializers.CharField(source='correct_answer', required=True)
    negativeMarks = serializers.FloatField(source='negative_marks', required=False)

    class Meta:
        model = Question
        fields = ['id', 'categoryId', 'categoryName', 'question', 'optionA', 'optionB', 'optionC', 'optionD', 'correctAnswer', 'explanation', 'marks', 'negativeMarks', 'status']
        extra_kwargs = {
            'category': {'write_only': True},
            'option_a': {'write_only': True},
            'option_b': {'write_only': True},
            'option_c': {'write_only': True},
            'option_d': {'write_only': True},
            'correct_answer': {'write_only': True},
            'negative_marks': {'write_only': True}
        }


class StudentProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='student_name')
    studentName = serializers.CharField(source='student_name')
    district = serializers.SerializerMethodField()
    college = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    registeredAt = serializers.DateTimeField(source='registered_at', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'name',
            'studentName',
            'email',
            'mobile',
            'district',
            'college',
            'course',
            'registered_at',
            'registeredAt',
        ]

    def get_district(self, obj):
        return obj.district.district_name if obj.district else ''

    def get_college(self, obj):
        return obj.college.college_name if obj.college else ''

    def get_course(self, obj):
        return obj.course.course_name if obj.course else ''


class StudentRegisterSerializer(serializers.Serializer):
    studentName = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    mobile = serializers.CharField(max_length=15)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    district = serializers.CharField(required=False, allow_blank=True)
    college = serializers.CharField(required=False, allow_blank=True)
    course = serializers.CharField(required=False, allow_blank=True)

    def validate_mobile(self, value):
        # Validate 10 digit mobile format if possible
        clean_mobile = value.strip()
        if len(clean_mobile) != 10 or not clean_mobile.isdigit():
            raise serializers.ValidationError("Mobile number must be exactly 10 digits")
        if StudentProfile.objects.filter(mobile=clean_mobile).exists() or User.objects.filter(mobile=clean_mobile).exists():
            raise serializers.ValidationError("This mobile number is already registered")
        return clean_mobile

    def create(self, validated_data):
        student_name = validated_data.get('studentName') or validated_data.get('name') or "Student"
        email = validated_data.get('email')
        mobile = validated_data.get('mobile')
        provided_password = validated_data.get('password')

        # Auto-generate password if not provided (PRAP@ + last 4 digits of mobile)
        if not provided_password:
            provided_password = f"PRAP@{mobile[-4:]}"

        # Resolve or get_or_create District
        district_input = validated_data.get('district')
        district_obj = None
        if district_input:
            if str(district_input).isdigit():
                district_obj = District.objects.filter(id=int(district_input)).first()
            if not district_obj:
                district_obj, _ = District.objects.get_or_create(district_name=district_input)

        # Resolve or get_or_create College
        college_input = validated_data.get('college')
        college_obj = None
        if college_input:
            if str(college_input).isdigit():
                college_obj = College.objects.filter(id=int(college_input)).first()
            if not college_obj and district_obj:
                college_obj, _ = College.objects.get_or_create(
                    college_name=college_input,
                    defaults={'district': district_obj}
                )
            elif not college_obj:
                default_dist, _ = District.objects.get_or_create(district_name="General")
                college_obj, _ = College.objects.get_or_create(
                    college_name=college_input,
                    defaults={'district': default_dist}
                )

        # Resolve or get_or_create Course
        course_input = validated_data.get('course')
        course_obj = None
        if course_input:
            if str(course_input).isdigit():
                course_obj = Course.objects.filter(id=int(course_input)).first()
            if not course_obj:
                course_obj, _ = Course.objects.get_or_create(
                    course_name=course_input,
                    defaults={'duration': '3 Years'}
                )

        # Create Django User for Auth
        user, created = User.objects.get_or_create(
            username=mobile,
            defaults={
                'email': email,
                'first_name': student_name,
                'role': 'student',
                'mobile': mobile
            }
        )
        user.set_password(provided_password)
        user.save()

        # Create StudentProfile
        profile = StudentProfile.objects.create(
            user=user,
            student_name=student_name,
            email=email,
            mobile=mobile,
            password=provided_password,
            district=district_obj,
            college=college_obj,
            course=course_obj
        )

        return profile


class StudentLoginSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        mobile = data.get('mobile', '').strip()
        password = data.get('password', '').strip()

        if not mobile or not password:
            raise serializers.ValidationError("Both mobile number and password are required.")

        # Find student profile or user
        profile = StudentProfile.objects.filter(mobile=mobile).first()

        # Check fallback for default demo student if profile doesn't exist yet
        if not profile and mobile == "7894561235" and (password == "PRAP@1235" or password == "123456"):
            # Auto-create demo student profile
            default_dist, _ = District.objects.get_or_create(district_name="Coimbatore")
            default_coll, _ = College.objects.get_or_create(college_name="RVS College", defaults={'district': default_dist})
            default_crs, _ = Course.objects.get_or_create(course_name="BCA", defaults={'duration': '3 Years'})
            user, _ = User.objects.get_or_create(username=mobile, defaults={'email': 'aaa@example.com', 'first_name': 'aaa', 'role': 'student', 'mobile': mobile})
            user.set_password(password)
            user.save()
            profile = StudentProfile.objects.create(
                user=user,
                student_name="aaa",
                email="aaa@example.com",
                mobile=mobile,
                password=password,
                district=default_dist,
                college=default_coll,
                course=default_crs
            )

        if not profile:
            raise serializers.ValidationError("Invalid mobile number or password")

        # Verify password against User object or profile password
        user = profile.user
        authenticated = False

        if user and user.check_password(password):
            authenticated = True
        elif profile.password == password:
            authenticated = True
            # Sync user password
            if user:
                user.set_password(password)
                user.save()

        if not authenticated:
            raise serializers.ValidationError("Invalid mobile number or password")

        # Generate SimpleJWT tokens
        refresh = RefreshToken.for_user(user) if user else RefreshToken()
        if user:
            refresh['role'] = user.role
            refresh['mobile'] = profile.mobile
            refresh['name'] = profile.student_name

        student_data = StudentProfileSerializer(profile).data
        # Ensure password is included in student payload if frontend expects it in session
        student_data['password'] = profile.password

        return {
            'success': True,
            'token': str(refresh.access_token),
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': student_data,
            'student': student_data
        }

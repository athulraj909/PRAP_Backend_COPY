from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class District(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    district_name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100, default='Kerala')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.district_name


class College(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    college_name = models.CharField(max_length=255)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='colleges')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.college_name


class Course(models.Model):
    APPLICABLE_CHOICES = (
        ('IT', 'IT'),
        ('NON_IT', 'NON_IT'),
        ('BOTH', 'BOTH'),
    )
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    course_name = models.CharField(max_length=255)
    duration = models.CharField(max_length=50)  # e.g., "4 Years", "3 Years"
    applicable_to = models.CharField(max_length=20, choices=APPLICABLE_CHOICES, default='BOTH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.course_name


class AssessmentCategory(models.Model):
    APPLICABLE_CHOICES = (
        ('IT', 'IT'),
        ('NON_IT', 'NON_IT'),
        ('BOTH', 'BOTH'),
    )
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    category_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    applicable_to = models.CharField(max_length=20, choices=APPLICABLE_CHOICES, default='BOTH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    percentage = models.FloatField(default=0.0)
    it_percentage = models.FloatField(default=0.0)
    non_it_percentage = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Assessment Categories"

    def __str__(self):
        return self.category_name


class Question(models.Model):
    ANSWER_CHOICES = (
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    )
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    category = models.ForeignKey(AssessmentCategory, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    explanation = models.TextField(blank=True, null=True)
    marks = models.IntegerField(default=1)
    negative_marks = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category.category_name} - {self.question[:30]}..."


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    student_name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=255)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} ({self.mobile})"


class AssessmentResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assessment_results', null=True, blank=True)
    student_mobile = models.CharField(max_length=15)
    student_name = models.CharField(max_length=255)
    college = models.CharField(max_length=255)
    course = models.CharField(max_length=255)
    score = models.FloatField()
    total_marks = models.IntegerField()
    category_breakdown = models.JSONField(default=dict)
    answers = models.JSONField(default=dict)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result: {self.student_name} - {self.score}/{self.total_marks}"


class ExamSettings(models.Model):
    question_count = models.IntegerField(default=100, help_text="Number of questions to load in exam")
    exam_duration_minutes = models.IntegerField(default=100, help_text="Exam duration in minutes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Exam Settings"
        verbose_name_plural = "Exam Settings"

    def __str__(self):
        return f"Settings: {self.question_count} questions, {self.exam_duration_minutes} minutes"

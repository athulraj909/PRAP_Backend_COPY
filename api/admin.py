from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    District,
    College,
    Course,
    AssessmentCategory,
    Question,
    StudentProfile,
    AssessmentResult,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'mobile', 'is_staff')
    fieldsets = (
        *UserAdmin.fieldsets,
        ('Custom Roles & Contact', {'fields': ('role', 'mobile')}),
    )
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        ('Custom Roles & Contact', {'fields': ('role', 'mobile')}),
    )


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'district_name', 'state', 'status', 'created_at')
    list_filter = ('status', 'state')
    search_fields = ('district_name',)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('id', 'college_name', 'district', 'status', 'created_at')
    list_filter = ('status', 'district')
    search_fields = ('college_name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_name', 'duration', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('course_name',)


@admin.register(AssessmentCategory)
class AssessmentCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name', 'applicable_to', 'status', 'created_at')
    list_filter = ('status', 'applicable_to')
    search_fields = ('category_name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'question', 'correct_answer', 'marks', 'status')
    list_filter = ('status', 'category')
    search_fields = ('question',)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'mobile', 'email', 'college', 'course', 'registered_at')
    search_fields = ('student_name', 'mobile', 'email')


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'student_mobile', 'college', 'score', 'total_marks', 'completed_at')
    search_fields = ('student_name', 'student_mobile', 'college')

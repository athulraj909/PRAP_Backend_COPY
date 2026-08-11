import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prap_backend.settings')
django.setup()

from api.models import User, StudentProfile

def delete_all_students():
    print("Deleting all students...")
    
    # Delete all student profiles
    student_profiles = StudentProfile.objects.all()
    profile_count = student_profiles.count()
    student_profiles.delete()
    print(f"Deleted {profile_count} student profiles")
    
    # Delete all student users (not admin)
    student_users = User.objects.filter(role='student')
    user_count = student_users.count()
    student_users.delete()
    print(f"Deleted {user_count} student users")
    
    print("All students deleted successfully!")

if __name__ == "__main__":
    delete_all_students()

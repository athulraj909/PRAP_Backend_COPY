import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prap_backend.settings')
django.setup()

from api.models import User

def create_admin_user():
    username = "PRAP@admin"
    password = "admin123"
    email = "admin@prap.com"
    
    # Check if admin user exists
    try:
        admin = User.objects.get(username=username)
        print(f"Admin user '{username}' already exists.")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        return admin
    except User.DoesNotExist:
        # Create admin user
        admin = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="PRAP",
            role="admin"
        )
        print(f"Admin user '{username}' created successfully!")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Password: {password}")
        print(f"Role: {admin.role}")
        return admin

if __name__ == "__main__":
    create_admin_user()

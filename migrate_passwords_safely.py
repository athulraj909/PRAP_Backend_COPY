"""
Safe Password Migration Script
Migrates plain text passwords from StudentProfile to Django User model
This ensures existing users can still login after removing the password field
"""

import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prap_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import StudentProfile

User = get_user_model()

def migrate_passwords():
    """
    Safely migrates passwords from StudentProfile to User model
    """
    print("🔄 Starting password migration...")
    print(f"⏰ Started at: {datetime.now()}")
    
    try:
        # Get all student profiles
        profiles = StudentProfile.objects.all()
        total_profiles = profiles.count()
        print(f"📊 Found {total_profiles} student profiles")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for profile in profiles:
            try:
                # Check if profile has a password field
                if hasattr(profile, 'password') and profile.password:
                    # Check if user exists
                    if profile.user:
                        # Check if user already has a password set
                        if not profile.user.password or profile.user.password.startswith('!'):  # Django unusable password
                            # Set the password from profile to user
                            profile.user.set_password(profile.password)
                            profile.user.save()
                            migrated_count += 1
                            print(f"✅ Migrated password for: {profile.student_name} ({profile.mobile})")
                        else:
                            # User already has a valid password, skip
                            skipped_count += 1
                            print(f"⏭️  Skipped (user has password): {profile.student_name} ({profile.mobile})")
                    else:
                        # No user exists, create one
                        user = User.objects.create_user(
                            username=profile.mobile,
                            email=profile.email,
                            first_name=profile.student_name,
                            password=profile.password,
                            mobile=profile.mobile,
                            role='student'
                        )
                        profile.user = user
                        profile.save()
                        migrated_count += 1
                        print(f"✅ Created user and migrated password: {profile.student_name} ({profile.mobile})")
                else:
                    # No password in profile or password field doesn't exist
                    skipped_count += 1
                    print(f"⏭️  No password to migrate: {profile.student_name} ({profile.mobile})")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error migrating {profile.student_name}: {e}")
                continue
        
        print(f"\n📊 Migration Summary:")
        print(f"✅ Successfully migrated: {migrated_count}")
        print(f"⏭️  Skipped: {skipped_count}")
        print(f"❌ Errors: {error_count}")
        print(f"📋 Total processed: {total_profiles}")
        print(f"⏰ Completed at: {datetime.now()}")
        
        return migrated_count, skipped_count, error_count
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 0, 0, 1

def verify_migration():
    """
    Verifies that all users have proper passwords set
    """
    print("\n🔍 Verifying migration...")
    
    try:
        users = User.objects.filter(role='student')
        total_users = users.count()
        valid_passwords = 0
        invalid_passwords = 0
        
        for user in users:
            if user.password and not user.password.startswith('!'):
                valid_passwords += 1
            else:
                invalid_passwords += 1
                print(f"⚠️  User with invalid password: {user.username}")
        
        print(f"📊 Verification Results:")
        print(f"✅ Valid passwords: {valid_passwords}/{total_users}")
        print(f"❌ Invalid passwords: {invalid_passwords}/{total_users}")
        
        return invalid_passwords == 0
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔐 PRAP Password Migration Script")
    print("=" * 60)
    
    # Step 1: Backup database
    print("\n📋 STEP 1: Creating database backup...")
    from backup_database import backup_database
    backup_path = backup_database()
    
    if not backup_path:
        print("❌ Backup failed. Aborting migration.")
        exit(1)
    
    # Step 2: Migrate passwords
    print("\n📋 STEP 2: Migrating passwords...")
    migrated, skipped, errors = migrate_passwords()
    
    if errors > 0:
        print(f"\n⚠️  Migration completed with {errors} errors. Please review.")
    else:
        print("\n✅ Migration completed successfully!")
    
    # Step 3: Verify migration
    print("\n📋 STEP 3: Verifying migration...")
    verification_passed = verify_migration()
    
    if verification_passed:
        print("\n✅ Verification passed! All users have valid passwords.")
    else:
        print("\n⚠️  Verification failed. Some users may have login issues.")
    
    print("\n" + "=" * 60)
    print("🎉 Migration process completed!")
    print("=" * 60)
    print(f"📁 Database backup: {backup_path}")
    print("📝 Next steps:")
    print("   1. Test login with existing user accounts")
    print("   2. If everything works, run: python manage.py makemigrations")
    print("   3. Then run: python manage.py migrate")
    print("   4. This will remove the password field from StudentProfile")
    print("=" * 60)
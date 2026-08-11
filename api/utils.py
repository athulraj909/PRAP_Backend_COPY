from django.core.mail import send_mail
from django.conf import settings


def send_welcome_email(student_name, student_email, student_mobile, password, district, college, course):
    """
    Send welcome email to newly registered student with their credentials
    """
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}Welcome to PRAP - Your Account Details"
    
    message = f"""
Dear {student_name},

Welcome to the Placement Readiness Assessment Program (PRAP)!

We are pleased to inform you that your registration has been successfully completed. Below are your account details:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STUDENT REGISTRATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Name: {student_name}
Email: {student_email}
Mobile: {student_mobile}
District: {district}
College: {college}
Course: {course}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOGIN CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mobile Number: {student_mobile}
Password: {password}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please keep your credentials safe and do not share them with anyone.

You can now log in to the PRAP application using your mobile number and password to:
• Take placement assessments
• View your performance statistics
• Track your progress
• Access study materials

If you have any questions or need assistance, please contact our support team.

Best regards,
PRAP Team
Placement Readiness Assessment Program

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated email. Please do not reply.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome email to {student_email}: {e}")
        return False

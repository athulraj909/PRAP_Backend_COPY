from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(student_name, student_email, student_mobile, password, district, college, course):
    """
    Send welcome email to newly registered student with their credentials
    """
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}Welcome to PRAP - Your Account Details"
    
    message = f"""
Dear {student_name},

Welcome to the Placement Readiness Assessment Program (PRAP)!

We are pleased to inform you that your registration has been successfully completed. Below are your account details:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

You can log in to the PRAP application using your mobile number and password to:
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
        logger.info(f"Attempting to send welcome email to {student_email}")
        logger.info(f"Email config: Host={settings.EMAIL_HOST}, Port={settings.EMAIL_PORT}, User={settings.EMAIL_HOST_USER}")
        
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student_email],
            fail_silently=False,
        )
        
        logger.info(f"Email send result: {result}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {student_email}: {e}")
        logger.error(f"Email configuration: {settings.EMAIL_HOST_USER}@{settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        return False
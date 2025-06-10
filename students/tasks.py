from celery import shared_task
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from academic_program.models import Program
from account.models import CustomUser
from account.tasks import get_domain  # Or define get_domain here if you prefer
from alumni.models import Alumni
from students.models import StudentDetail, StudentEnrollment


@shared_task
def send_alumnus_congratulations_email(student_email, program_name, year_of_completion):
    """
    Sends an email to a student congratulating them for becoming an alumnus.
    """
    # Build context data for the email template
    domain = get_domain()
    current_time = timezone.now()

    context = {
        'program_name': program_name,
        'year_of_completion': year_of_completion,
        'current_time': current_time
    }

    # Render an HTML email template (create it if you haven't yet)
    email_body = render_to_string('alumni/emails/alumnus_congrats.html', context)

    email_msg = EmailMessage(
        subject=f"Congratulations on Becoming an Alumnus of {program_name}!",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,  # or specify directly
        to=[student_email],
    )
    # Make sure to send HTML
    email_msg.content_subtype = 'html'
    email_msg.send(fail_silently=False)


@shared_task
def send_enrollment_notification_email(student_email, course_list, program_name, schedule_table_html):
    """
    Sends an email to the student listing the courses they've been enrolled in,
    the program name, and a rendered schedule table (if any).
    """
    domain = "6295-41-66-237-210.ngrok-free.app"
    dashboard_link = f"https://{domain}" + reverse('students:student_portal')

    context = {
        'course_list': course_list,
        'program_name': program_name,
        'dashboard_link': dashboard_link,
        'schedule_table': schedule_table_html,
    }

    email_body = render_to_string('students/emails/enrollment_notification_email.html', context)
    email = EmailMessage(
        subject=f"New Course Enrollment in {program_name}",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[student_email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def send_student_welcome_email(user_id):
    """
    Sends an official welcome email to the new student, asking them to set their password.
    """
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return  # User no longer exists

    domain = "6295-41-66-237-210.ngrok-free.app"
    # Build the password reset (set password) URL.
    reset_link = f"https://{domain}" + reverse('account:password_reset')
    # Build the student portal link.
    portal_link = f"https://{domain}" + reverse('students:student_portal')

    context = {
        'user': user,
        'reset_link': reset_link,
        'portal_link': portal_link,
        'email': user.email,
        'current_time': timezone.now(),
    }

    # Render the email template (create students/emails/welcome_email.html accordingly)
    email_body = render_to_string('students/emails/welcome_email.html', context)
    email = EmailMessage(
        subject="Welcome to CEIBS Africa – Your Student Account",
        body=email_body,
        to=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    # Ensure the email is sent as HTML
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def convert_selected_students_to_alumni(student_ids, program_id):
    """
    For each student ID in student_ids, mark all their active enrollments in the given program
    as 'Alumnus' and 'active=False', create or update an Alumni record,
    and send a curated email.
    """
    from account.models import CustomUser

    try:
        program = Program.objects.get(pk=program_id, flag=True)
    except Program.DoesNotExist:
        # Program not found or flagged off, skip
        return

    # We'll do everything in a transaction for consistency
    with transaction.atomic():
        for sid in student_ids:
            try:
                student = StudentDetail.objects.get(pk=sid)
            except StudentDetail.DoesNotExist:
                continue  # Skip if not found

            # Find active enrollments for this student in the program
            enrollments = StudentEnrollment.objects.filter(
                student=student,
                program=program,
                active=True
            )
            if not enrollments.exists():
                # No active enrollments to mark
                continue

            for enroll in enrollments:
                if enroll.status != "Alumnus":
                    enroll.status = "Alumnus"
                    enroll.active = False
                    enroll.save()

            # Create or get an Alumni record
            # Suppose your 'Alumni' model requires these fields:
            #  (student, user, first_name, last_name, email, program, year_of_completion, current_position, company, industry, picture)
            # Adjust as needed
            defaults = {
                'first_name': student.first_name,
                'last_name': student.last_name,
                'email': student.email,
                'year_of_completion': enrollments.first().end_date.year
                if enrollments.first().end_date else 'N/A',
                'current_position': student.position or '',
                'company': student.company or '',
                'industry': 'Tech',  # or an actual field from your data
                'picture': student.image,
            }
            alumnus_obj, created = Alumni.objects.get_or_create(
                student=student,
                user=student.user,
                program=program,
                defaults=defaults
            )

            # Send an alumnus confirmation email
            try:
                mail_subject = f"Congratulations! You are now an Alumnus of {program.program_name}"
                context = {
                    'student': student,
                    'program': program,
                    'conversion_date': timezone.now()
                }
                email_body = render_to_string('students/emails/alumnus_notification.html', context)
                msg = EmailMessage(
                    subject=mail_subject,
                    body=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[student.email],
                )
                msg.content_subtype = 'html'
                msg.send(fail_silently=True)
            except Exception as e:
                print(e)
                # Log or ignore error if sending fails
                pass


@shared_task
def send_enrollment_notification_email_task(student_id, program_id, dashboard_link, support_link):
    try:
        student = StudentDetail.objects.get(id=student_id)
        program = Program.objects.get(id=program_id)
    except (StudentDetail.DoesNotExist, Program.DoesNotExist):
        return  # If either object is missing, do nothing

    context = {
        'student': student,
        'program': program,
        'dashboard_link': dashboard_link,
        'email': student.user.email,
        'support_link': support_link,
        'current_time': timezone.now(),
    }

    subject = f"Enrollment Confirmation for {program.program_name} - CEIBS Africa"
    email_body = render_to_string('students/emails/enrollment_notification.html', context)
    email = EmailMessage(
        subject=subject,
        body=email_body,
        to=[student.email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)






import datetime
import os

import pandas as pd
from celery import shared_task
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from academic_program.models import Course, Program, ProgramParticipant, CourseParticipant
from alumni.models import Alumni
from finance.models import ProgramFees, FinanceStatement, StudentFinance
from students.models import StudentDetail, StudentEnrollment
from account.models import CustomUser, Role


def get_domain():
    # Return your domain; adjust for production.
    return 'localhost:3000'


@shared_task
def send_student_enrollment_email(student_id, program_id):
    """
    Sends an official welcome email to the new student informing them of their enrollment,
    listing the courses in the program and providing a portal link.
    """
    try:
        student = StudentDetail.objects.get(pk=student_id)
        program = Program.objects.get(pk=program_id)
    except (StudentDetail.DoesNotExist, Program.DoesNotExist):
        return

    domain = get_domain()
    portal_link = f"https://{domain}" + reverse('students:student_portal')

    # Fetch courses under the program
    courses = Course.objects.filter(program=program)
    course_names = [course.course_name for course in courses]

    context = {
        'student': student,
        'program': program,
        'course_names': course_names,
        'portal_link': portal_link,
        'current_time': timezone.now(),
    }

    email_body = render_to_string('academic_program/emails/enrollment_email.html', context)
    email = EmailMessage(
        subject=f"Welcome to {program.program_name} at CEIBS Africa",
        body=email_body,
        to=[student.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def send_program_participant_welcome_email(participant_id, program_id):
    """
    Sends an official welcome email to a new program participant, informing them about the program,
    listing its courses, and providing a participant portal link.
    """
    try:
        participant = ProgramParticipant.objects.get(pk=participant_id)
        program = Program.objects.get(pk=program_id)
    except (ProgramParticipant.DoesNotExist, Program.DoesNotExist):
        return

    domain = get_domain()
    # Adjust this URL if program participants have a dedicated portal

    courses = Course.objects.filter(program=program)
    course_names = [course.course_name for course in courses]

    context = {
        'participant': participant,
        'program': program,
        'course_names': course_names,
        'current_time': timezone.now(),
    }

    email_body = render_to_string('academic_program/emails/participant_welcome_email.html', context)
    email = EmailMessage(
        subject=f"Welcome to {program.program_name} at CEIBS Africa",
        body=email_body,
        to=[participant.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def process_excel_import_task(file_path, program_id):
    """
    Background task to parse the uploaded Excel file and create StudentDetail or ProgramParticipant
    records depending on whether the program is an alumni program.
    """
    # Safely load the Program
    try:
        program = Program.objects.get(pk=program_id, flag=True)
    except Program.DoesNotExist:
        # If the program doesn't exist or is inactive, we can't proceed
        return

    # Read Excel data
    df = pd.read_excel(file_path)
    counter = 0

    # We'll define a convenience check for whether the program is 'active' (not ended)
    # Adjust logic as needed (e.g., if you have 'program_ended' field or 'status' field).
    program_is_active = not program.program_ended if hasattr(program, 'program_ended') else True

    # Student role object, used if alumni_program is True
    student_role, _ = Role.objects.get_or_create(name='Student')

    for _, row in df.iterrows():
        if program.alumni_program:
            # ---------------------------
            # Alumni Program Logic
            # ---------------------------
            # Create the StudentDetail record
            student = StudentDetail.objects.create(
                first_name=row['first name'],
                last_name=row['last name'],
                other_names=row['other names'],
                email=row['email'],
                date_of_birth=row['date of birth'],
                gender=row['gender'],
                unique_id=row['student id'],
                phone_number=row['phone number'],
                address=row['address'],
                company=row['company'],
                position=row['position']
            )

            # If program is active, create a user account and send reset link
            if program_is_active:
                # Create a random password or store if needed
                random_pwd = get_random_string(12)
                new_user = CustomUser.objects.create_user(
                    username=row['student id'],
                    email=row['email'],
                    password=random_pwd,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    is_student=True
                )
                new_user.roles.add(student_role)
                new_user.save()
                student.user = new_user
                student.save()

                # Enroll the student in the program
                enrollment = StudentEnrollment.objects.create(
                    student=student,
                    program=program,
                    start_date=datetime.datetime.now(),
                    end_date=program.end_date,
                    active=True
                )

                # Enroll them in all courses for this program
                courses = Course.objects.filter(program=program)
                for course in courses:
                    CourseParticipant.objects.create(course=course, student=student)

                program_fees = ProgramFees.objects.get_or_create(program=program)
                finance_statement = FinanceStatement.objects.get_or_create(program_fees=program_fees)
                new_student = enrollment.student
                new_student_finance = StudentFinance.objects.get_or_create(
                    student=new_student,
                    finance_statement=finance_statement,
                )

                # Send a password reset link via email (since we created a new user)
                send_password_reset_email(new_user)
            else:
                # Program ended or not active: we still create the StudentDetail, but no user or email
                pass

            counter += 1

        else:
            # ---------------------------
            # Non-Alumni Program Logic
            # ---------------------------
            # Create ProgramParticipant
            participant = ProgramParticipant.objects.create(
                first_name=row['first name'],
                last_name=row['last name'],
                other_names=row['other names'],
                email=row['email'],
                phone_number=row['phone number'],
                position=row.get('position', ''),  # or row['position'] if guaranteed
                company=row.get('company', ''),    # or row['company'] if guaranteed
                program=program
            )

            counter += 1

    # Optionally, remove the file after processing
    try:
        os.remove(file_path)
    except OSError:
        pass


def send_password_reset_email(user):
    """
    Helper function to send a Django password reset link to 'user'.
    """
    domain = get_domain()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = f"https://{domain}" + reverse('account:password_reset')

    mail_subject = "Set Your CEIBS Africa Account Password"
    message_body = (
        f"Dear {user.first_name},\n\n"
        f"You have been added to a CEIBS Africa program. Please set your password by following the link below:\n"
        f"{reset_link}\n\n"
        f"After setting your password, you can log in to our student portal.\n"
        f"Best regards,\nCEIBS Africa"
    )

    email = EmailMessage(
        subject=mail_subject,
        body=message_body,
        to=[user.email],
    )
    email.send(fail_silently=False)


@shared_task
def convert_selected_students_to_alumni_task(student_ids, program_id):
    """
    For each student in student_ids, mark all their enrollments in program_id as Alumnus and
    create Alumni records if not existing. Then, if the student has no other active enrollments
    in ANY program, remove the 'Student' role from user and add 'Alumnus' role.
    Finally, send a 'You are now an alumnus' email.
    """
    from django.db.models import Q

    try:
        program = Program.objects.get(pk=program_id, flag=True)
    except Program.DoesNotExist:
        # Program not found or not flagged
        return

    # Roles for convenience
    alumnus_role, _ = Role.objects.get_or_create(name='Alumnus')
    student_role, _ = Role.objects.get_or_create(name='Student')

    with transaction.atomic():
        for sid in student_ids:
            try:
                student = StudentDetail.objects.get(pk=sid)
            except StudentDetail.DoesNotExist:
                continue

            # 1) Mark all enrollments of this student in THIS program as Alumnus
            enrollments = StudentEnrollment.objects.filter(
                student=student,
                program=program,
                active=True
            )
            if not enrollments.exists():
                # No enrollments to mark in this program
                continue

            # Mark them as alumnus
            for enroll in enrollments:
                if enroll.status != "Alumnus":
                    enroll.status = "Alumnus"
                enroll.active = False
                enroll.save()

            # 2) Check if the student has any other active enrollment in ANY program
            still_active = StudentEnrollment.objects.filter(
                student=student,
                active=True
            ).exists()

            # 3) If no more active enrollments across all programs, remove Student role, add Alumnus role
            if not still_active:
                # remove student role
                if student.user:
                    if student_role.group and student_role.group in student.user.groups.all():
                        student.user.groups.remove(student_role.group)
                    # also remove the role from the M2M
                    student.user.roles.remove(student_role)
                    # add alumnus role
                    student.user.roles.add(alumnus_role)
                    if alumnus_role.group:
                        student.user.groups.add(alumnus_role.group)
                    student.user.save()

            # 4) Create (or update) an Alumni record for each
            #    We'll use the first enrollment's end_date or 'N/A'
            year_of_completion = 'N/A'
            first_enrollment = enrollments.first()
            if first_enrollment.end_date:
                year_of_completion = str(first_enrollment.end_date.year)

            defaults = {
                'first_name': student.first_name,
                'last_name': student.last_name,
                'email': student.email,
                'year_of_completion': year_of_completion,
                'current_position': student.position or '',
                'company': student.company or '',
                'industry': 'Tech',  # or your default
                'picture': student.image,
            }
            alumnus_obj, created = Alumni.objects.get_or_create(
                student=student,
                user=student.user,
                program=program,
                defaults=defaults
            )

            # 5) Send email
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
                # If sending fails, we log or ignore
                pass

    # Done
    return


@shared_task(name="facilitator.send_facilitator_email")
def send_facilitator_email(course_id, subject, message):
    """
    Sends a custom email to all participants of the course.
    """
    course = Course.objects.get(id=course_id)
    participants = CourseParticipant.objects.filter(course=course, flag=True)
    # Build email context
    context = {
        'course': course,
        'message': message,
        'current_time': timezone.now(),
    }
    email_body = render_to_string('facilitator/emails/course_notification.html', context)
    for participant in participants:
        recipient_email = participant.email_address
        if recipient_email:
            email = EmailMessage(
                subject=subject,
                body=email_body,
                to=[recipient_email]
            )
            email.content_subtype = 'html'
            email.send(fail_silently=False)


@shared_task(name="account.send_password_reset_email")
def send_password_reset_email(user_id):
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return
    domain = get_domain()  # Make sure DOMAIN is defined in your settings (e.g., "yourdomain.com")
    reset_link = f"https://{domain}" + reverse('account:password_reset')
    context = {
        'user': user,
        'password_reset_link': reset_link,
        'dashboard_link': f"https://{domain}" + reverse('students:student_portal'),
        'current_time': timezone.now(),
    }
    email_body = render_to_string('account/emails/welcome_email.html', context)
    email = EmailMessage(
        subject=f"Welcome to CEIBS Africa Online – Set Your Password",
        body=email_body,
        to=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task(name="academic_program.send_course_assignment_email")
def send_course_assignment_email(course_id, lecturer_id):
    try:
        course = Course.objects.get(id=course_id)
        lecturer = CustomUser.objects.get(pk=lecturer_id)
    except (Course.DoesNotExist, CustomUser.DoesNotExist):
        return

    domain = get_domain()  # E.g., "yourdomain.com"
    program_link = f"https://{domain}" + reverse('academic_program:student_list', args=[course.program.program_name, course.program.program_type.name])
    context = {
        'lecturer': lecturer,
        'course': course,
        'program': course.program,
        'program_link': program_link,
        'current_time': timezone.now(),
    }
    email_body = render_to_string('academic_program/emails/course_assignment.html', context)
    email = EmailMessage(
        subject=f"You have been assigned to course: {course.course_name}",
        body=email_body,
        to=[lecturer.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)

























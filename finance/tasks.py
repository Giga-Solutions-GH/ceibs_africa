# finance/tasks.py
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from academic_program.models import Program, Course, CourseParticipant
from account.models import CustomUser
from finance.models import StudentFinance, AdmissionFinance  # Adjust the import path as necessary
from marketing.models import Admission
from student_grading.models import StudentGrade
from students.models import StudentDetail, StudentEnrollment
from students.tasks import send_student_welcome_email
from academic_program.tasks import send_student_enrollment_email


def get_domain():
    # Return your domain; adjust for production.
    return '6295-41-66-237-210.ngrok-free.app'


@shared_task(name="send_finance_receipt_email")
def send_finance_receipt_email(finance_id):
    """
    Sends a finance receipt email to the student associated with the given StudentFinance record.
    The email includes details about total fees, amount paid, percentage cleared, and balance remaining.
    """
    try:
        finance_record = AdmissionFinance.objects.get(pk=finance_id)
    except StudentFinance.DoesNotExist:
        return

    # Retrieve total fee using the related FinanceStatement and ProgramFees
    total_fee = finance_record.fees.program_fees.fee or 0.0
    fees_paid = finance_record.fees_paid or 0.0
    balance = total_fee - fees_paid
    percentage = (fees_paid / total_fee * 100) if total_fee > 0 else 0.0

    # Build a link to the student dashboard (adjust 'students:student_portal' as needed)
    domain = get_domain()

    context = {
        'student': finance_record.student,
        'total_fee': total_fee,
        'fees_paid': fees_paid,
        'balance': balance,
        'percentage': percentage,
        'current_time': timezone.now(),
        'finance_record': finance_record
    }

    subject = f"Your Payment Receipt from CEIBS Africa Online"
    email_body = render_to_string('finance/layouts/emails/finance_receipt.html', context)
    email = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[finance_record.student.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def convert_admission_to_student(admission_id):
    """
    Converts an Admission (whose finance status is cleared) into a Student.
    This includes:
      - Creating a StudentDetail record.
      - Creating a CustomUser for the student.
      - Enrolling the student in the active program.
      - Creating CourseParticipant records for all courses.
      - Creating a StudentFinance record (transferring admission finance).
      - Creating StudentGrade records for all courses.
      - Sending a welcome email with a password reset link.
    """
    from django.db import transaction
    try:
        with transaction.atomic():
            admission = Admission.objects.select_for_update().get(id=admission_id)
            # Create the StudentDetail record.
            student_detail = StudentDetail.objects.create(
                first_name=admission.first_name,
                last_name=admission.last_name,
                other_names=admission.other_names,
                email=admission.email,
                phone_number=admission.phone_number,
                nationality=admission.nationality,
                gender=admission.gender,
                date_of_birth=admission.date_of_birth,
                position=admission.position,
                company=admission.company
                # Add any other fields as required.
            )
            # Create a CustomUser for the student.
            user = CustomUser.objects.create_user(
                email=admission.email,
                password=None,  # No password; a reset email will be sent.
                first_name=admission.first_name,
                last_name=admission.last_name,
            )
            # Link the student detail to the user.
            student_detail.user = user
            student_detail.save()

            # Enroll the student in the active program.
            active_program = Program.objects.get(
                program_cover=admission.program_of_interest,
                flag=True,
                program_ended=False,
            )
            enrollment = StudentEnrollment.objects.create(
                student=student_detail,
                program=active_program,
                start_date=active_program.start_date,
                end_date=active_program.end_date,
                active=True,
            )

            # Enroll the student in all courses under the active program.
            courses = Course.objects.filter(program=active_program)
            for course in courses:
                CourseParticipant.objects.create(
                    course=course,
                    student=enrollment
                )

            admission_finance = AdmissionFinance.objects.get(student=admission, active=True)

            # Create a StudentFinance record for the student.
            student_finance = StudentFinance.objects.create(
                student=student_detail,
                fees=admission_finance.fees,  # Transfer the FinanceStatement from admission finance.
                fees_paid=admission_finance.fees_paid,
            )
            # The save() method on StudentFinance recalculates percentage and balance.

            # Create StudentGrade records for all courses with initial score 0.
            for course in courses:
                StudentGrade.objects.create(
                    student=student_detail,
                    course=course,
                    program=active_program,
                    student_score=0
                )

            # Mark the admission as completed.
            admission.status = 'admission_completed'
            admission.last_update = timezone.now()
            admission.save()

            domain = get_domain()

            # Trigger a welcome email to the student with the password reset link.
            send_student_welcome_email.delay(user.id)
            send_student_enrollment_email.delay(user.id, active_program.id)

            # Optionally, send an email notifying them that their admission has been converted.
            # (Assume send_admission_conversion_complete_email is defined in tasks.)
            # send_admission_conversion_complete_email.delay(user.id, active_program.program_name)

    except Exception as e:
        # Log the exception as needed.
        print("Error converting admission to student:", e)
        raise e























from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

from marketing.models import Admission, Prospect
from marketing.utils import get_progress_for_status

User = get_user_model()


@shared_task
def send_student_welcome_email_task(user_id, dashboard_link, reset_link):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    context = {
        'user': user,
        'dashboard_link': dashboard_link,
        'reset_link': reset_link,
        'current_time': timezone.now(),
    }
    subject = f"Welcome to CEIBS Africa - Set Your Password"
    body = render_to_string('marketing/emails/student_welcome_email.html', context)
    email = EmailMessage(subject=subject, body=body, to=[user.email])
    email.content_subtype = "html"
    email.send(fail_silently=False)


@shared_task
def send_admission_document_request_email(admission_id):
    try:
        admission = Admission.objects.get(id=admission_id)
    except Admission.DoesNotExist:
        return  # If admission record no longer exists, do nothing

    domain = "6295-41-66-237-210.ngrok-free.app"  # e.g. 'ceibs-africa.example.com'
    # Build the upload documents URL (make sure you have this URL pattern defined)
    upload_url = f"https://{domain}" + reverse('admission:admissions_document_upload', args=[admission.id])

    context = {
        'admission': admission,
        'upload_url': upload_url,
        'current_time': timezone.now(),
    }
    email_body = render_to_string('marketing/admissions/emails/admission_document_request.html', context)
    email = EmailMessage(
        subject="CEIBS Africa - Please Upload Your Admission Documents",
        body=email_body,
        to=[admission.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def send_admission_request_email_task(prospect_id, admission_request_url):
    try:
        prospect = Prospect.objects.get(id=prospect_id)
    except Prospect.DoesNotExist:
        return

    context = {
        'prospect': prospect,
        'admission_request_url': admission_request_url,
        'current_time': timezone.now(),
    }

    email_body = render_to_string('marketing/emails/admission_request_email.html', context)
    email = EmailMessage(
        subject="CEIBS Africa Online - Admission Documents Request",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[prospect.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)



@shared_task
def send_admission_confirmation_email_task(admission_id):
    from marketing.models import Admission
    try:
        admission = Admission.objects.get(id=admission_id)
    except Admission.DoesNotExist:
        return

    domain = "6295-41-66-237-210.ngrok-free.app"  # Replace with your domain or use get_domain() if defined
    # dashboard_link = f"https://{domain}" + reverse('marketing:admission_dashboard')
    context = {
        'admission': admission,
        # 'dashboard_link': dashboard_link,
        'current_time': timezone.now(),
    }
    email_body = render_to_string('marketing/emails/admission_confirmation.html', context)
    email = EmailMessage(
        subject="Your Admission Documents Have Been Received",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admission.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task
def send_admission_status_update_email(admission_id):
    try:
        admission = Admission.objects.get(id=admission_id)
    except Admission.DoesNotExist:
        return

    progress = get_progress_for_status(admission.status)
    context = {
        'admission': admission,
        'progress': progress,
    }
    email_body = render_to_string('marketing/emails/admission_status_update.html', context)
    email = EmailMessage(
        subject=f"Your Admission Status Updated: {admission.get_status_display()}",
        body=email_body,
        to=[admission.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)











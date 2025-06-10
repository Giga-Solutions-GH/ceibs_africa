from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from account.models import CustomUser

User = get_user_model()


def get_domain():
    return '6295-41-66-237-210.ngrok-free.app'


@shared_task(name="account.send_login_notification")
def send_login_notification(user_id, ip_address):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return  # User no longer exists

    domain = get_domain()
    # Build a clickable password reset URL
    password_reset_url = f"https://{domain}" + reverse('account:password_reset')

    context = {
        'user': user,
        'ip_address': ip_address,
        'current_time': timezone.now(),
        'password_reset_link': password_reset_url,
    }

    # Render HTML template
    email_body = render_to_string('account/emails/login_notification.html', context)
    email = EmailMessage(
        subject="New Login Detected on Your Account",
        body=email_body,
        to=[user.email]
    )
    # Set the email content subtype to HTML
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task(name="account.send_welcome_email")
def send_welcome_email(user_id, code):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    domain = get_domain()
    dashboard_link = f"https://{domain}" + reverse('students:student_portal')

    context = {
        'user': user,
        'dashboard_link': dashboard_link,
        'code': code
    }

    # Render the HTML template instead of text
    email_body = render_to_string('account/emails/welcome_email.html', context)

    email = EmailMessage(
        subject=f"Welcome to Our App, {user.email}!",
        body=email_body,
        to=[user.email]
    )
    # Set the content subtype to html
    email.content_subtype = 'html'
    email.send(fail_silently=False)


@shared_task(name="account.send_password_reset_code_email")
def send_password_reset_code_email(user_id, code):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return  # User no longer exists; no email to send.

    context = {
        'user': user,
        'code': code
    }
    email_body = render_to_string('account/emails/password_reset_code.txt', context)
    email = EmailMessage(
        subject="Your Password Reset Code",
        body=email_body,
        to=[user.email],
    )
    email.send(fail_silently=False)


@shared_task(name="account.send_profile_verification_code_email")
def send_profile_verification_code_email(email, code):
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string

    context = {'code': code}
    email_body = render_to_string('account/emails/profile_change_verification.txt', context)
    email_msg = EmailMessage(
        subject="Confirm Your Profile Changes",
        body=email_body,
        to=[email],
    )
    email_msg.send(fail_silently=False)


@shared_task(name="account.send_email_verification_code")
def send_email_verification_code(email, code):
    context = {'code': code}
    email_body = render_to_string('account/emails/email_verification.txt', context)
    email_msg = EmailMessage(
        subject="Verify Your Email Address",
        body=email_body,
        to=[email],
    )
    email_msg.send(fail_silently=False)


@shared_task
def send_new_user_welcome_email(user_id):
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return

    domain = get_domain()  # For example, 'ceibs-africa.com'
    password_reset_url = f"https://{domain}" + reverse('account:password_reset')
    # Gather role and department information.
    roles = ", ".join([role.name for role in user.roles.all()])
    departments = ", ".join([role.department.name for role in user.roles.all() if role.department])
    dashboard_link = f"https://{domain}" + reverse('students:student_portal')

    context = {
        'user': user,
        'password_reset_link': password_reset_url,
        'dashboard_link': dashboard_link,
        'roles': roles,
        'email': user.email,
        'departments': departments,
        'current_time': timezone.now(),
    }
    email_body = render_to_string('account/emails/new_user_welcome_email.html', context)
    email = EmailMessage(
        subject=f"Welcome to CEIBS Africa Online - Set Your Password",
        body=email_body,
        to=[user.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)








import random

from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from account.forms import VerificationCodeForm, CustomAuthenticationForm, PasswordResetRequestForm, \
    PasswordResetConfirmForm
from account.models import EmailVerificationCode, CustomUser, PasswordResetCode
from account.tasks import send_email_verification_code, send_login_notification, send_password_reset_code_email

import logging

logger = logging.getLogger(__name__)


# Create your views here.
def get_client_ip(request):
    """Helper function to reliably get the client's IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', None)
    return ip


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Log out successful")
        return redirect(reverse_lazy('account:login'))


class VerifyEmailView(FormView):
    template_name = 'account/verify_email.html'
    form_class = VerificationCodeForm
    success_url = reverse_lazy('account:login')

    def dispatch(self, request, *args, **kwargs):
        # If user is logged in and already verified, go to dashboard
        if request.user.is_authenticated and request.user.email_verified:
            return redirect('hub_app:dashboard')
        # If not authenticated at all
        if not request.user.is_authenticated:
            messages.warning(request, "You must be logged in to verify your email.")
            return redirect('account:login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user

        # Check if user requested a resend
        if 'resend' in request.GET:
            return self.handle_resend(user)

        # Try to get the existing code
        verification = EmailVerificationCode.objects.filter(user=user).first()

        # If no code or code is expired, generate a new one
        if not verification or verification.is_expired():
            EmailVerificationCode.objects.filter(user=user).delete()
            code = ''.join(str(random.randint(0, 9)) for _ in range(6))
            verification = EmailVerificationCode.objects.create(user=user, code=code)
            send_email_verification_code.delay(user.email, code)
            messages.info(request, "A new verification code has been sent to your email.")

        # At this point, we have a valid code (not expired) or just re-sent it
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        code = form.cleaned_data['code']
        user = self.request.user

        try:
            verification = EmailVerificationCode.objects.get(user=user, code=code)
        except EmailVerificationCode.DoesNotExist:
            # Invalid code (maybe old code) - let user know to re-check email or resend
            messages.error(self.request, "Invalid verification code. Please ensure you are using the latest code sent.")
            return self.form_invalid(form)

        if verification.is_expired():
            verification.delete()
            messages.error(self.request, "The verification code has expired. Please refresh or resend a new code.")
            return self.form_invalid(form)

        # Mark user as verified
        user.email_verified = True
        user.save()
        verification.delete()
        messages.success(self.request, "Your email has been verified. You can now log in.")
        # Log the user out to force them to re-login as verified
        logout(self.request)
        return super().form_valid(form)

    def handle_resend(self, user):
        # Handle the "resend code" logic
        verification = EmailVerificationCode.objects.filter(user=user).first()

        # If no verification code, create a new one
        if not verification:
            code = ''.join(str(random.randint(0, 9)) for _ in range(6))
            verification = EmailVerificationCode.objects.create(user=user, code=code)
            send_email_verification_code.delay(user.email, verification.code)
            messages.success(self.request, "A new verification code has been sent to your email.")
            return redirect('account:verify_email')

        # Check if 2 minutes have passed since last code was sent
        elapsed = (timezone.now() - verification.created_at).total_seconds()
        if elapsed < 120:  # less than 2 minutes
            wait_time = 120 - int(elapsed)
            messages.error(self.request, f"Please wait {wait_time} more seconds before resending the code.")
            return redirect('account:verify_email')

        # Otherwise, resend a new code
        verification.delete()
        code = ''.join(str(random.randint(0, 9)) for _ in range(6))
        EmailVerificationCode.objects.create(user=user, code=code)
        send_email_verification_code.delay(user.email, code)
        messages.success(self.request, "A new verification code has been sent to your email.")
        return redirect('account:verify_email')


class CustomUserLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'account/login.html'
    success_url = reverse_lazy('hub_app:dashboard')  # Default fallback

    def form_valid(self, form):
        user = form.get_user()
        if not user.email_verified:
            messages.warning(self.request, "Please verify your email before logging in.")
            # Log user in but unverified - redirect to verify email page
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            return redirect('account:verify_email')

        messages.success(self.request, "You have successfully logged in.")
        response = super().form_valid(form)
        # Send login notification
        ip_address = get_client_ip(self.request)
        send_login_notification.delay(user.id, ip_address)
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user  # No need to query again
        if user.is_student:
            return reverse_lazy('students:student_portal')  # Replace with actual student dashboard URL name
        return reverse_lazy('elevated:home')  # Redirect for other users


class PasswordResetRequestView(FormView):
    template_name = 'account/password/forgot-password.html'
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy('account:password_reset_confirm')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.success(self.request, "A verification code has been sent to your email address if it exists.")
            # messages.error(self.request, "No account is associated with that phone number.")
            # return self.form_invalid(form)
            return redirect('account:password_reset_confirm')

        # Generate a 6-digit random code
        code = ''.join(str(random.randint(0, 9)) for _ in range(6))

        # Store the code in the database
        PasswordResetCode.objects.create(user=user, code=code)

        # Send the email asynchronously via Celery
        try:
            send_password_reset_code_email.delay(user.id, code)
        except Exception as e:
            logger.error(f'Failed to initiate sending password reset code email to {user.email}: {e}')
            messages.error(self.request, "Failed to queue the reset code email. Please try again later.")
            return self.form_invalid(form)

        messages.success(self.request, "A verification code has been sent to your email address if it exists.")
        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    template_name = 'account/password/password_reset_confirm.html'
    form_class = PasswordResetConfirmForm
    success_url = reverse_lazy('account:login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        code = self.request.POST.get('code', None)
        try:
            reset_code = PasswordResetCode.objects.get(code=code, is_used=False)
            kwargs['user'] = reset_code.user
        except PasswordResetCode.DoesNotExist:
            kwargs['user'] = None
        return kwargs

    def form_valid(self, form):
        code = form.cleaned_data['code']
        new_password = form.cleaned_data['new_password1']
        confirm_password = form.cleaned_data['new_password2']

        try:
            reset_code = PasswordResetCode.objects.get(code=code, is_used=False)
        except PasswordResetCode.DoesNotExist:
            messages.warning(self.request, "Invalid or expired code.")
            return self.form_invalid(form)

        # Use the is_expired property here
        if reset_code.is_expired:
            messages.warning(self.request, "The code has expired.")
            return self.form_invalid(form)

        user = reset_code.user
        user.set_password(new_password)
        user.email_verified = True
        user.is_active = False
        user.save()

        # Mark the code as used or delete it
        reset_code.is_used = True
        reset_code.save()

        messages.success(self.request, "Your password has been reset successfully. Log in to continue")
        return super().form_valid(form)



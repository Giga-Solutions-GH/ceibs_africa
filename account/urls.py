from django.urls import path
from .views import (
    CustomUserLoginView,
    CustomLogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView, VerifyEmailView,
)

app_name = "account"

urlpatterns = [
    path('login/', CustomUserLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

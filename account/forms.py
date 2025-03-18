import secrets

from django import forms
from django.contrib.auth.forms import SetPasswordForm, AuthenticationForm

from account.models import CustomUser


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(
                                attrs={'placeholder': 'Enter your email', 'class': 'form-control'}))



class PasswordResetConfirmForm(SetPasswordForm):
    code = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter the 6-digit code sent to your phone',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(self.user, *args, **kwargs)
        # Add Bootstrap form-control to all fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        # Remove default password criteria help text
        self.fields['new_password1'].help_text = ""
        self.fields['new_password2'].help_text = ""



class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(
        attrs={'autofocus': True, 'class': 'form-control form-control-lg', 'placeholder': 'E-mail'}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-lg', 'placeholder': 'Password'}))


class VerificationCodeForm(forms.Form):
    code = forms.CharField(max_length=6, required=True, label="Verification Code",
                           widget=forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': 'Enter verification code'
                           }))


class CustomUserCreationForm(forms.ModelForm):
    """
    A form for creating new users without requiring the admin to set the password.
    The password is auto-generated and a password reset email will be sent.
    """
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'username', 'roles')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Generate a random password
        random_password = secrets.token_hex(2)
        user.set_password(random_password)
        if commit:
            user.save()
        return user





from django import forms

from academic_program.models import Program
from marketing.models import Prospect, ProspectFeedback, Admission, AdmissionDocument


class AddProspectForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'First Name'}))
    last_name = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Last Name'}))
    other_names = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Other Names'}), required=False)
    phone_number = forms.CharField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    company = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Company'}))
    position = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Position'}))
    comments = forms.CharField(widget=forms.Textarea(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Comments', 'required': False}), required=False)

    class Meta:
        model = Prospect
        fields = ('first_name', 'last_name', 'other_names', 'phone_number', 'email', 'company', 'position', 'comments')


class AddProspectFeedback(forms.ModelForm):
    prospect = forms.ModelChoiceField(queryset=Prospect.objects.all(), empty_label=None,
                                      widget=forms.Select(
                                          attrs={'class': 'form-control', 'placeholder': 'Notice Title'}))
    feedback = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Feedback on reaching prospective'}))

    class Meta:
        model = ProspectFeedback
        fields = ('prospect', 'feedback')


class ProspectToStudentForm(forms.Form):
    first_name = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'First Name', 'autofocus': True}))
    last_name = forms.CharField(
        widget=forms.TextInput(
            {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Last Name'}))
    other_names = forms.CharField(
        widget=forms.TextInput(
            {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Other Names'}))
    email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone_number = forms.CharField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    date_of_birth = forms.CharField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'autofocus': True, 'type': 'date'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    student_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    company = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}),
                               choices=(("Male", "Male"), ("Female", "Female")))
    program = forms.ModelChoiceField(queryset=Program.objects.filter(flag=True), empty_label=None, widget=forms.Select(attrs={'class': 'form-control'}))


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['first_name', 'last_name', 'other_names', 'phone_number', 'email', 'company', 'position', 'comments']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter other names (if any)'}),
            'phone_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company or organization'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter position'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comments about the prospect'}),
        }


class AdmissionDocumentForm(forms.ModelForm):
    class Meta:
        model = AdmissionDocument
        fields = ['certificate', 'transcript', 'other_document']
        widgets = {
            'certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'transcript': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'other_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }















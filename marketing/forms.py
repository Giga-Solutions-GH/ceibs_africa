from django import forms
from academic_program.models import Program, ProgramCover
from marketing.models import Prospect, ProspectFeedback, Admission


# -------------------------------
# Prospect Form
# -------------------------------
class AddProspectForm(forms.ModelForm):
    class Meta:
        model = Prospect
        fields = [
            'first_name',
            'last_name',
            'other_names',
            'phone_number',
            'email',
            'company',
            'position',
            'comments'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'Last Name'
            }),
            'other_names': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'Other Names'
            }),
            'phone_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'Company'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'Position'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'Additional Comments',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super(AddProspectForm, self).__init__(*args, **kwargs)
        # Only require first name, last name, and email.
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        # Other fields are optional.
        self.fields['other_names'].required = False
        self.fields['phone_number'].required = False
        self.fields['company'].required = False
        self.fields['position'].required = False
        self.fields['comments'].required = False


# -------------------------------
# Prospect Feedback Form
# -------------------------------
class AddProspectFeedbackForm(forms.ModelForm):
    class Meta:
        model = ProspectFeedback
        fields = ['prospect', 'feedback']
        widgets = {
            'prospect': forms.Select(attrs={'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter feedback',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super(AddProspectFeedbackForm, self).__init__(*args, **kwargs)
        self.fields['feedback'].required = False


# -------------------------------
# Prospect to Student Conversion Form
# -------------------------------
class ProspectToStudentForm(forms.Form):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            'placeholder': 'First Name',
            'autofocus': True
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            'placeholder': 'Last Name'
        })
    )
    other_names = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            'placeholder': 'Other Names'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Address'
        })
    )
    student_id = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Student ID'
        })
    )
    company = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company'
        })
    )
    position = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Position'
        })
    )
    gender = forms.ChoiceField(
        required=False,
        choices=(("Male", "Male"), ("Female", "Female")),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(flag=True),
        required=True,
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = [
            'first_name',
            'last_name',
            'other_names',
            'date_of_birth',
            'phone_number',
            'email',
            'company',
            'position',
            'comments',
            'program_of_interest',
            'passport_picture',
            'passport_front_page',
            'certificate_files',
            'transcript_files',
            'other_files',
            'cv',
            'status'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'other_names': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter other names (optional)'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your date of birth'
            }),
            'phone_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company or organization'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter position'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Any additional comments (optional)',
                'rows': 3
            }),
            'passport_picture': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'passport_front_page': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'transcript_files': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'certificate_files': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'other_files': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'cv': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'program_of_interest': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super(AdmissionForm, self).__init__(*args, **kwargs)
        # Make only first name, last name, and email required.
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        # All other fields are optional.
        self.fields['other_names'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['phone_number'].required = False
        self.fields['company'].required = True
        self.fields['position'].required = True
        self.fields['program_of_interest'].required = True
        self.fields['comments'].required = False
        self.fields['passport_picture'].required = True
        self.fields['passport_front_page'].required = True
        self.fields['certificate_files'].required = False
        self.fields['transcript_files'].required = False
        self.fields['other_files'].required = False
        self.fields['cv'].required = True


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


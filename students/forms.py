from django import forms

from students.models import StudentEnrollment, StudentDetail


class AddStudentDetailForm(forms.Form):
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    other_names = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Other Names', 'required': False}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gender = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}),
                               choices=(("Male", "Male"), ("Female", "Female")))
    unique_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unique ID'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
                             required=False)
    phone_number = forms.CharField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    position = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
                               required=False)
    next_of_kin = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Next of Kin'}),
                                  required=False)


class StudentDetailForm(forms.ModelForm):
    class Meta:
        model = StudentDetail
        fields = [
            'image', 'first_name', 'last_name', 'other_names', 'date_of_birth',
            'gender', 'unique_id', 'email', 'phone_number', 'address', 'company', 'position'
        ]
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'unique_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StudentEnrollmentForm(forms.ModelForm):
    class Meta:
        model = StudentEnrollment
        fields = ['student', 'program', 'start_date', 'end_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class EnrollmentStatusForm(forms.ModelForm):
    class Meta:
        model = StudentEnrollment
        fields = ['status']
        widgets = {
            'status': forms.Select(choices=StudentEnrollment.choices, attrs={'class': 'form-control'}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = StudentDetail
        fields = ['first_name', 'last_name', 'other_names', 'date_of_birth', 'gender', 'unique_id', 'email',
                  'phone_number', 'address', 'position', 'company', 'image']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'unique_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class EditStudentContactForm(forms.Form):
    phone_number = forms.CharField(max_length=20)
    email = forms.EmailField()
    company = forms.CharField(max_length=300)
    position = forms.CharField(max_length=250)
























from django import forms

from academic_program.models import Lecturer, LecturerType, Course, ProgramParticipant, Attendance, ProgramSchedule, \
    ProgramScheduleDate
from students.models import StudentDetail


class LecturerForm(forms.ModelForm):
    lecturer_type = forms.ModelChoiceField(
        queryset=LecturerType.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Lecturer
        fields = ['first_name', 'last_name', 'other_names', 'title', 'email', 'phone_number', 'lecturer_type', 'image']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class CourseAssignmentForm(forms.Form):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Courses"
    )


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


class ProgramParticipantForm(forms.ModelForm):
    class Meta:
        model = ProgramParticipant
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'company', 'position']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['is_present', 'comment']
        widgets = {
            'is_present': forms.CheckboxInput(),
            'comment': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        student_enrollment = kwargs.pop('student_enrollment', None)
        super().__init__(*args, **kwargs)
        if student_enrollment:
            # Add the student field as a hidden input and set its initial value
            self.fields['student'] = forms.CharField(
                widget=forms.HiddenInput(), initial=student_enrollment.id
            )


class ProgramScheduleForm(forms.ModelForm):
    session_dates = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control multidate-picker',
            'placeholder': 'Select multiple dates'
        }),
        required=False,
        help_text="Select multiple dates using the calendar widget (separate by commas or newlines)."
    )

    class Meta:
        model = ProgramSchedule
        fields = ['course', 'location', 'start_time', 'end_time', 'start_date', 'end_date', 'session_dates']

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)
        if program:
            self.fields['course'].queryset = Course.objects.filter(program=program, flag=True)
        self.fields['course'].widget.attrs.update({'class': 'form-control'})
        self.fields['location'].widget.attrs.update({'class': 'form-control'})
        self.fields['start_time'].widget = forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        self.fields['end_time'].widget = forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        self.fields['start_date'].widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        self.fields['end_date'].widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})

        # If editing an existing schedule, pre-populate session_dates with existing dates
        if self.instance and self.instance.pk:
            existing_dates = self.instance.schedule_dates.all().order_by('session_date')
            if existing_dates.exists():
                # Join the dates as a comma-separated string
                dates_str = ", ".join([d.session_date.strftime("%Y-%m-%d") for d in existing_dates])
                self.fields['session_dates'].initial = dates_str

































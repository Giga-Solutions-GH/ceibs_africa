from django import forms

from events.models import EventParticipant, Event


class AddEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'description',
            'duration',
            'start_time',
            'end_time',
            'number_of_participants',
            'venue',
            'event_type',
            'department',
            'presence',
            'event_contact_name',
            'event_contact_email',
            'event_contact_phone',
            'company',
            'comments',
            'event_image',
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'number_of_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'presence': forms.Select(attrs={'class': 'form-control'}),
            'event_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'event_contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'event_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control'}),
            'event_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(AddEventForm, self).__init__(*args, **kwargs)
        # Ensure all fields have the 'form-control' class.
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
        # Make department and company fields optional.
        self.fields['department'].required = False
        self.fields['company'].required = False

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.user = user
        # Calculate duration using the model's method.
        instance.duration = instance.calculate_duration()
        if commit:
            instance.save()
        return instance


class UploadParticipantsForm(forms.Form):
    participants_excel = forms.FileField()


class AddEventParticipantForm(forms.ModelForm):
    class Meta:
        model = EventParticipant
        fields = ['last_name', 'first_name', 'other_names', 'phone_contact', 'email_address', 'company', 'position']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'required': False}, ),
            'phone_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EventParticipantForm(forms.ModelForm):
    class Meta:
        model = EventParticipant
        fields = [
            'first_name', 'last_name', 'other_names',
            'phone_contact', 'email_address', 'company', 'position'
        ]

    def __init__(self, *args, **kwargs):
        super(EventParticipantForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

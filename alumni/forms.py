from django import forms

from academic_program.models import Program
from alumni.models import Alumni


class AddAlumniForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(
        {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'First Name', 'autofocus': True}))
    last_name = forms.CharField(
        widget=forms.TextInput(
            {'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Last Name'}))
    email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    program = forms.ModelChoiceField(queryset=Program.objects.filter(alumni_program=True), empty_label=None,
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    year_of_completion = forms.CharField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'autofocus': True, 'type': 'month'}))
    current_position = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current position'}))
    company = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}))
    industry = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Industry'}))
    picture = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Image'}),
                               required=False)
    nationality = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}))
    country_of_residence = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country of residence'}))

    class Meta:
        model = Alumni
        fields = (
            'first_name', 'last_name', 'email', 'picture', 'program', 'year_of_completion', 'current_position',
            'company',
            'industry', 'nationality', 'country_of_residence')


class AlumniForm(forms.ModelForm):
    class Meta:
        model = Alumni
        fields = [
            'first_name', 'last_name', 'email', 'program',
            'year_of_completion', 'current_position', 'company',
            'industry', 'picture', 'nationality', 'country_of_residence'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'year_of_completion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Year of Completion'}),
            'current_position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current Position'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company'}),
            'industry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Industry'}),
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'country_of_residence': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Country of Residence'}),
        }






























from django import forms

from student_grading.models import StudentGrade, GradeSystem


class GradeEntryForm(forms.ModelForm):
    class Meta:
        model = StudentGrade
        fields = ['student', 'course', 'student_score', 'id']
        widgets = {
            'student': forms.HiddenInput(),
            'course': forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'student_score': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'class': 'form-control score-input',  # We'll use "score-input" for AJAX
                'placeholder': 'Enter Score (0-100)'
            }),
        }

    def clean_student_score(self):
        score = self.cleaned_data.get('student_score', 0)
        if score < 0 or score > 100:
            raise forms.ValidationError("Score must be between 0 and 100.")
        return score

    def save(self, commit=True):
        """
        Override save to automatically compute and assign the `grade`
        based on your GradeSystem (assuming your models require that).
        """
        instance = super().save(commit=False)
        # Find the GradeSystem record that matches this score
        # (assuming you store min_score, max_score, grade, remarks)
        if instance.student_score is not None:
            possible_grades = GradeSystem.objects.all()
            # Find a grade range that fits
            for g in possible_grades:
                if g.min_score <= instance.student_score <= g.max_score:
                    instance.grade = g
                    break
        if commit:
            instance.save()
        return instance

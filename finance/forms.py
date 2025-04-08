from django import forms

from finance.models import ProgramFees, FinanceStatement


class FinanceAdmissionForm(forms.Form):
    fees_paid = forms.FloatField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'step': 0.01
        }),
        label="Update Fees Paid"
    )
    payment_method = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Payment Method",
        choices=[
            ('', '--Select Payment Method--'),
            ('Direct Payment', 'Direct Payment'),
            ('Bank', 'Bank'),
            ('Other', 'Other')
        ],
        required=False
    )
    status_update = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Update Admission Status",
        choices=[
            ('', '--Select New Status--'),
            ('awaiting_financial_clearance', 'Awaiting Financial Clearance'),
            ('student_cleared_financially', 'Student Cleared Financially'),
            ('admission_completed', 'Admission Completed'),
            ('rejected', 'Rejected'),
        ],
        required=False
    )


class ProgramFeesForm(forms.ModelForm):
    class Meta:
        model = ProgramFees
        fields = ['fee']
        widgets = {
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class FinanceStatementForm(forms.ModelForm):
    class Meta:
        model = FinanceStatement
        fields = ['payment_options']
        widgets = {
            'payment_options': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter payment options'}),
        }



















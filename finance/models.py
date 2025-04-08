import uuid

from django.db import models

from academic_program.models import Program


# Create your models here.
class ProgramFees(models.Model):
    program = models.ForeignKey('academic_program.Program', on_delete=models.CASCADE)
    fee = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.program} - {self.fee}"


class FinanceStatement(models.Model):
    program_fees = models.ForeignKey('ProgramFees', on_delete=models.CASCADE)
    payment_options = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.program_fees.program.program_name


class StudentFinance(models.Model):
    student = models.ForeignKey('students.StudentDetail', on_delete=models.CASCADE)
    fees_paid = models.FloatField(null=True, blank=True, default=0.0)
    fees = models.ForeignKey(FinanceStatement, on_delete=models.CASCADE)
    percentage_cleared = models.FloatField(null=True, blank=True, default=0.0)
    student_balance = models.FloatField(null=True, blank=True, default=0.0)

    def __str__(self):
        return f"{self.student}"

    def save(self, *args, **kwargs):
        # Retrieve total fee from the linked FinanceStatement via ProgramFees.
        total_fee = self.fees.program_fees.fee or 0.0
        # Calculate the balance: total fee minus what has been paid.
        self.student_balance = total_fee - self.fees_paid
        # Update percentage cleared, only if total_fee is non-zero.
        if total_fee > 0:
            self.percentage_cleared = (self.fees_paid / total_fee) * 100
        else:
            self.percentage_cleared = 0.0
        super().save(*args, **kwargs)


class AdmissionFinance(models.Model):
    student = models.ForeignKey('marketing.Admission', on_delete=models.CASCADE, related_name='admission_finance')
    fees_paid = models.FloatField(null=True, blank=True, default=0.0)
    fees = models.ForeignKey(FinanceStatement, on_delete=models.CASCADE)
    percentage_cleared = models.FloatField(null=True, blank=True, default=0.0)
    student_balance = models.FloatField(null=True, blank=True, default=0.0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student}"

    def save(self, *args, **kwargs):
        # Retrieve total fee from the linked FinanceStatement via ProgramFees.
        total_fee = self.fees.program_fees.fee or 0.0
        # Calculate the balance: total fee minus what has been paid.
        self.student_balance = total_fee - self.fees_paid
        # Update percentage cleared, only if total_fee is non-zero.
        if total_fee > 0:
            self.percentage_cleared = (self.fees_paid / total_fee) * 100
        else:
            self.percentage_cleared = 0.0
        super().save(*args, **kwargs)



class PaymentTrail(models.Model):
    student_finance = models.ForeignKey(
        'StudentFinance',
        on_delete=models.CASCADE,
        related_name='payment_trails'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    amount_paid = models.FloatField()
    new_balance = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student_finance.student} - {self.program} - ${self.amount_paid:.2f}"



class AdmissionPaymentTrail(models.Model):
    admission_finance = models.ForeignKey(
        'AdmissionFinance',
        on_delete=models.CASCADE,
        related_name='payment_trails'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    amount_paid = models.FloatField(null=True, blank=True, default=0.0)
    payment_method = models.CharField(max_length=250, null=True, blank=True, choices=(("Direct Payment", "Direct Payment"), ("Bank", "Bank"), ("Other", "Other")))
    new_balance = models.FloatField(null=True, blank=True, default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.admission_finance.student} - {self.program} - ${self.amount_paid:.2f}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate a unique receipt number that starts with "ADM" followed by an 8-character random hex string.
            self.receipt_number = "ADM" + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)










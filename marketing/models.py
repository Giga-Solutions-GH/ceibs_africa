from django.db import models

from account.models import CustomUser


# Create your models here.

class Prospect(models.Model):
    first_name = models.CharField(max_length=250, null=False, blank=False)
    last_name = models.CharField(max_length=250, null=False, blank=False)
    other_names = models.CharField(max_length=250, null=True, blank=True)
    phone_number = models.PositiveBigIntegerField()
    email = models.EmailField(blank=False, null=False)
    num_of_times_reached = models.PositiveBigIntegerField(default=0, null=True, blank=True)
    converted = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey('account.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    company = models.CharField(null=True, blank=True, max_length=300)
    position = models.CharField(max_length=250, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    flag = models.BooleanField(default=True)

    def __str__(self):
        return self.first_name


class ProspectFeedback(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    feedback = models.CharField(max_length=500, null=False, blank=False)
    date_added = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey('account.CustomUser', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.prospect.first_name} {self.prospect.last_name} - {self.prospect.email}"


class Admission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    other_names = models.CharField(max_length=250, blank=True, null=True)
    phone_number = models.PositiveBigIntegerField()
    email = models.EmailField()
    company = models.CharField(max_length=300, blank=True, null=True)
    position = models.CharField(max_length=250, blank=True, null=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(null=True, blank=True)
    # Optionally, if the applicant already has a user account:
    user = models.ForeignKey('account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class AdmissionDocument(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='documents')
    certificate = models.FileField(upload_to='admissions/certificates/', null=True, blank=True)
    transcript = models.FileField(upload_to='admissions/transcripts/', null=True, blank=True)
    other_document = models.FileField(upload_to='admissions/others/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # You can add a status field if you want to track review (e.g., under review, approved, rejected)
    review_status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ), default='pending')

    def __str__(self):
        return f"Documents for {self.admission}"
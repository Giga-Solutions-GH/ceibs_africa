from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from django.utils import timezone
from account.models import CustomUser


class Prospect(models.Model):
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    other_names = models.CharField(max_length=250, blank=True, null=True)
    phone_number = models.PositiveBigIntegerField()
    email = models.EmailField()
    num_of_times_reached = models.PositiveBigIntegerField(default=0, blank=True, null=True)
    # This flag indicates if the prospect has been converted into an admission.
    converted = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    company = models.CharField(max_length=300, blank=True, null=True)
    position = models.CharField(max_length=250, blank=True, null=True)
    program_of_interest = models.ForeignKey('academic_program.ProgramCover', null=True, blank=True,
                                            on_delete=models.SET_NULL)
    comments = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    flag = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ProspectFeedback(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name="feedbacks")
    feedback = models.CharField(max_length=500)
    date_added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.prospect.first_name} {self.prospect.last_name} - {self.feedback[:30]}..."


def rename_file_upload(instance, filename, folder_name):
    """
    Generates a custom path and filename for uploads, e.g.:
    admissions/passport_pictures/john_johnexample_com_passport.jpg
    """
    import os

    # Extract file extension
    extension = os.path.splitext(filename)[1]  # includes the dot, like ".jpg"

    # Replace problematic characters in the email (e.g., '@', '.')
    safe_email = instance.email.replace('@', '_').replace('.', '_')

    # Construct a new filename
    new_filename = f"{instance.first_name}_{safe_email}{extension}"

    # Return the final path: folder plus our new filename
    return f"admissions/{folder_name}/{new_filename}"


def passport_picture_upload(instance, filename):
    return rename_file_upload(instance, filename, 'passport_pictures')


def passport_front_page_upload(instance, filename):
    return rename_file_upload(instance, filename, 'passport_front_pages')


def cv_upload(instance, filename):
    return rename_file_upload(instance, filename, 'cvs')


def certificate_files_upload(instance, filename):
    return rename_file_upload(instance, filename, 'certificates')


def transcript_files_upload(instance, filename):
    return rename_file_upload(instance, filename, 'transcripts')


def other_files_upload(instance, filename):
    return rename_file_upload(instance, filename, 'others')


class Admission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('documents_under_review', 'Documents Under Review'),
        ('documents_review_cleared', 'Documents Review Cleared'),
        ('cleared_by_admissions', 'Cleared By Admissions'),
        ('awaiting_financial_clearance', 'Awaiting Financial Clearance'),
        ('student_cleared_financially', 'Student Cleared Financially'),
        ('admission_completed', 'Admission Completed'),
        ('rejected', 'Rejected'),
    )
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    other_names = models.CharField(max_length=250, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.PositiveBigIntegerField()
    email = models.EmailField()
    company = models.CharField(max_length=300, blank=True, null=True)
    position = models.CharField(max_length=250, blank=True, null=True)
    program_of_interest = models.ForeignKey('academic_program.ProgramCover', null=True, blank=True,
                                            on_delete=models.SET_NULL)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(null=True, blank=True)
    # Optionally link to an existing user account if available.
    user = models.ForeignKey('account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    # New fields for documents that are single uploads:
    passport_picture = models.ImageField(upload_to=passport_picture_upload, null=True, blank=True)
    passport_front_page = models.ImageField(upload_to=passport_front_page_upload, null=True, blank=True)
    cv = models.FileField(upload_to=cv_upload, null=True, blank=True)
    certificate_files = models.FileField(null=True, blank=True, upload_to=certificate_files_upload)
    transcript_files = models.FileField(null=True, blank=True, upload_to=transcript_files_upload)
    other_files = models.FileField(null=True, blank=True, upload_to=other_files_upload)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# class AdmissionTranscript(models.Model):
#     """
#     Model to store transcript documents for an admission.
#     Multiple transcripts can be uploaded for each admission.
#     """
#     admission = models.ForeignKey(Admission, related_name='transcripts', on_delete=models.CASCADE)
#     transcript = models.FileField(upload_to='admissions/transcripts/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     review_status = models.CharField(
#         max_length=20,
#         choices=(
#             ('pending', 'Pending'),
#             ('under_review', 'Under Review'),
#             ('approved', 'Approved'),
#             ('rejected', 'Rejected'),
#         ),
#         default='pending'
#     )
#
#     def __str__(self):
#         return f"Transcript for {self.admission.first_name} {self.admission.last_name}"
#
#
# class AdmissionCertificate(models.Model):
#     """
#     Model to store certificate documents for an admission.
#     Multiple certificates can be uploaded for each admission.
#     """
#     admission = models.ForeignKey(Admission, related_name='certificates', on_delete=models.CASCADE)
#     certificate = models.FileField(upload_to='admissions/certificates/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     review_status = models.CharField(
#         max_length=20,
#         choices=(
#             ('pending', 'Pending'),
#             ('under_review', 'Under Review'),
#             ('approved', 'Approved'),
#             ('rejected', 'Rejected'),
#         ),
#         default='pending'
#     )
#
#     def __str__(self):
#         return f"Certificate for {self.admission.first_name} {self.admission.last_name}"


@receiver(pre_save, sender=Admission)
def admission_pre_save(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_status = old_instance.status
    else:
        instance._old_status = None


@receiver(post_save, sender=Admission)
def admission_post_save(sender, instance, created, **kwargs):
    # If the admission is newly created or if the status has changed:
    if created or instance.status != instance._old_status:
        from marketing.tasks import send_admission_status_update_email
        send_admission_status_update_email.delay(instance.id)

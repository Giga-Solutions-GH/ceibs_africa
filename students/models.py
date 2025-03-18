from django.db import models

from academic_program.models import Program
from account.models import CustomUser


# Create your models here.
class StudentDetail(models.Model):
    image = models.ImageField(upload_to='student_images/', null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=200, blank=False, null=False)
    last_name = models.CharField(max_length=200, blank=False, null=False)
    other_names = models.CharField(max_length=200, blank=True, null=True)
    date_of_birth = models.DateField(null=False, blank=False)
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
    )
    gender = models.CharField(max_length=150, choices=GENDER_CHOICES, default="Male")
    unique_id = models.CharField(max_length=250, null=False, blank=False, unique=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.PositiveBigIntegerField(blank=True, null=True)
    address = models.CharField(max_length=300, null=True, blank=True)
    status = models.BooleanField(default=True)
    position = models.CharField(max_length=250, null=True, blank=True)
    next_of_kin = models.CharField(max_length=250, null=True, blank=True)
    nationality = models.CharField(max_length=250, null=True, blank=True)
    flag = models.BooleanField(default=True)
    company = models.CharField(null=True, blank=True, max_length=300)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.unique_id}"


class StudentDocumentType(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name


class StudentDocument(models.Model):
    document_type = models.ForeignKey(StudentDocumentType, on_delete=models.CASCADE, null=False, blank=False)
    student = models.ForeignKey(StudentDetail, on_delete=models.CASCADE, null=True, blank=True)
    document = models.FileField(upload_to='student_documents/', null=True, blank=True)
    document_description = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.student.first_name} {self.student.last_name}"



class StudentEnrollment(models.Model):
    student = models.ForeignKey(StudentDetail, on_delete=models.CASCADE)
    student_program_id = models.CharField(max_length=250, null=True, blank=True, unique=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    choices = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Deferred", "Deferred"),
        ("Completed", "Completed"),
        ("Alumnus", "Alumnus"),
    )
    status = models.CharField(max_length=250, null=False, blank=False, choices=choices, default="Active")

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.program.program_name}"


















































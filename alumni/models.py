from django.db import models


# Create your models here.
class Alumni(models.Model):
    student = models.ForeignKey('students.StudentDetail', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey('account.CustomUser', on_delete=models.CASCADE, null=False, blank=False)
    first_name = models.CharField(max_length=250, null=False, blank=False)
    last_name = models.CharField(max_length=250, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    program = models.ForeignKey('academic_program.Program', on_delete=models.CASCADE)
    year_of_completion = models.CharField(max_length=250, null=False, blank=False)
    current_position = models.CharField(max_length=250, null=False, blank=False)
    company = models.CharField(max_length=250, null=True, blank=True)
    industry = models.CharField(max_length=250, null=True, blank=True)
    picture = models.ImageField(upload_to='alumni_images/', null=False, blank=False)
    nationality = models.CharField(max_length=250, null=True, blank=True)
    country_of_residence = models.CharField(max_length=250, null=True, blank=True)
    flag = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.program}"

    def save_uploaded_file(self, uploaded_image):
        # 'uploaded_file' is the file object obtained from the form

        # Set the file_upload field with the uploaded file
        self.picture.save(uploaded_image.name, uploaded_image, save=True)

        # Save the model instance
        self.save()

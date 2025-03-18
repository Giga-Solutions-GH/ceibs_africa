from django.db import models
from django.utils import timezone
from django.utils.functional import lazy

from account.models import CustomUser
# from students.models import StudentEnrollment, StudentDetail
from django.apps import apps


# Create your models here.
class ProgramType(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=False, blank=False)

    def __str__(self):
        return self.name


class ProgramCover(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)

    def __str__(self):
        return self.name


class CourseCovers(models.Model):
    program_cover = models.ForeignKey('ProgramCover', null=True, blank=True, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=250, null=False, blank=False)
    course_description = models.CharField(max_length=250, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    lecturer = models.ForeignKey('Lecturer', on_delete=models.CASCADE, null=True, blank=True, related_name='course_covers')
    flag = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.program_cover.name} - {self.course_name}"


class Program(models.Model):
    program_cover = models.ForeignKey(ProgramCover, null=True, blank=True, on_delete=models.SET_NULL)
    program_name = models.CharField(max_length=250, null=False, blank=False)
    program_code = models.CharField(max_length=200, null=True, blank=True)
    program_type = models.ForeignKey(ProgramType, on_delete=models.CASCADE, null=True, blank=True)
    duration = models.CharField(max_length=250, null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    number_of_modules = models.PositiveSmallIntegerField(null=True, blank=True)
    # Program officer and Assistant Program Officer are now CustomUser instances.
    program_officer = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='program_officer'
    )
    assistant_program_officer = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assistant_program_officer'
    )
    alumni_program = models.BooleanField(default=False, null=True, blank=True)
    program_ended = models.BooleanField(default=False, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    flag = models.BooleanField(default=True)

    def __str__(self):
        return self.program_name


class ProgramSchedule(models.Model):
    program = models.ForeignKey('Program', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    location = models.CharField(max_length=250)
    start_time = models.TimeField()
    end_time = models.TimeField()
    start_date = models.DateField()
    end_date = models.DateField()
    flag = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.course_name} - {self.program.program_name} on {self.start_date}"


class ProgramScheduleDate(models.Model):
    """
    Model to store multiple dates for a ProgramSchedule.
    """
    program_schedule = models.ForeignKey(ProgramSchedule, related_name='schedule_dates', on_delete=models.CASCADE)
    session_date = models.DateField(default=timezone.now)

    def __str__(self):
        return str(self.session_date)


class Course(models.Model):
    program = models.ForeignKey('Program', on_delete=models.CASCADE)
    course_name = models.CharField(max_length=250, null=False, blank=False)
    course_description = models.CharField(max_length=250, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    lecturer = models.ForeignKey('Lecturer', on_delete=models.CASCADE, null=True, blank=True, related_name='courses')
    flag = models.BooleanField(default=True)

    def __str__(self):
        return self.course_name + "-" + self.program.program_name


class LecturerType(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)
    ceibs_professor = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Lecturer(models.Model):
    first_name = models.CharField(max_length=200, blank=False, null=False)
    last_name = models.CharField(max_length=200, blank=False, null=False)
    other_names = models.CharField(max_length=200, blank=False, null=False)
    title = models.CharField(max_length=250, blank=False, null=False)
    email = models.EmailField(blank=False, null=False)
    phone_number = models.PositiveBigIntegerField(blank=True, null=True)
    department = models.CharField(max_length=250, blank=True, null=True)
    lecturer_type = models.ForeignKey(LecturerType, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='lecturers/', null=True, blank=True)  # Optional image field
    flag = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title}, {self.first_name} {self.last_name}"


class CourseParticipant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='participants', null=True, blank=True)
    student = models.ForeignKey('students.StudentEnrollment', on_delete=models.CASCADE, null=True, blank=True)
    flag = models.BooleanField(default=True)


class TranscriptRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey('students.StudentDetail', on_delete=models.CASCADE, null=False, blank=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    year_of_completion = models.CharField(max_length=250, null=False, blank=False)
    generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.program}"


class GeneratedTranscriptRequest(models.Model):
    transcript_request = models.ForeignKey(TranscriptRequest, on_delete=models.CASCADE, null=False, blank=False)
    transcript_file = models.FileField(upload_to='generated_transcripts/', null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    show_transcript = models.BooleanField(default=False)
    flag = models.BooleanField(default=False)


class Attendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=False, blank=False)
    student = models.ForeignKey('students.StudentEnrollment', on_delete=models.CASCADE, null=False, blank=False)
    attendance_date = models.DateField(default=timezone.now, null=True, blank=True)
    comment = models.CharField(max_length=500, null=True, blank=True)
    is_present = models.BooleanField(default=False)


class ProgramParticipant(models.Model):
    first_name = models.CharField(max_length=200, blank=False, null=False)
    last_name = models.CharField(max_length=200, blank=False, null=False)
    other_names = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.PositiveBigIntegerField(blank=True, null=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    student = models.ForeignKey('students.StudentDetail', on_delete=models.CASCADE, null=True, blank=True)
    position = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=250, null=True, blank=True)
    flag = models.BooleanField(default=True)
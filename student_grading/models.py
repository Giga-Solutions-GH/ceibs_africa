from django.db import models


# Create your models here.
class GradeSystem(models.Model):
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    grade = models.CharField(max_length=100)
    remarks = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.grade


class StudentGrade(models.Model):
    student = models.ForeignKey('students.StudentDetail', on_delete=models.CASCADE)
    student_score = models.PositiveIntegerField()
    course = models.ForeignKey('academic_program.Course', on_delete=models.CASCADE)
    program = models.ForeignKey('academic_program.Program', on_delete=models.CASCADE)
    grade = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, editable=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.grade = self.calculate_grade()
        super().save(*args, **kwargs)

    def calculate_grade(self):
        grade_systems = GradeSystem.objects.all()
        for grade_system in grade_systems:
            if grade_system.min_score <= self.student_score <= grade_system.max_score:
                return grade_system
        return None


class StudentOverallGrade(models.Model):
    student_id = models.CharField(max_length=200, blank=True, null=True)
    year_program = models.ForeignKey('academic_program.Program', on_delete=models.CASCADE)
    csa = models.FloatField(null=True, blank=True)
    overall_performance = models.CharField(max_length=100, null=True, blank=True)
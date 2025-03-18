from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

from .models import GradeSystem, StudentGrade, StudentOverallGrade


def export_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
    writer = csv.writer(response, csv.excel)

    writer.writerow(field_names)
    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            row.append(smart_str(value))
        writer.writerow(row)
    return response


export_as_csv.short_description = "Export Selected to CSV"


@admin.register(GradeSystem)
class GradeSystemAdmin(admin.ModelAdmin):
    list_display = ['min_score', 'max_score', 'grade', 'remarks']
    search_fields = ['grade', 'remarks']
    actions = [export_as_csv]


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'student_score', 'course', 'program', 'grade']
    list_filter = ['program__program_name', 'grade__grade']
    search_fields = [
        'student__unique_id', 'student__first_name',
        'student__last_name', 'course__course_name'
    ]
    actions = [export_as_csv]


@admin.register(StudentOverallGrade)
class StudentOverallGradeAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'year_program', 'csa', 'overall_performance']
    list_filter = ['year_program__program_name']
    search_fields = ['student_id', 'overall_performance']
    actions = [export_as_csv]

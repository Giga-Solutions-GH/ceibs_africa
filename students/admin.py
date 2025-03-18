from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

from .models import (
    StudentDetail, StudentDocumentType, StudentDocument,
    StudentEnrollment
)


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


# -----------------------------
#  Inlines
# -----------------------------
class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 1


# -----------------------------
#  Admins
# -----------------------------
@admin.register(StudentDetail)
class StudentDetailAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'unique_id',
        'date_of_birth', 'gender', 'email', 'status'
    ]
    list_filter = ['gender', 'status', 'flag']
    search_fields = ['first_name', 'last_name', 'unique_id', 'email']
    inlines = [StudentDocumentInline]
    actions = [export_as_csv]


@admin.register(StudentDocumentType)
class StudentDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    actions = [export_as_csv]


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'student']
    list_filter = ['document_type__name']
    search_fields = ['name', 'student__unique_id', 'student__first_name', 'student__last_name']
    actions = [export_as_csv]


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'student_program_id', 'program',
        'start_date', 'end_date', 'active', 'status'
    ]
    list_filter = ['program__program_name', 'active', 'status']
    search_fields = [
        'student__unique_id', 'student__first_name',
        'student__last_name', 'student_program_id'
    ]
    actions = [export_as_csv]

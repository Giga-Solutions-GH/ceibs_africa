from django import forms
from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str
from django.core.exceptions import ObjectDoesNotExist

from account.models import CustomUser
from .models import (
    ProgramType, ProgramCover, Program, ProgramSchedule,
    Course, CourseCovers, LecturerType, Lecturer, CourseParticipant,
    TranscriptRequest, GeneratedTranscriptRequest, Attendance,
    ProgramParticipant, ProgramScheduleDate
)


# -----------------------------
#  Reusable CSV export action
# -----------------------------
def export_as_csv(modeladmin, request, queryset):
    """
    Generic CSV export admin action.
    Exports all fields of the Model.
    """
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
    writer = csv.writer(response, csv.excel)

    # Write header
    writer.writerow(field_names)

    # Write data rows
    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            row.append(smart_str(value))
        writer.writerow(row)
    return response


export_as_csv.short_description = "Export Selected to CSV"


# -----------------------------
#  Custom ModelForm for ProgramAdmin
# -----------------------------
class ProgramAdminForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ProgramAdminForm, self).__init__(*args, **kwargs)
        # Restrict the available choices for the program officer fields
        self.fields['program_officer'].queryset = CustomUser.objects.filter(roles__name='Program Officer')
        self.fields['assistant_program_officer'].queryset = CustomUser.objects.filter(roles__name='Program Officer')
        # Optionally, add Bootstrap classes if needed:
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


# -----------------------------
#  Inlines
# -----------------------------
class ProgramScheduleInline(admin.TabularInline):
    model = ProgramSchedule
    extra = 1


class CourseInline(admin.TabularInline):
    model = Course
    extra = 1


class CourseParticipantInline(admin.TabularInline):
    model = CourseParticipant
    extra = 1


class GeneratedTranscriptRequestInline(admin.TabularInline):
    model = GeneratedTranscriptRequest
    extra = 1


class ProgramScheduleDateInline(admin.TabularInline):
    model = ProgramScheduleDate
    extra = 1


class CourseCoverInline(admin.TabularInline):
    model = CourseCovers
    extra = 1


# -----------------------------
#  Admins
# -----------------------------
@admin.register(ProgramType)
class ProgramTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    actions = [export_as_csv]


@admin.register(ProgramCover)
class ProgramCoverAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    actions = [export_as_csv]
    inlines = [CourseCoverInline]


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    form = ProgramAdminForm  # Use the custom form here.
    list_display = [
        'program_name', 'program_code', 'program_type',
        'duration', 'start_date', 'end_date',
        'program_officer_display', 'assistant_program_officer_display', 'flag'
    ]
    list_filter = ['program_type', 'alumni_program', 'program_ended', 'flag']
    search_fields = ['program_name', 'program_code']
    inlines = [CourseInline, ProgramScheduleInline]  # Include additional inlines as needed
    actions = [export_as_csv]

    def save_model(self, request, obj, form, change):
        """
        Override save_model so that when a Program is saved,
        we automatically create Course records from matching CourseCovers,
        if they do not already exist for that program.
        """
        super().save_model(request, obj, form, change)
        if obj.program_cover:
            # Get all CourseCovers where the program_cover matches.
            course_covers = CourseCovers.objects.filter(program_cover=obj.program_cover.id, flag=True)
            for cc in course_covers:
                if not Course.objects.filter(program=obj, course_name=cc.course_name).exists():
                    Course.objects.create(
                        program=obj,
                        course_name=cc.course_name,
                        course_description=cc.course_description,
                        start_date=cc.start_date,
                        lecturer=cc.lecturer,
                        flag=cc.flag
                    )

    def program_officer_display(self, obj):
        """Display the program officer's full name, or '-' if not set."""
        if obj.program_officer:
            return f"{obj.program_officer.first_name} {obj.program_officer.last_name}"
        return "-"

    program_officer_display.short_description = "Program Officer"

    def assistant_program_officer_display(self, obj):
        """Display the assistant program officer's full name, or '-' if not set."""
        if obj.assistant_program_officer:
            return f"{obj.assistant_program_officer.first_name} {obj.assistant_program_officer.last_name}"
        return "-"

    assistant_program_officer_display.short_description = "Assistant Program Officer"


@admin.register(ProgramSchedule)
class ProgramScheduleAdmin(admin.ModelAdmin):
    list_display = ['program', 'course', 'location', 'start_date', 'end_date', 'flag']
    list_filter = ['program__program_name', 'course__course_name', 'flag']
    search_fields = ['program__program_name', 'course__course_name', 'location']
    inlines = [ProgramScheduleDateInline]
    actions = [export_as_csv]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'program', 'lecturer', 'start_date', 'flag']
    list_filter = ['program__program_name', 'lecturer', 'flag']
    search_fields = ['course_name', 'program__program_name']
    inlines = [CourseParticipantInline]
    actions = [export_as_csv]


@admin.register(LecturerType)
class LecturerTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'ceibs_professor']
    search_fields = ['name']
    list_filter = ['ceibs_professor']
    actions = [export_as_csv]


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ['title', 'first_name', 'last_name', 'department', 'lecturer_type', 'email', 'flag']
    list_filter = ['lecturer_type', 'flag']
    search_fields = ['first_name', 'last_name', 'email']
    actions = [export_as_csv]


@admin.register(CourseParticipant)
class CourseParticipantAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'flag']
    list_filter = ['course__course_name', 'flag']
    search_fields = ['course__course_name', 'student__student__first_name']
    actions = [export_as_csv]


@admin.register(TranscriptRequest)
class TranscriptRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'student', 'program', 'year_of_completion', 'generated']
    list_filter = ['program__program_name', 'generated']
    search_fields = ['user__username', 'student__unique_id', 'year_of_completion']
    inlines = [GeneratedTranscriptRequestInline]
    actions = [export_as_csv]


@admin.register(GeneratedTranscriptRequest)
class GeneratedTranscriptRequestAdmin(admin.ModelAdmin):
    list_display = ['transcript_request', 'transcript_file', 'created_at', 'show_transcript', 'flag']
    list_filter = ['show_transcript', 'flag']
    search_fields = ['transcript_request__student__unique_id']
    actions = [export_as_csv]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'student', 'attendance_date', 'is_present']
    list_filter = ['course__course_name', 'is_present']
    search_fields = ['user__username', 'student__student__unique_id']
    actions = [export_as_csv]


@admin.register(ProgramParticipant)
class ProgramParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'email', 'phone_number',
        'program', 'company', 'flag'
    ]
    list_filter = ['program__program_name', 'flag']
    search_fields = ['first_name', 'last_name', 'email']
    actions = [export_as_csv]


admin.site.register(ProgramScheduleDate)
admin.site.register(CourseCovers)

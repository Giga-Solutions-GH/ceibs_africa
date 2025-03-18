from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

from .models import Alumni


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


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'email', 'program',
        'year_of_completion', 'company', 'flag'
    ]
    list_filter = ['program__program_name', 'flag']
    search_fields = ['first_name', 'last_name', 'email']
    actions = [export_as_csv]

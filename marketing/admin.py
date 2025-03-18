from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

from .models import Prospect, ProspectFeedback


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


class ProspectFeedbackInline(admin.TabularInline):
    model = ProspectFeedback
    extra = 1


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'phone_number', 'email',
        'converted', 'num_of_times_reached', 'active'
    ]
    list_filter = ['converted', 'active']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    inlines = [ProspectFeedbackInline]
    actions = [export_as_csv]


@admin.register(ProspectFeedback)
class ProspectFeedbackAdmin(admin.ModelAdmin):
    list_display = ['prospect', 'feedback', 'date_added', 'user']
    list_filter = ['date_added', 'user']
    search_fields = ['prospect__first_name', 'prospect__last_name', 'feedback']
    actions = [export_as_csv]

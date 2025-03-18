from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

from .models import Event, EventDocument, EventParticipant


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


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 1


class EventDocumentInline(admin.TabularInline):
    model = EventDocument
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'date', 'venue', 'presence',
        'active', 'event_contact_name', 'date_created'
    ]
    list_filter = ['active', 'presence', 'date']
    search_fields = ['name', 'venue', 'event_contact_name']
    inlines = [EventParticipantInline, EventDocumentInline]
    actions = [export_as_csv]


@admin.register(EventDocument)
class EventDocumentAdmin(admin.ModelAdmin):
    list_display = ['event', 'document_name']
    list_filter = ['event__name']
    search_fields = ['document_name', 'event__name']
    actions = [export_as_csv]


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ['event', 'last_name', 'first_name', 'email_address', 'phone_contact']
    list_filter = ['event__name']
    search_fields = ['last_name', 'first_name', 'email_address']
    actions = [export_as_csv]

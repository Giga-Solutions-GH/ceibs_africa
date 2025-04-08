from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

from .models import ProgramFees, FinanceStatement, StudentFinance, PaymentTrail, AdmissionFinance, AdmissionPaymentTrail


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


@admin.register(ProgramFees)
class ProgramFeesAdmin(admin.ModelAdmin):
    list_display = ['program', 'fee']
    list_filter = ['program__program_name']
    search_fields = ['program__program_name']
    actions = [export_as_csv]


@admin.register(FinanceStatement)
class FinanceStatementAdmin(admin.ModelAdmin):
    list_display = ['program_fees', 'payment_options']
    list_filter = ['program_fees__program__program_name']
    search_fields = ['program_fees__program__program_name', 'payment_options']
    actions = [export_as_csv]


@admin.register(StudentFinance)
class StudentFinanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'fees_paid', 'fees', 'percentage_cleared']
    list_filter = ['fees__program_fees__program__program_name']
    search_fields = ['student__unique_id', 'student__first_name', 'student__last_name']
    actions = [export_as_csv]


@admin.register(AdmissionFinance)
class AdmissionFinanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'fees_paid', 'fees', 'percentage_cleared']
    list_filter = ['fees__program_fees__program__program_name']
    search_fields = ['student__unique_id', 'student__first_name', 'student__last_name']
    actions = [export_as_csv]


admin.site.register(PaymentTrail)
admin.site.register(AdmissionPaymentTrail)

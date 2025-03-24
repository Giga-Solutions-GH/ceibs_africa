from django.urls import path

from finance.views import student_finance_overview, student_finance_detail, admission_list

app_name = 'student_finance'

urlpatterns = [
    path('student-finance-overview/', student_finance_overview, name='student_finance_overview'),
    path('student-finance/<int:student_id>/', student_finance_detail, name='student_finance_detail'),
    path('admissions_cleared_for_finance', admission_list, name='admission_list_finance')
]

from django.urls import path

from alumni.views import all_alumni, alumni_detail, list_programs, add_alumni, upload_alumni, export_alumni, \
    alumni_statistics


app_name = 'alumni'

urlpatterns = [
    path('all_alumni/', all_alumni, name='all_alumni'),
    path('alumni/<int:alumni_id>/', alumni_detail, name='alumni_detail'),
    path('programs/alumni', list_programs, name='list_programs'),
    path('add-alumni/<int:program_id>/', add_alumni, name='add_alumni_program'),
    path('upload-alumni-excel/<int:program_id>/', upload_alumni,
         name='upload_alumni_excel_program'),
    path('export-alumni-excel/<int:program_id>/', export_alumni,
         name='export_alumni_excel_program'),
    path('alumni/statistics', alumni_statistics, name='alumni_statistics'),

]

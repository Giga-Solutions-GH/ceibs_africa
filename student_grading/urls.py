from django.urls import path

from student_grading import views

app_name = 'student_grading'

urlpatterns = [
    path('programs/<int:program_id>/students/', views.program_students, name='program_students'),
    path('students/<int:student_id>/grades/<int:program_id>', views.student_grades,
         name='student_grades'),
    path('overview', views.student_grades_overview, name='student_grades_overview'),
    path('program/<int:program_id>/export_grades/', views.export_program_grades,
         name='export_program_grades'),
    path('program/<int:program_id>/export_student_details/', views.export_student_details,
         name='export_student_details'),
    path('active_programs/', views.active_programs, name='active_programs'),
    path('program/<int:program_id>/', views.program_grades, name='program_grades'),
    path('export/<int:program_id>/', views.export_grades, name='export_grades'),
    path('ajax/fetch-grade/', views.ajax_fetch_grade, name='ajax_fetch_grade'),
    path('statistics', views.grade_statistics, name='statistics'),
    path('ajax/load-courses/', views.ajax_load_courses, name='ajax_load_courses'),
    path('ajax/load-ranking/', views.ajax_load_ranking, name='ajax_load_ranking'),
]

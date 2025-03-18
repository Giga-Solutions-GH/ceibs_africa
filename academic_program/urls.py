from django.urls import path

from academic_program import views
from academic_program.lecturers import lecturer_views

app_name = 'academic_program'

urlpatterns = [
    path('lecturer/deactivate/<int:pk>/', lecturer_views.deactivate_lecturer, name='deactivate_lecturer'),
    path('lecturer/delete/<int:pk>/', lecturer_views.delete_lecturer, name='delete_lecturer'),
    path('lecturer_list', lecturer_views.lecturers_list, name='lecturer_list'),
    path('courses/<int:course_id>/change_lecturer/', lecturer_views.change_lecturer, name='change_lecturer'),
    path('export-lecturer-statistics/', lecturer_views.export_lecturer_statistics,
         name='export_lecturer_statistics'),
    path('lecturer/edit/<int:pk>/', lecturer_views.edit_lecturer, name='edit_lecturer'),
    path('lecturer/add/', lecturer_views.lecturer_add, name='add_lecturer'),
    path('lecturers/export/', lecturer_views.export_lecturers_to_excel, name='export_lecturers'),
    path('lecturer/statistics', lecturer_views.lecturer_statistics, name='lecturer_statistics'),

    path("program_types", views.program_type_overview, name="program_types"),
    path("program_types/<str:program_type>", views.programs, name="programs"),
    path('program/statistics', views.program_statistics, name='program_statistics'),
    path('export-program-statistics/', views.export_program_statistics, name='export_program_statistics'),
    path('program-module-overview/', views.program_module_overview, name='program_module_overview'),
    path('course-details/<int:course_id>/', views.course_details, name='course_details'),
    path('program/<int:program_id>/add_student/', views.add_student_from_program,
         name='add_student_from_program_page'),
    path('program_participants/<str:program_name>/<str:program_type>', views.student_list,
         name='student_list'),
    path('program/<int:program_id>/add-participant/', views.add_program_participant,
         name='add_program_participant'),
    path('participant/<int:participant_id>/', views.program_participant_detail,
         name='program_participant_detail'),
    path('delete_participant/<int:participant_id>/', views.delete_participant, name='delete_participant'),
    path('<str:program_name>/courses/attendance', views.courses_under_program_for_attendance,
         name='attendance_course'),
    path('<str:program_name>/<str:course_name>/take_attendance', views.take_attendance,
         name='take_attendance'),
    path('update_student_enrolment_status/<int:enrollment_id>/', views.update_enrollment_status,
         name='update_enrolment_status'),

    # Program Schedule Views
    path('add-schedule/', views.select_program_to_add_schedule, name='add_schedule_overview'),
    path('add_schedule/<int:program_id>/', views.add_program_schedule, name='add_schedule'),
    path('schedule/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('update_schedule/<int:schedule_id>/', views.update_program_schedule, name='update_schedule'),

    path('attendance-overview/', views.attendance_overview, name='attendance_overview'),
    path('export-attendance/<int:course_id>/', views.export_attendance, name='export_attendance'),

    path('export_course_attendance', views.export_course_attendance_excel, name='export_course_attendance'),

    path('<str:program_name>/<str:program_type>/make_po/<int:student_id>/', views.make_program_officer,
         name='make_program_officer'),
    path('<str:program_name>/<str:program_type>/make_apo/<int:student_id>/', views.make_assistant_program_officer,
         name='make_assistant_program_officer'),
    path('<str:program_name>/<str:program_type>/export_students/', views.export_students, name='export_students'),
    path('export_program_attendance/<int:program_id>', views.export_attendance_excel, name='export_program_attendance'),

    path('dashboard/', lecturer_views.facilitator_dashboard, name='dashboard'),
    path('course/<int:course_id>/grades/', lecturer_views.course_grades, name='course_grades'),
    path('course/<int:course_id>/participants/', lecturer_views.course_participants, name='course_participants'),
    path('course/<int:course_id>/send-email/', lecturer_views.send_course_email, name='send_email'),

]

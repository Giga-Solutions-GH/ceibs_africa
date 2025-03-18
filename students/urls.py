from django.urls import path

from academic_program.views import update_enrollment_status
from students.views import add_student, delete_student_view, student_statistics, enrollment, student_detail_view, \
    all_students, add_student_from_program, student_list, student_portal, edit_student_contact, student_programs, \
    program_courses, request_transcript, program_schedule_overview, student_program_schedule, transcript_requests, \
    enrollment_detail_view, mark_enrollment_as_alumni, generate_transcript, add_to_calendar, student_fee_history, \
    program_officer_attendance, program_officer_courses, take_attendance_for_course, export_student_statistics

app_name = 'students'

urlpatterns = [
    path('add_student', add_student, name='add_student'),
    path('student/delete/<int:student_id>/', delete_student_view, name='delete_student'),
    path("student_statistics", student_statistics, name='student_statistics'),
    path('enrol_student', enrollment, name='enrol_student'),
    path('student_details/<student_id>', student_detail_view, name='student_details'),
    path('all_students', all_students, name='student_overview'),
    path('program/<int:program_id>/add_student/', add_student_from_program,
         name='add_student_from_program_page'),
    path('program_participants/<str:program_name>/<str:program_type>', student_list,
         name='student_list'),
    path('student-portal/', student_portal, name='student_portal'),
    path('edit-student-contact/', edit_student_contact, name='edit_student_contact'),
    path('student_portal/programs/', student_programs, name='student_programs'),
    path('student_portal/programs/<int:enrollment_id>/courses/', program_courses,
         name='program_courses'),
    path('student_portal/request-transcript/', request_transcript, name='request_transcript'),
    path('student_portal/transcripts/all/', transcript_requests, name='all_transcript_requests'),
    path('student_portal/program_schedule', program_schedule_overview,
         name='program_schedule_overview'),
    path('student_portal/program_chedule/<int:program_id>/',
         student_program_schedule, name='student_program_schedule'),
    path('update_student_enrolment_status/<int:enrollment_id>/', update_enrollment_status,
         name='update_enrolment_status'),
    path('enrollment/<int:enrollment_id>/details/', enrollment_detail_view,
         name='enrollment_detail'),
    path('enrollment/<int:enrollment_id>/mark-as-alumni/', mark_enrollment_as_alumni,
         name='mark_enrollment_as_alumni'),
    path('transcripts/generate/<int:transcript_id>/', generate_transcript,
         name='generate_transcript'),
    path('add-to-calendar/<int:schedule_id>/', add_to_calendar, name='add_to_calendar'),
    path('student_finances', student_fee_history, name='student_fee_history'),
    path('program-officer/', program_officer_attendance, name='program_officer_attendance'),

    # List courses for a selected program (for program officers)
    path('program-officer/courses/<int:program_id>/', program_officer_courses, name='program_officer_courses'),

    # Take attendance for a specific course in a program
    path('program-officer/course/<int:program_id>/<int:course_id>/take-attendance/',
         take_attendance_for_course,
         name='take_attendance_for_course'),
    path('export-student-statistics/', export_student_statistics, name='export_student_statistics'),
]

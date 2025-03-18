from django.urls import path

from events.views import add_event, event_overview, add_participant, generate_qr_code, upload_participants_excel_event, \
    export_participants_excel_event, event_detail, export_participants, event_thank_you, event_statistics, \
    export_event_statistics, register_participant, send_event_contact_email_view

app_name = 'event'

urlpatterns = [
    path('add_event/', add_event, name='add_event'),
    path('events_overview/', event_overview, name='events_overview'),
    path('add_participants/<int:event_id>/', add_participant, name='add_participants'),
    path('generate_qr_code/<int:event_id>/', generate_qr_code, name='generate_qr_code'),
    path('event/<int:event_id>/upload_participants/', upload_participants_excel_event,
         name='upload_participants_excel_event'),
    path('event/<int:event_id>/export_participants/', export_participants_excel_event,
         name='export_participants_excel_event'),
    path('event_detail/<int:pk>/', event_detail, name='event_detail'),
    path('events/<int:pk>/export/', export_participants, name='export_participants'),
    path('event/thank-you/<int:event_id>/', event_thank_you, name='event_thank_you'),
    path('event/statistics', event_statistics, name='event_statistics'),
    path('export/event-statistics/', export_event_statistics, name='export_event_statistics'),
    path('events/<int:event_id>/register/external', register_participant,
         name='register_participant_external'),
    path('send-contact-email/<int:event_id>/', send_event_contact_email_view, name='send_contact_email'),
]

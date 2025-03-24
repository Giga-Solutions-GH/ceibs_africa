from django.urls import path

from marketing.views import show_prospects, add_prospect, convert_prospect, add_prospect_feedback, view_feedbacks, \
    prospect_statistics, admission_add, admission_list, upload_documents, admission_request, \
    send_prospect_admission_request_email, admission_success, admission_detail

app_name = 'marketing'

urlpatterns = [
    path('prospect_feedback/<int:pk>', add_prospect_feedback, name='prospect_feedback'),
    path('prospect/convert/<int:pk>', convert_prospect, name='convert_prospect'),
    path('add_prospect', add_prospect, name='add_prospect'),
    path('prospect_list', show_prospects, name="prospect_list"),
    path('prospect/prospect_feedbacks/<int:pk>', view_feedbacks, name="view_feedbacks"),
    path('prospect_stats', prospect_statistics, name='prospect_stats'),
    path('add_admission', admission_add, name='add_admission_prospect'),
    path('admissions/all', admission_list, name='admissions_list'),
    # URL to trigger sending an admission request email to a prospect.
    path('prospect/<int:prospect_id>/send-admission-request/',
         send_prospect_admission_request_email,
         name='send_admission_request_email'),

    # URL for the prospect to fill out their admission documents.
    path('admission-request/<int:prospect_id>/<str:token>/',
         admission_request,
         name='admission_request'),

    # A simple success page after the prospect submits their admission documents.
    path('admission-success/',
         admission_success,
         name='admission_success'),

    path('admission_detail/<int:admission_id>', admission_detail, name='admission_detail')
]

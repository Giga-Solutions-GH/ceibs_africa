from django.urls import path

from marketing.views import show_prospects, add_prospect, convert_prospect, add_prospect_feedback, view_feedbacks, \
    prospect_statistics, admission_add, admission_list, upload_documents

app_name = 'marketing'

urlpatterns = [
    path('prospect_feedback/<int:pk>', add_prospect_feedback, name='prospect_feedback'),
    path('prospect/convert/<int:pk>', convert_prospect, name='convert_prospect'),
    path('add_prospect', add_prospect, name='add_prospect'),
    path('prospect_list', show_prospects, name="prospect_list"),
    path('prospect/prospect_feedbacks/<int:pk>', view_feedbacks, name="view_feedbacks"),
    path('prospect_stats', prospect_statistics, name='prospect_stats'),
    path('admission/add_prospect', admission_add, name='add_admission_prospect'),
    path('admissions/all', admission_list, name='admissions_list'),
    path('admissions/<int:admission_id>/upload_documents', upload_documents, name='admissions_document_upload')
]

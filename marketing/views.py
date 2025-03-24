from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from .tasks import send_student_welcome_email_task, send_admission_document_request_email, \
    send_admission_request_email_task, send_admission_confirmation_email_task

from academic_program.models import CourseParticipant, Course, ProgramCover
from marketing.forms import AddProspectForm, ProspectToStudentForm, AddProspectFeedbackForm, \
    AdmissionForm
from marketing.models import Prospect, ProspectFeedback, Admission
from students.models import StudentEnrollment, StudentDetail
from .utils import generate_admission_token, verify_admission_token, get_progress_for_status


def add_prospect(request):
    if request.method == 'POST':
        form = AddProspectForm(request.POST)
        print(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prospect Added')
            return redirect('marketing:add_prospect')
        else:
            print(form.errors)
            messages.error(request, "Invalid Form Submission")
            return redirect('marketing:add_prospect')
    form = AddProspectForm()
    context = {
        'form': form
    }
    return render(request, "marketing/add_prospect.html", context=context)


def show_prospects(request):
    all_prospects = Prospect.objects.all()
    context = {
        'prospects': all_prospects,
        'count': all_prospects.count(),
    }
    return render(request, "marketing/prospects.html", context=context)


def convert_prospect(request, pk):
    prospect = get_object_or_404(Prospect, id=pk)
    if request.method == 'POST':
        form = ProspectToStudentForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            other_names = form.cleaned_data['other_names']
            date_of_birth = form.cleaned_data['date_of_birth']
            gender = form.cleaned_data['gender']
            address = form.cleaned_data['address']
            student_id = form.cleaned_data['student_id']
            company = form.cleaned_data['company']
            position = form.cleaned_data['position']
            program = form.cleaned_data['program']

            # Create the new student record
            new_student = StudentDetail.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                other_names=other_names,
                date_of_birth=date_of_birth,
                gender=gender,
                address=address,
                unique_id=student_id,
                company=company,
                position=position
            )
            new_student.save()

            # Create a user for the student
            User = get_user_model()
            random_password = get_random_string(12)
            new_user = User.objects.create_user(username=student_id, email=email, password=random_password)
            new_user.save()
            new_student.user = new_user
            new_student.save()

            # Mark the prospect as converted
            prospect.converted = True
            prospect.save()

            # Enroll the student in the selected program
            prospect_enrolment = StudentEnrollment.objects.create(
                student=new_student,
                program=program,
                active=True,
                start_date=program.start_date,
                end_date=program.end_date,
                student_program_id=student_id
            )
            prospect_enrolment.save()

            # Enroll the student in all courses for the program
            courses = Course.objects.filter(program=program, flag=True)
            for course in courses:
                new_participant = CourseParticipant.objects.create(
                    course=course,
                    student=new_student,
                )
                new_participant.save()

            # Prepare links for the email
            domain = "ab71-41-215-169-36.ngrok-free.app"  # e.g., "example.com" or include protocol if needed
            dashboard_link = f"https://{domain}{reverse('student_dashboard')}"  # Update URL name as needed
            reset_link = f"https://{domain}{reverse('account:password_reset')}"  # Update URL name as needed

            # Queue the background task to send the welcome email
            send_student_welcome_email_task.delay(new_user.id, dashboard_link, reset_link)

            messages.success(request, "Prospect converted to Student and enrolled successfully.")
            return redirect('marketing:prospect_list')
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = ProspectToStudentForm(initial={
            'first_name': prospect.first_name,
            'phone_number': prospect.phone_number,
            'email': prospect.email,
            'company': prospect.company,
            'position': prospect.position,
        })
    context = {
        'form': form,
        'prospect': prospect
    }
    return render(request, "marketing/convert_prospect.html", context=context)


def add_prospect_feedback(request, pk):
    prospect = Prospect.objects.get(id=pk)
    print(prospect)
    form = AddProspectFeedbackForm(
        initial={
            'prospect': prospect
        }
    )
    if request.method == 'POST':
        form = AddProspectFeedbackForm(request.POST)
        print(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Feedback Added")
            prospect.num_of_times_reached += 1
            prospect.save()
            return redirect('marketing:prospect_list')
        else:
            messages.error(request, "Invalid Submission")
    context = {
        'form': form,
        'prospect': prospect
    }
    return render(request, 'marketing/feedback.html', context=context)



def view_feedbacks(request, pk):
    prospect = Prospect.objects.get(id=pk)
    feedbacks = ProspectFeedback.objects.filter(prospect=prospect)
    context = {
        'feedbacks': feedbacks,
        'prospect': prospect
    }
    return render(request, 'marketing/prospect_feedbacks.html', context=context)


def prospect_statistics(request):
    # Filter active prospects (you can adjust the filter criteria if needed)
    prospects = Prospect.objects.filter(flag=True)

    total_prospects = prospects.count()
    converted_count = prospects.filter(converted=True).count()
    not_converted_count = total_prospects - converted_count
    avg_reach = prospects.aggregate(avg=Avg('num_of_times_reached'))['avg'] or 0

    # Monthly prospects: group by month (using the date_added field)
    monthly_stats_qs = prospects.annotate(month=TruncMonth('date_added')).values('month').annotate(count=Count('id')).order_by('month')
    # Prepare labels and data for monthly chart
    monthly_labels = [entry['month'].strftime('%Y-%m') for entry in monthly_stats_qs]
    monthly_counts = [entry['count'] for entry in monthly_stats_qs]

    # Top companies: only consider non-empty company values; show top 5
    top_companies_qs = prospects.exclude(company__exact="").values('company').annotate(count=Count('id')).order_by('-count')[:5]
    top_companies = [entry['company'] for entry in top_companies_qs]
    top_company_counts = [entry['count'] for entry in top_companies_qs]

    # Total feedback count
    total_feedback = ProspectFeedback.objects.count()

    context = {
        'total_prospects': total_prospects,
        'converted_count': converted_count,
        'not_converted_count': not_converted_count,
        'avg_reach': round(avg_reach, 2),
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
        'top_companies': top_companies,
        'top_company_counts': top_company_counts,
        'total_feedback': total_feedback,
    }
    return render(request, 'marketing/prospect_statistics.html', context)


@login_required
def send_prospect_admission_request_email(request, prospect_id):
    prospect = get_object_or_404(Prospect, id=prospect_id)
    token = generate_admission_token(prospect.id)
    domain = "33e2-41-215-171-159.ngrok-free.app"  # Replace with your domain or use a function like get_domain()
    # Build the URL using reverse and the token
    admission_request_url = f"https://{domain}" + reverse('marketing:admission_request', args=[prospect.id, token])
    send_admission_request_email_task.delay(prospect.id, admission_request_url)
    messages.success(request, "Admission request email has been sent to the prospect.")
    return redirect('marketing:prospect_list')


@transaction.atomic
def admission_request(request, prospect_id, token):
    """
    Displays the admission request form for a prospect.
    Verifies the token (valid for 1 hour) and, if valid, allows the prospect to submit their admission details,
    including single uploads (passport picture, passport front page, CV) and multiple transcripts and certificates.
    After submission, an Admission record is created with status 'under_review' and associated transcript/certificate records are saved.
    """
    # Verify token validity (max_age in seconds, e.g. 3600 for 1 hour)
    verified_prospect_id = verify_admission_token(token, max_age=3600)
    if not verified_prospect_id or str(prospect_id) != verified_prospect_id:
        messages.error(request, "The admission request link has expired or is invalid.")
        return redirect('marketing:admission_expired')  # Ensure you have this view/template

    prospect = get_object_or_404(Prospect, id=prospect_id)

    # Prevent duplicate submissions
    if Admission.objects.filter(email=prospect.email, status__in=['under_review', 'accepted']).exists():
        messages.info(request, "Your admission documents have already been submitted.")
        return redirect('marketing:admission_success')


    if request.method == 'POST':
        admission_form = AdmissionForm(request.POST, request.FILES)

        if admission_form.is_valid():
            admission = admission_form.save(commit=False)
            admission.status = 'documents_under_review'
            admission.save()

            messages.success(request, "Your admission documents have been submitted and are under review.")
            return redirect('marketing:admission_success')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        admission_form = AdmissionForm()

    context = {
        'admission_form': admission_form,
        'prospect': prospect,
    }
    return render(request, 'marketing/admissions/admission_request.html', context)


def admission_success(request):
    """
    A simple view to display a success message after a prospect submits their admission documents.
    Once this page is rendered, the submission link should be considered expired.
    """
    # Optionally, you could add logic here to ensure the submission flag is set.
    return render(request, "marketing/admissions/admission_success.html")



@login_required(login_url='account:login')
def admission_list(request):
    # Retrieve all admissions, ordered by date_submitted (latest first)
    admissions = Admission.objects.all().order_by('-date_submitted')

    # Retrieve filter parameters from GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status')
    program_filter = request.GET.get('program')

    # Apply filters if provided
    if start_date:
        admissions = admissions.filter(date_submitted__gte=start_date)
    if end_date:
        admissions = admissions.filter(date_submitted__lte=end_date)
    if status_filter:
        admissions = admissions.filter(status=status_filter)
    if program_filter:
        admissions = admissions.filter(program_of_interest__id=program_filter)

    # Get all possible filter options
    all_statuses = Admission.STATUS_CHOICES  # List of tuples (key, value)
    # Get all ProgramCover objects for the "program of interest" filter
    program_covers = ProgramCover.objects.all()

    context = {
        'admissions': admissions,
        'start_date': start_date,
        'end_date': end_date,
        'status_filter': status_filter,
        'program_filter': program_filter,
        'all_statuses': all_statuses,
        'program_covers': program_covers,
    }
    return render(request, 'marketing/admissions/admission_list.html', context)


# Upload Documents Page (for applicants)
def upload_documents(request, admission_id):
    ...
    # admission = get_object_or_404(Admission, id=admission_id)
    # # Use a minimal layout without sidebar/header if needed (e.g., base_blank.html)
    # if request.method == 'POST':
    #     form = AdmissionDocumentForm(request.POST, request.FILES)
    #     if form.is_valid():
    #         admission_doc = form.save(commit=False)
    #         admission_doc.admission = admission
    #         admission_doc.save()
    #         messages.success(request, "Documents uploaded successfully!")
    #         return redirect('admission:upload_documents', admission_id=admission.id)
    #     else:
    #         messages.error(request, "There was an error uploading your documents. Please try again.")
    # else:
    #     form = AdmissionDocumentForm()
    # context = {
    #     'admission': admission,
    #     'form': form
    # }
    # return render(request, 'marketing/admissions/upload_documents.html', context)


@login_required(login_url='account:login')
@transaction.atomic
def admission_add(request):
    """
    View to add a new Admission along with multiple transcript and certificate uploads.
    After successful submission, the Admission status is set to 'under_review'.
    """

    if request.method == 'POST':
        admission_form = AdmissionForm(request.POST, request.FILES)

        if admission_form.is_valid():
            # Save the Admission record with status under_review.
            admission = admission_form.save(commit=False)
            admission.status = 'documents_under_review'
            admission.save()

            messages.success(request, "Admission added successfully! Documents are under review.")
            return redirect('marketing:admissions_list')
        else:
            print(admission_form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        admission_form = AdmissionForm()


    context = {
        'admission_form': admission_form,
    }
    return render(request, 'marketing/admissions/admission_add.html', context)


@transaction.atomic
@login_required(login_url='account:login')
def admission_detail(request, admission_id):
    admission = get_object_or_404(Admission, id=admission_id)

    if request.method == 'POST':
        admission_form = AdmissionForm(request.POST, request.FILES, instance=admission)

        if admission_form.is_valid():
            # Save the main admission form (e.g. updating status, personal info, etc.)
            admission_form.save()

            messages.success(request, "Admission details updated successfully.")
            return redirect('marketing:admission_detail', admission_id=admission.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        admission_form = AdmissionForm(instance=admission, initial={
            'certificate_files': admission.certificate_files,
            'transcript_files': admission.transcript_files,
            'other_files': admission.other_files
        })

    # Assume get_progress_for_status is defined elsewhere.
    progress = get_progress_for_status(admission.status)

    context = {
        'admission': admission,
        'admission_form': admission_form,
        'progress': progress,
        'now': timezone.now(),
    }
    return render(request, 'marketing/admissions/admission_detail.html', context)




















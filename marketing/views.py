from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from .tasks import send_student_welcome_email_task, send_admission_document_request_email

from academic_program.models import CourseParticipant, Course
from marketing.forms import AddProspectForm, ProspectToStudentForm, AddProspectFeedback, AdmissionDocumentForm, \
    AdmissionForm
from marketing.models import Prospect, ProspectFeedback, Admission
from students.models import StudentEnrollment, StudentDetail


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
    form = AddProspectFeedback(
        initial={
            'prospect': prospect
        }
    )
    if request.method == 'POST':
        form = AddProspectFeedback(request.POST)
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


@login_required(login_url='account:login')
def admission_list(request):
    admissions = Admission.objects.all().order_by('-date_submitted')
    if request.method == 'POST':
        # If user selects multiple admissions and clicks "Send Document Request"
        selected_ids = request.POST.getlist('selected_admissions')
        if selected_ids:
            for admission_id in selected_ids:
                send_admission_document_request_email.delay(admission_id)
            messages.success(request, "Document request emails have been sent in the background!")
            return redirect('admission_list')
        else:
            messages.warning(request, "No admissions selected.")
    context = {
        'admissions': admissions
    }
    return render(request, 'marketing/admissions/admission_list.html', context)


# Upload Documents Page (for applicants)
def upload_documents(request, admission_id):
    admission = get_object_or_404(Admission, id=admission_id)
    # Use a minimal layout without sidebar/header if needed (e.g., base_blank.html)
    if request.method == 'POST':
        form = AdmissionDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            admission_doc = form.save(commit=False)
            admission_doc.admission = admission
            admission_doc.save()
            messages.success(request, "Documents uploaded successfully!")
            return redirect('admission:upload_documents', admission_id=admission.id)
        else:
            messages.error(request, "There was an error uploading your documents. Please try again.")
    else:
        form = AdmissionDocumentForm()
    context = {
        'admission': admission,
        'form': form
    }
    return render(request, 'marketing/admissions/upload_documents.html', context)


@login_required(login_url='account:login')
def admission_add(request):
    """
    View to add a new admission.
    After saving the admission, the admin can later send a document request email
    from the admissions list page.
    """
    if request.method == 'POST':
        form = AdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            admission = form.save()
            messages.success(request, "Admission added successfully!")
            return redirect('admission:admission_list')  # Update with your actual URL name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdmissionForm()
    return render(request, 'marketing/admissions/admission_add.html', {'form': form})


















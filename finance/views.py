from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from academic_program.models import Program, ProgramCover
from finance.models import FinanceStatement, StudentFinance, ProgramFees, PaymentTrail, AdmissionFinance, \
    AdmissionPaymentTrail
from marketing.models import Admission
from marketing.utils import get_progress_for_status
from students.models import StudentDetail, StudentEnrollment
from .forms import FinanceAdmissionForm, ProgramFeesForm, FinanceStatementForm
from .tasks import send_finance_receipt_email, convert_admission_to_student


# Create your views here.
def student_finance_overview(request):
    selected_program_id = request.GET.get('program')
    selected_gender = request.GET.get('gender')
    company = request.GET.get('company')

    # Only include students with at least one active enrollment
    students = StudentDetail.objects.filter(studentenrollment__active=True).distinct()

    if selected_program_id:
        students = students.filter(studentenrollment__program_id=selected_program_id, studentenrollment__active=True).distinct()

    if selected_gender:
        students = students.filter(gender=selected_gender)

    if company:
        students = students.filter(company__icontains=company)

    # Attach all finance records to each student
    active_students = []
    for student in students:
        finance_records = student.studentfinance_set.all()
        if finance_records.exists():
            student.finance_records = finance_records
            active_students.append(student)
    students = active_students

    # Prepare data for the chart (using the first finance record per student)
    percentage_data = {'100': 0, '50': 0, 'other': 0}
    for student in students:
        finance = student.finance_records.first()
        if finance:
            percentage = finance.percentage_cleared
            if percentage >= 99.9:
                percentage_data['100'] += 1
            elif percentage >= 49.9:
                percentage_data['50'] += 1
            else:
                percentage_data['other'] += 1

    # Count active enrollments only for stats
    enrollment_counts = StudentEnrollment.objects.filter(active=True).values('status').annotate(count=Count('status'))
    status_counts = {status['status']: status['count'] for status in enrollment_counts}

    count = len(students)
    active_count = count  # all students shown have active enrollment
    male_count = sum(1 for s in students if s.gender == 'Male')
    female_count = sum(1 for s in students if s.gender == 'Female')

    context = {
        'students': students,
        'percentage_data': percentage_data,
        'programs': Program.objects.all(),
        'genders': [('Male', 'Male'), ('Female', 'Female')],
        'count': count,
        'active_count': active_count,
        'male_count': male_count,
        'female_count': female_count,
        'today': timezone.now().date(),  # used in template to show program status
    }
    return render(request, 'finance/layouts/student_finance_overview.html', context)


def student_finance_detail(request, student_id):
    # 1) Get the student
    student = get_object_or_404(StudentDetail, id=student_id)

    # 2) Ensure there's a StudentFinance record for each enrollment
    enrollments = StudentEnrollment.objects.filter(student=student)
    for enrollment in enrollments:
        program = enrollment.program
        try:
            program_fees = ProgramFees.objects.get(program=program)
        except ProgramFees.DoesNotExist:
            messages.info(request, "Program Fees Yet to be Added.")
            return redirect('student_finance:student_finance_overview')

        finance_statement, _ = FinanceStatement.objects.get_or_create(program_fees=program_fees)
        StudentFinance.objects.get_or_create(
            student=student,
            fees=finance_statement,
            defaults={'fees_paid': 0.0, 'percentage_cleared': 0.0}
        )

    # 3) Retrieve all StudentFinance records for this student
    student_finances = StudentFinance.objects.filter(student=student)

    if request.method == 'POST':
        updated = False
        # 4) For each finance record, see if there's an 'amount_to_add_ID'
        for finance in student_finances:
            form_key = f"amount_to_add_{finance.id}"
            if form_key in request.POST:
                raw_value = request.POST.get(form_key, "0").strip()
                try:
                    add_amount = float(raw_value)
                except ValueError:
                    add_amount = 0.0

                if add_amount > 0:
                    # 5) Check if adding this amount would exceed total fees
                    program_fees = finance.fees.program_fees.fee or 0.0
                    if finance.fees_paid + add_amount > program_fees:
                        messages.error(
                            request,
                            f"Cannot exceed total fee for {finance.fees.program_fees.program.program_name}. "
                            f"(Current fees paid: ${finance.fees_paid:.2f}, Fee: ${program_fees:.2f}, Attempted to add: ${add_amount:.2f})"
                        )
                        continue

                    # 6) Update fees_paid and percentage
                    finance.fees_paid += add_amount
                    finance.percentage_cleared = (finance.fees_paid / program_fees) * 100 if program_fees > 0 else 0
                    finance.save()

                    # 7) Create PaymentTrail
                    PaymentTrail.objects.create(
                        student_finance=finance,
                        program=finance.fees.program_fees.program,  # store the program
                        amount_paid=add_amount,
                        receipt_number=f"RCPT-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                        remarks="Payment added via finance detail update.",
                        new_balance=finance.fees_paid
                    )
                    updated = True

        if updated:
            messages.success(request, "Payment(s) recorded successfully!")
        else:
            messages.info(request, "No valid payment was added.")
        return redirect('student_finance:student_finance_detail', student_id=student_id)

    # 8) Gather PaymentTrails for grouping by program
    all_trails = PaymentTrail.objects.filter(student_finance__student=student).select_related('program')
    # Build a dictionary: { program: [trail, trail, ...], ... }
    from collections import defaultdict
    grouped_trails = defaultdict(list)
    for trail in all_trails:
        grouped_trails[trail.program].append(trail)

    context = {
        'student': student,
        'student_finances': student_finances,
        'grouped_trails': dict(grouped_trails),  # Convert to normal dict if you like
        'today': timezone.now().date(),
    }
    return render(request, 'finance/layouts/student_finance_detail.html', context)


@login_required(login_url='account:login')
def admission_list(request):
    # Retrieve all admissions, ordered by date_submitted (latest first)
    admissions = Admission.objects.filter(
        status__in=[
            'awaiting_financial_clearance',
            'student_cleared_financially',
            'admission_completed',
            'rejected'
        ]
    ).order_by('-date_submitted')

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
    return render(request, 'finance/layouts/admissions.html', context)


@transaction.atomic
@login_required(login_url='account:login')
def admission_finance_detail(request, admission_id):
    """
    Displays and updates the finance details for an Admission.
    It calculates the total fee (via FinanceStatement linked to ProgramFees),
    updates the fees paid, computes the balance and percentage cleared,
    and allows finance to update the admission status (only statuses from
    "awaiting_financial_clearance" downward). If the new status is
    "student_cleared_financially", a background task is triggered to convert the
    admission into a student.
    """
    # Retrieve the Admission record.
    admission = get_object_or_404(Admission, id=admission_id)

    # Get the active program under the admission's program of interest.
    try:
        active_program = Program.objects.get(
            program_cover=admission.program_of_interest,
            flag=True,
            program_ended=False,
        )
    except Program.DoesNotExist:
        messages.error(request, "No active program found for this admission.")
        return redirect('student_finance:admission_list_finance')

    try:
        program_fees = ProgramFees.objects.get(program=active_program)
        finance_statement = FinanceStatement.objects.get(program_fees=program_fees)
    except (ProgramFees.DoesNotExist, FinanceStatement.DoesNotExist):
        messages.error(request, "Finance information is not configured for the selected program.")
        return redirect('student_finance:admission_list_finance')

    # Get or create the AdmissionFinance record.
    admission_finance, created = AdmissionFinance.objects.get_or_create(student=admission, fees=finance_statement)
    total_fee = admission_finance.fees.program_fees.fee or 0.0

    if request.method == 'POST':
        form = FinanceAdmissionForm(request.POST)
        if form.is_valid():
            fees_paid = form.cleaned_data['fees_paid']
            new_status = form.cleaned_data.get('status_update', '')
            payment_method = form.cleaned_data.get('payment_method', '')

            # Compute percentage cleared and balance.
            if total_fee > 0:
                percentage = (fees_paid / total_fee) * 100
            else:
                percentage = 0.0
            balance = total_fee - fees_paid

            # Update the AdmissionFinance record.
            admission_finance.fees_paid = fees_paid
            admission_finance.percentage_cleared = percentage
            admission_finance.student_balance = balance
            admission_finance.save()

            # Optionally update the admission status if provided.
            if new_status:
                admission.status = new_status
                admission.last_update = timezone.now()
                admission.save()
                # If the new status indicates that the student is cleared financially,
                # trigger a background task to convert the admission into a student.
                if new_status == "student_cleared_financially":
                    convert_admission_to_student.delay(admission.id)

            # Create a new payment trail record.
            AdmissionPaymentTrail.objects.create(
                admission_finance=admission_finance,
                program=active_program,
                amount_paid=fees_paid,
                new_balance=balance,
                payment_method=payment_method,
                remarks="Payment updated via finance portal."
            )

            # Trigger background task to send a finance receipt email.
            send_finance_receipt_email.delay(admission_finance.id)

            messages.success(request, "Financial details updated successfully. A receipt email has been sent.")
            return redirect('student_finance:admission_finance_detail', admission_id=admission.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        initial_data = {
            'fees_paid': admission_finance.fees_paid or 0.0,
            'status_update': admission.status if admission.status in [
                'awaiting_financial_clearance',
                'student_cleared_financially',
                'admission_completed',
                'rejected'
            ] else '',
        }
        form = FinanceAdmissionForm(initial=initial_data)
        fees_paid = admission_finance.fees_paid or 0.0
        percentage = admission_finance.percentage_cleared or 0.0
        balance = admission_finance.student_balance or (total_fee - fees_paid)

    progress = get_progress_for_status(admission.status)

    context = {
        'admission': admission,
        'admission_finance': admission_finance,
        'total_fee': total_fee,
        'fees_paid': fees_paid,
        'percentage': percentage,
        'balance': balance,
        'progress': progress,
        'now': timezone.now(),
        'finance_form': form,
    }
    return render(request, 'finance/layouts/admission_finance_detail.html', context)


@transaction.atomic
@login_required(login_url='account:login')
def manage_program_fees(request):
    # Get active programs (active = flag True and program_ended = False)
    active_programs = Program.objects.filter(flag=True, program_ended=False).order_by('program_name')

    selected_program = None
    program_fees_form = None
    finance_statement_form = None

    # If a program is selected (via GET parameter)
    program_id = request.GET.get('program_id')
    if program_id:
        try:
            selected_program = active_programs.get(id=program_id)
        except Program.DoesNotExist:
            messages.error(request, "Selected program not found.")
        if selected_program:
            # Get or create the ProgramFees for the selected program.
            program_fees, _ = ProgramFees.objects.get_or_create(program=selected_program)
            # Get or create the FinanceStatement using the ProgramFees.
            finance_statement, _ = FinanceStatement.objects.get_or_create(program_fees=program_fees)

            if request.method == 'POST':
                # Use two separate forms – both forms should be in the POST data.
                program_fees_form = ProgramFeesForm(request.POST, instance=program_fees)
                finance_statement_form = FinanceStatementForm(request.POST, instance=finance_statement)
                if program_fees_form.is_valid() and finance_statement_form.is_valid():
                    program_fees_form.save()
                    finance_statement_form.save()
                    messages.success(request, "Program fees and payment options updated successfully.")
                    return redirect(f"{reverse('finance:manage_program_fees')}?program_id={selected_program.id}")
                else:
                    messages.error(request, "Please correct the errors below.")
            else:
                program_fees_form = ProgramFeesForm(instance=program_fees)
                finance_statement_form = FinanceStatementForm(instance=finance_statement)

    context = {
        'active_programs': active_programs,
        'selected_program': selected_program,
        'program_fees_form': program_fees_form,
        'finance_statement_form': finance_statement_form,
    }
    return render(request, 'finance/layouts/manage_program_fees.html', context)



































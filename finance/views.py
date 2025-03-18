from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from academic_program.models import Program
from finance.models import FinanceStatement, StudentFinance, ProgramFees, PaymentTrail
from students.models import StudentDetail, StudentEnrollment


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


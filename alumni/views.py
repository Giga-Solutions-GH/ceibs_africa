import pandas as pd
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from academic_program.models import Program, CourseParticipant, Course
from account.models import CustomUser
from alumni.forms import AlumniForm, AddAlumniForm
from alumni.models import Alumni
from students.models import StudentEnrollment


def student_to_alumni(request, enrollment_id):
    enrollment = StudentEnrollment.objects.get(id=enrollment_id)
    enrollment.active = False
    enrollment.save()

    student = enrollment.student
    if not StudentEnrollment.objects.filter(student=student).exists():
        user = student.user
        user.role = "Alumni"
        student.status = False

        user.save()
        student.save()

    if Alumni.objects.filter(student=student, program=enrollment.program).exists():
        messages.warning(request, "Alumni Already Exists")
        return redirect('student_details', student_id=student.student_id)

    new_alumni = Alumni.objects.create(
        first_name=enrollment.student.first_name,
        last_name=enrollment.student.last_name,
        email=enrollment.student.email,
        year_of_completion=enrollment.completion_year,
        student=enrollment.student,
        user=enrollment.student.user,
        program=enrollment.program,
    )
    new_alumni.save()
    messages.success(request, "Student Enrollment Converted to Alumni")
    return redirect('student_details', student_id=student.student_id)


def list_programs(request):
    programs = Program.objects.filter(alumni_program=True)
    return render(request, 'alumni/list_programs.html', {'programs': programs})


def add_alumni(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    form = AddAlumniForm(initial={'program': program})

    if request.method == "POST":
        form = AddAlumniForm(request.POST, request.FILES)
        if form.is_valid():
            alumni = form.save()
            default_password = get_random_string(length=8)
            user = CustomUser.objects.create_user(
                username=alumni.email,
                email=alumni.email,
                password=default_password,
                first_name=alumni.first_name,
                last_name=alumni.last_name
            )
            user.save()

            alumni.user = user
            alumni.save()

            # Send email (commented for now)
            # send_mail(
            #     'Welcome to Alumni Network',
            #     f'Hello {alumni.first_name},\n\nYour account has been created. Please use the following credentials to log in and change your password:\n\nUsername: {alumni.email}\nPassword: {default_password}\n\nPlease change your password after logging in.\n\nThank you!',
            #     'admin@yourdomain.com',
            #     [alumni.email],
            #     fail_silently=False,
            # )

            messages.success(request, 'Alumni added successfully.')
            return redirect('add_alumni_program', program_id=program_id)

    context = {'form': form, 'program': program}
    return render(request, 'alumni/add_alumni.html', context)


def upload_alumni(request, program_id):
    program = get_object_or_404(Program, id=program_id)

    if request.method == "POST":
        excel_file = request.FILES['alumni_excel']
        df = pd.read_excel(excel_file)

        for _, row in df.iterrows():
            # Create CustomUser
            default_password = get_random_string(length=8)
            user = CustomUser.objects.create_user(
                username=row['email'],
                email=row['email'],
                password=default_password,
                first_name=row['first_name'],
                last_name=row['last_name']
            )
            user.save()

            # Create Alumni
            Alumni.objects.create(
                user=user,
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                program=program,
                year_of_completion=row['year_of_completion'],
                current_position=row['current_position'],
                company=row['company'],
                industry=row['industry'],
                picture=row['picture'],
                nationality=row['nationality'],
                country_of_residence=row['country_of_residence'],
            )

            # Send email (commented for now)
            # send_mail(
            #     'Welcome to Alumni Network',
            #     f'Hello {row["first_name"]},\n\nYour account has been created. Please use the following credentials to log in and change your password:\n\nUsername: {row["email"]}\nPassword: {default_password}\n\nPlease change your password after logging in.\n\nThank you!',
            #     'admin@yourdomain.com',
            #     [row['email']],
            #     fail_silently=False,
            # )

        messages.success(request, 'Alumni uploaded successfully.')
        return redirect('add_alumni_program', program_id=program_id)

    return render(request, 'alumni/add_alumni.html', {'program': program})


def export_alumni(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    alumni = Alumni.objects.filter(program=program)
    data = []

    for alumnus in alumni:
        data.append([
            alumnus.student.id,
            alumnus.first_name,
            alumnus.last_name,
            alumnus.email,
            alumnus.program.id,
            alumnus.year_of_completion,
            alumnus.current_position,
            alumnus.company,
            alumnus.industry,
            alumnus.picture.url,
            alumnus.nationality,
            alumnus.country_of_residence,
            alumnus.relative_id
        ])

    df = pd.DataFrame(data, columns=[
        'Student ID', 'First Name', 'Last Name', 'Email', 'Program ID',
        'Year of Completion', 'Current Position', 'Company', 'Industry',
        'Picture', 'Nationality', 'Country of Residence', 'Relative ID'
    ])

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="alumni_{program.program_name}.xlsx"'
    df.to_excel(response, index=False)

    return response


def alumni_overview(request):
    programs = Program.objects.all()
    program_counts = []
    for program in programs:
        count = Alumni.objects.filter(program=program).count()
        program_counts.append({'program': program, 'count': count})
    context = {
        'programs': program_counts
    }
    return render(request, 'alumni/alumni_list_overview.html', context=context)


def alumni_list(request, program_name):
    program = Program.objects.get(program_name=program_name)
    alumni = Alumni.objects.filter(program=program)
    context = {'alumni': alumni, 'program_name': program_name, 'count': alumni.count()}
    return render(request, 'alumni/alumni_list.html', context=context)


def all_alumni(request):
    """
    Display a list of all alumni, allowing filters by nationality, industry,
    country of residence, and program.
    """

    # --- Get filter parameters from GET ---
    nationality_filter = request.GET.get('nationality', '').strip()
    industry_filter = request.GET.get('industry', '').strip()
    residence_filter = request.GET.get('country_of_residence', '').strip()
    program_filter = request.GET.get('program', '').strip()

    # --- Base queryset ---
    alumni = Alumni.objects.filter(flag=True)

    # --- Apply filters if provided ---
    if nationality_filter:
        # Use icontains for partial matching, or iexact for exact
        alumni = alumni.filter(nationality__icontains=nationality_filter)

    if industry_filter:
        alumni = alumni.filter(industry__icontains=industry_filter)

    if residence_filter:
        alumni = alumni.filter(country_of_residence__icontains=residence_filter)

    if program_filter:
        alumni = alumni.filter(program__id=program_filter)

    # --- Gather distinct filter values for dropdowns ---
    # nationalities, industries, and residences from active alumni
    # (exclude empty/None to avoid blank dropdown entries)
    all_nationalities = (
        Alumni.objects.filter(flag=True)
        .exclude(nationality__isnull=True)
        .exclude(nationality__exact='')
        .values_list('nationality', flat=True)
        .distinct()
    )
    all_industries = (
        Alumni.objects.filter(flag=True)
        .exclude(industry__isnull=True)
        .exclude(industry__exact='')
        .values_list('industry', flat=True)
        .distinct()
    )
    all_residences = (
        Alumni.objects.filter(flag=True)
        .exclude(country_of_residence__isnull=True)
        .exclude(country_of_residence__exact='')
        .values_list('country_of_residence', flat=True)
        .distinct()
    )
    # Programs from academic_program
    all_programs = Program.objects.filter(flag=True)

    context = {
        'alumni': alumni,
        'program_name': 'All Programs',  # If you need a heading (you may override)
        'all_nationalities': all_nationalities,
        'all_industries': all_industries,
        'all_residences': all_residences,
        'all_programs': all_programs,

        # For retaining the user's currently selected filters
        'selected_nationality': nationality_filter,
        'selected_industry': industry_filter,
        'selected_residence': residence_filter,
        'selected_program': program_filter,
    }
    return render(request, 'alumni/alumni_all.html', context=context)


def alumni_statistics(request):
    # Only consider active alumni (flag=True)
    alumni_qs = Alumni.objects.filter(flag=True)

    total_alumni = alumni_qs.count()

    # Alumni by Program
    alumni_by_program = alumni_qs.values('program__program_name').annotate(count=Count('id')).order_by('program__program_name')
    alumni_by_program_labels = [entry['program__program_name'] for entry in alumni_by_program]
    alumni_by_program_data = [entry['count'] for entry in alumni_by_program]

    # Alumni by Year of Completion
    alumni_by_year = alumni_qs.values('year_of_completion').annotate(count=Count('id')).order_by('year_of_completion')
    alumni_by_year_labels = [entry['year_of_completion'] for entry in alumni_by_year]
    alumni_by_year_data = [entry['count'] for entry in alumni_by_year]

    # Alumni by Industry (replace empty with "Unknown")
    alumni_by_industry = alumni_qs.values('industry').annotate(count=Count('id')).order_by('industry')
    alumni_by_industry_labels = [entry['industry'] if entry['industry'] else "Unknown" for entry in alumni_by_industry]
    alumni_by_industry_data = [entry['count'] for entry in alumni_by_industry]

    # Alumni by Country of Residence (replace empty with "Unknown")
    alumni_by_country = alumni_qs.values('country_of_residence').annotate(count=Count('id')).order_by('country_of_residence')
    alumni_by_country_labels = [entry['country_of_residence'] if entry['country_of_residence'] else "Unknown" for entry in alumni_by_country]
    alumni_by_country_data = [entry['count'] for entry in alumni_by_country]

    # Additional insight: Top Industry
    if alumni_by_industry_data:
        max_index = alumni_by_industry_data.index(max(alumni_by_industry_data))
        top_industry = alumni_by_industry_labels[max_index]
    else:
        top_industry = "N/A"

    context = {
        'total_alumni': total_alumni,
        'alumni_by_program_labels': alumni_by_program_labels,
        'alumni_by_program_data': alumni_by_program_data,
        'alumni_by_year_labels': alumni_by_year_labels,
        'alumni_by_year_data': alumni_by_year_data,
        'alumni_by_industry_labels': alumni_by_industry_labels,
        'alumni_by_industry_data': alumni_by_industry_data,
        'alumni_by_country_labels': alumni_by_country_labels,
        'alumni_by_country_data': alumni_by_country_data,
        'top_industry': top_industry,
    }
    return render(request, 'alumni/alumni_statistics.html', context)


def alumni_detail(request, alumni_id):
    alumni = get_object_or_404(Alumni, id=alumni_id)

    if request.method == "POST":
        form = AlumniForm(request.POST, request.FILES, instance=alumni)
        if form.is_valid():
            form.save()
            messages.success(request, "Alumni details updated successfully!")
            return redirect('alumni_detail', alumni_id=alumni.id)  # Redirect back here
    else:
        form = AlumniForm(instance=alumni)

    # If this Alumni record is linked to a student, gather the enrollments
    enrollments = []
    if alumni.student:
        # Fetch all enrollments for this StudentDetail
        enrollments = StudentEnrollment.objects.filter(student=alumni.student).select_related('program')

        # For each enrollment, gather the courses for which the student is a participant
        for e in enrollments:
            course_ids = CourseParticipant.objects.filter(student=e).values_list('course_id', flat=True)
            # Attach a 'courses' attribute to the enrollment for easy access in the template
            e.courses = Course.objects.filter(pk__in=course_ids)

    context = {
        'alumni': alumni,
        'form': form,
        'enrollments': enrollments,
    }
    return render(request, 'alumni/alumni_detail.html', context)

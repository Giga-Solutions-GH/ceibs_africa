import random
import string

import openpyxl
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from academic_program import forms
from academic_program.models import Lecturer, Course, LecturerType, CourseParticipant
from account.models import CustomUser, Department, Role
from student_grading.models import StudentGrade
from ..tasks import send_facilitator_email, send_course_assignment_email, send_password_reset_email


def generate_random_password(length=12):
    """Generates a random password."""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def lecturers_list(request):
    all_lecturers = Lecturer.objects.all()
    count = all_lecturers.count()

    # Annotate each LecturerType with the number of related Lecturer objects
    lecturer_type_counts = LecturerType.objects.annotate(num_lecturers=Count('lecturer')).values('name',
                                                                                                 'num_lecturers')

    context = {
        'lecturers': all_lecturers,
        'count': count,
        'lecturer_type_counts': lecturer_type_counts,
    }
    return render(request, "academic_program/layouts/lecturer_list.html", context)


@login_required
def edit_lecturer(request, pk):
    """
    Edit an existing lecturer.
    (Assumes that the lecturer already has a CustomUser account.)
    Allows updating details and reassigning courses.
    """
    lecturer = get_object_or_404(Lecturer, pk=pk)
    if request.method == 'POST':
        lecturer_form = forms.LecturerForm(request.POST, request.FILES, instance=lecturer)
        course_form = forms.CourseAssignmentForm(request.POST)
        if lecturer_form.is_valid() and course_form.is_valid():
            lecturer_form.save()
            selected_courses = course_form.cleaned_data['courses']
            lecturer.courses.set(selected_courses)
            lecturer.save()
            messages.success(request, 'Lecturer updated successfully.')
            return redirect('academic_program:edit_lecturer', pk=lecturer.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        lecturer_form = forms.LecturerForm(instance=lecturer)
        course_form = forms.CourseAssignmentForm(initial={'courses': lecturer.courses.all()})
    context = {
        'lecturer_form': lecturer_form,
        'course_form': course_form,
        'lecturer': lecturer
    }
    return render(request, 'academic_program/layouts/edit_lecturer.html', context)


def export_lecturers_to_excel(request):
    # Fetch all lecturers
    lecturers = Lecturer.objects.all().values('first_name', 'last_name', 'other_names', 'title', 'email',
                                              'phone_number', 'lecturer_type__name')

    # Convert to DataFrame
    df = pd.DataFrame(list(lecturers))

    # Create an HttpResponse object with Excel content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=lecturers.xlsx'

    # Write DataFrame to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lecturers')

    return response


def lecturer_statistics(request):
    # Total lecturers count
    total_lecturers = Lecturer.objects.count()

    # Group lecturers by status using the 'flag' field:
    status_qs = Lecturer.objects.values('flag').annotate(count=Count('id'))
    statuses = []
    status_counts = []
    for item in status_qs:
        label = "Active" if item['flag'] else "Inactive"
        statuses.append(label)
        status_counts.append(item['count'])

    # Group lecturers by type (using lecturer_type__name)
    type_qs = Lecturer.objects.values('lecturer_type__name').annotate(count=Count('id'))
    types = [item['lecturer_type__name'] if item['lecturer_type__name'] else "Undefined" for item in type_qs]
    type_counts = [item['count'] for item in type_qs]

    # Group lecturers by title
    title_qs = Lecturer.objects.values('title').annotate(count=Count('id'))
    titles = [item['title'] for item in title_qs]
    print(titles)
    title_counts = [item['count'] for item in title_qs]

    context = {
        'total_lecturers': total_lecturers,
        'statuses': statuses,
        'status_counts': status_counts,
        'types': types,
        'type_counts': type_counts,
        'titles': titles,
        'title_counts': title_counts,
    }
    return render(request, 'academic_program/layouts/lecturer_statistics.html', context)


def export_lecturer_statistics(request):
    # Create an Excel workbook and worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Lecturer Statistics'

    # Add headers to the worksheet
    headers = [
        'Total Lecturers',
        'Lecturers by Status',
        'Lecturers by Title',
        'Lecturers by Department',
        'Lecturers per Course'
    ]
    worksheet.append(headers)

    # Calculate statistics
    total_lecturers = Lecturer.objects.count()
    lecturers_by_status = Lecturer.objects.values('status').annotate(count=Count('id'))
    lecturers_by_title = Lecturer.objects.values('title').annotate(count=Count('id'))
    lecturers_by_department = Lecturer.objects.values('department').annotate(count=Count('id'))
    lecturers_per_course = Course.objects.values('lecturer__title').annotate(count=Count('id'))

    # Write total number of lecturers
    worksheet.append([total_lecturers])

    # Write statistics by status
    for item in lecturers_by_status:
        worksheet.append([f"Status: {item['status']}", item['count']])

    # Write statistics by title
    for item in lecturers_by_title:
        worksheet.append([f"Title: {item['title']}", item['count']])

    # Write statistics by department
    for item in lecturers_by_department:
        worksheet.append([f"Department: {item['department']}", item['count']])

    # Write statistics for lecturers per course
    for item in lecturers_per_course:
        worksheet.append([f"Course: {item['lecturer__title']}", item['count']])

    # Create HTTP response with Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="lecturer_statistics.xlsx"'
    workbook.save(response)

    return response


@login_required
def lecturer_add(request):
    """
    View to add a new lecturer.
    When a lecturer is added, a CustomUser account is created (if not exists),
    the Facilitator role under the 'Programs' department is assigned, and
    a password reset email is sent in the background.
    """
    if request.method == "POST":
        form = forms.LecturerForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the Lecturer instance
            lecturer = form.save(commit=False)
            lecturer.save()

            # Create or get the custom user account
            user, created = CustomUser.objects.get_or_create(
                email=lecturer.email,
                defaults={
                    'first_name': lecturer.first_name,
                    'last_name': lecturer.last_name,
                    'username': lecturer.email,  # use email as username if desired
                    'is_staff': True,  # Set as staff if needed
                    'password1': generate_random_password(),
                    'password2': generate_random_password(),
                }
            )
            # Associate the lecturer with the user if not already
            if not lecturer.user:
                lecturer.user = user
                lecturer.save()

            # Ensure the user has the Facilitator role in the Programs department.
            # Get or create the Programs department.
            dept, _ = Department.objects.get_or_create(
                name="Programs",
                defaults={"description": "Programs Department"}
            )
            # Get or create the Facilitator role for this department.
            facilitator_role, _ = Role.objects.get_or_create(
                name="Facilitator",
                department=dept
            )
            if not user.roles.filter(id=facilitator_role.id).exists():
                user.roles.add(facilitator_role)
                user.save()

            # Send a password reset email in the background
            send_password_reset_email.delay(user.pk)

            messages.success(request, "Lecturer added successfully and a password reset email has been sent.")
            return redirect('academic_program:add_lecturer')
        else:
            messages.error(request, "Form is not valid. Please correct the errors.")
    else:
        form = forms.LecturerForm()
    return render(request, 'academic_program/layouts/lecturer_add.html', {'form': form})


def deactivate_lecturer(request, pk):
    lecturer = get_object_or_404(Lecturer, pk=pk)
    lecturer.flag = False
    lecturer.save()
    messages.success(request, 'Lecturer marked as inactive.')
    return redirect('academic_program:lecturers_list')


def delete_lecturer(request, pk):
    lecturer = get_object_or_404(Lecturer, pk=pk)
    lecturer.flag = False
    lecturer.save()
    messages.success(request, 'Lecturer deleted (flagged as inactive).')
    return redirect('academic_program:lecturers_list')



@login_required
def change_lecturer(request, course_id):
    """
    Change the lecturer for a specific course.
    After updating, an email is sent to the new lecturer with program and course details.
    """
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        lecturer_id = request.POST.get('lecturer')
        lecturer = get_object_or_404(Lecturer, id=lecturer_id)
        course.lecturer = lecturer
        course.save()
        messages.success(request, 'Lecturer updated for the course successfully.')
        # Send an email notification to the new lecturer
        send_course_assignment_email.delay(course.id, lecturer.id)
    return redirect('academic_program:course_details', course_id=course_id)


@login_required
def facilitator_dashboard(request):
    # Ensure the logged-in user has the Facilitator role.
    if not request.user.has_role("Facilitator"):
        messages.error(request, "You are not authorized to access this page.")
        return redirect("account:login")

    try:
        # Assume the facilitator's Lecturer record is identified by the same email.
        lecturer = Lecturer.objects.get(email=request.user.email)
    except Lecturer.DoesNotExist:
        messages.error(request, "No facilitator record found for your account.")
        return redirect("account:login")

    # Get all courses where the facilitator is the lecturer.
    courses = Course.objects.filter(lecturer=lecturer, flag=True).order_by('course_name')

    context = {
        'courses': courses,
    }
    return render(request, 'academic_program/facilitator/dashboard.html', context)


@login_required
def course_grades(request, course_id):
    """View to input grades for a specific course."""
    course = get_object_or_404(Course, id=course_id, flag=True)
    try:
        lecturer = Lecturer.objects.get(email=request.user.email)
    except Lecturer.DoesNotExist:
        messages.error(request, "No facilitator record found.")
        return redirect("facilitator:dashboard")

    if course.lecturer != lecturer:
        messages.error(request, "You are not authorized to enter grades for this course.")
        return redirect("facilitator:dashboard")

    # Retrieve CourseParticipants for the course.
    participants = CourseParticipant.objects.filter(course=course, flag=True)
    # (In a real scenario, you might use a formset to update grades for each student.)
    # Here, we simply list the participants and provide an input field for a new grade.
    if request.method == 'POST':
        # Process each grade input; for brevity, assume inputs are named "grade_<participant_id>"
        for participant in participants:
            grade_input = request.POST.get(f'grade_{participant.id}')
            if grade_input is not None:
                try:
                    new_score = int(grade_input)
                    # Update or create a StudentGrade record (assume one per course-participant)
                    sg, created = StudentGrade.objects.get_or_create(
                        student=participant.student.student,
                        course=course,
                        program=course.program,
                        defaults={'student_score': new_score}
                    )
                    if not created:
                        sg.student_score = new_score
                        sg.save()
                except ValueError:
                    messages.error(request, f"Invalid grade input for participant {participant.id}.")
        messages.success(request, "Grades updated successfully.")
        return redirect('facilitator:course_grades', course_id=course.id)

    context = {
        'course': course,
        'participants': participants,
    }
    return render(request, 'academic_program/facilitator/course_grades.html', context)


@login_required
def course_participants(request, course_id):
    """View to display the participants for a given course."""
    course = get_object_or_404(Course, id=course_id, flag=True)
    try:
        lecturer = Lecturer.objects.get(email=request.user.email)
    except Lecturer.DoesNotExist:
        messages.error(request, "No facilitator record found.")
        return redirect("facilitator:dashboard")
    if course.lecturer != lecturer:
        messages.error(request, "You are not authorized to view participants for this course.")
        return redirect("facilitator:dashboard")

    participants = CourseParticipant.objects.filter(course=course, flag=True)
    context = {
        'course': course,
        'participants': participants,
    }
    return render(request, 'academic_program/facilitator/course_participants.html', context)


@login_required
def send_course_email(request, course_id):
    """
    View to allow the facilitator to send an email to all course participants.
    The email form is displayed and upon submission, the email is sent using a background task.
    """
    course = get_object_or_404(Course, id=course_id, flag=True)
    try:
        lecturer = Lecturer.objects.get(email=request.user.email)
    except Lecturer.DoesNotExist:
        messages.error(request, "No facilitator record found.")
        return redirect("facilitator:dashboard")
    if course.lecturer != lecturer:
        messages.error(request, "You are not authorized to send emails for this course.")
        return redirect("facilitator:dashboard")

    if request.method == 'POST':
        subject = request.POST.get("subject", f"Update for {course.course_name}")
        message = request.POST.get("message", "")
        # In a production environment, you’d likely use Celery to send emails asynchronously.
        # For example:
        send_facilitator_email.delay(course.id, subject, message)
        messages.success(request, "Emails have been sent to all course participants.")
        return redirect("facilitator:dashboard")

    context = {
        'course': course,
    }
    return render(request, 'academic_program/facilitator/send_email.html', context)

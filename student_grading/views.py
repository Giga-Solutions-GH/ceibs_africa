from django.db.models import Avg, Count
from django.db.models.functions import ExtractYear
from django.shortcuts import render
import pandas as pd
from django.contrib import messages
from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from academic_program.models import Program, Course, CourseParticipant
from student_grading.forms import GradeEntryForm
from student_grading.models import StudentGrade, GradeSystem
from students.models import StudentEnrollment, StudentDetail


def active_programs(request):
    """
    Shows all 'flag=True' programs grouped by their ProgramCover.
    We also pass 'today' so the template can check if a program is ended or ongoing.
    """
    # Fetch all flagged programs (with optional related fields if needed)
    all_programs = Program.objects.filter(flag=True).select_related('program_cover', 'program_type')

    # Group programs by cover
    cover_dict = {}
    for prog in all_programs:
        cover = prog.program_cover  # could be None if not set
        if cover not in cover_dict:
            cover_dict[cover] = []
        cover_dict[cover].append(prog)

    context = {
        'cover_dict': cover_dict,  # {ProgramCover or None: [Program, ...]}
        'today': timezone.now().date()  # for ended checks
    }
    return render(request, 'student_grading/layouts/active_programs.html', context)


def program_grades(request, program_id):
    # Retrieve the program object or return 404
    program = get_object_or_404(Program, id=program_id, flag=True)
    courses = Course.objects.filter(program=program)

    # Create a ModelFormSet for StudentGrade
    GradeEntryFormSet = modelformset_factory(
        StudentGrade,
        form=GradeEntryForm,
        extra=0,
        can_delete=False
    )

    # We'll store a list of tuples (course, formset) to pass to the template.
    formset_data = []

    if request.method == 'POST':
        all_valid = True
        # Process each course's formset by its unique prefix.
        for course in courses:
            prefix = f'course_{course.id}'
            formset = GradeEntryFormSet(
                request.POST,
                queryset=StudentGrade.objects.filter(course=course, program=program),
                prefix=prefix
            )
            if formset.is_valid():
                formset.save()
            else:
                all_valid = False
                messages.error(request, f"Errors in {course.course_name}: {formset.errors}")
        if all_valid:
            messages.success(request, "All grades updated successfully!")
        else:
            messages.warning(request, "Some errors occurred. Please review the details above.")
        return redirect('student_grading:program_grades', program_id=program.id)
    else:
        # For GET, build a formset for each course.
        for course in courses:
            prefix = f'course_{course.id}'
            # Get participants for the course.
            participants = CourseParticipant.objects.filter(course=course)
            initial_data = []
            for participant in participants:
                try:
                    # Ensure there's a StudentGrade record for each participant.
                    grade_obj, created = StudentGrade.objects.get_or_create(
                        student=participant.student.student,
                        course=course,
                        program=program,
                        defaults={'student_score': 0}
                    )
                    initial_data.append({
                        'student': grade_obj.student,
                        'student_score': grade_obj.student_score,
                        'course': grade_obj.course,
                        'id': grade_obj.id,
                    })
                except Exception as e:
                    # Log error if needed and skip this participant.
                    continue
            queryset = StudentGrade.objects.filter(course=course, program=program)
            formset = GradeEntryFormSet(
                queryset=queryset,
                initial=initial_data,
                prefix=prefix
            )
            formset_data.append((course, formset))

    context = {
        'program': program,
        'formset_data': formset_data,  # List of (course, formset) tuples
    }
    return render(request, 'student_grading/layouts/program_grades.html', context)


def export_grades(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    grades = StudentGrade.objects.filter(program=program).select_related('student', 'course')

    data = []
    for grade in grades:
        data.append({
            'Student ID': grade.student.unique_id,
            'Student Name': f"{grade.student.first_name} {grade.student.last_name}",
            'Course': grade.course.course_name,
            'Score': grade.student_score,
            'Grade': grade.grade.grade if grade.grade else 'N/A'
        })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={program.program_name}_grades.xlsx'
    df.to_excel(response, index=False, sheet_name='Grades')
    return response


def program_students(request, program_id):
    program = get_object_or_404(Program, id=program_id)

    # Get the students enrolled in this program
    enrollments = StudentEnrollment.objects.filter(program=program)
    student_ids = enrollments.values_list('student_id', flat=True)
    students = StudentDetail.objects.filter(id__in=student_ids)

    context = {
        'program': program,
        'students': students
    }
    return render(request, 'student_grading/layouts/program_students.html', context)


def student_grades(request, student_id, program_id):
    """
    Displays and edits grades for all courses in which the student is a participant
    under the specified program.
    Ensures a StudentGrade object exists for each such course, so the formset covers them all.
    """
    student = get_object_or_404(StudentDetail, id=student_id)
    program = get_object_or_404(Program, id=program_id)
    enrolment = StudentEnrollment.objects.filter(student=student, program=program).first()

    # 1) Get all courses in which the student is a participant for this program
    #    i.e., using CourseParticipant
    course_ids = CourseParticipant.objects.filter(
        student=enrolment,
        course__program=program
    ).values_list('course_id', flat=True)

    # 2) If you want to include all courses under the program even if not a participant, do:
    # courses = program.course_set.all()
    # But typically, we only want to see courses the student is actually in:
    # So we limit to course_ids from above.

    # 3) Create (or fetch) a StudentGrade record for each relevant course, so it appears in the formset
    for cid in course_ids:
        course = get_object_or_404(program.course_set, id=cid)
        # get_or_create ensures there's a StudentGrade object for each course
        StudentGrade.objects.get_or_create(
            student=student,
            course=course,
            program=program,
            defaults={'student_score': 0}  # or any default
        )

    # 4) Build the formset from all StudentGrade records for these courses
    GradeEntryFormSet = modelformset_factory(
        StudentGrade,
        form=GradeEntryForm,
        extra=0,
    )
    queryset = StudentGrade.objects.filter(
        student=student,
        program=program,
        course__in=course_ids
    )

    if request.method == 'POST':
        formset = GradeEntryFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Grades updated successfully!')
            return redirect(
                'student_grading:student_grades',
                student_id=student.id,
                program_id=program.id
            )
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = GradeEntryFormSet(queryset=queryset)

    context = {
        'student': student,
        'program': program,
        'formset': formset
    }
    return render(request, 'student_grading/layouts/student_grades.html', context)



def student_grades_overview(request):
    """
    Displays all alumni programs (flag=True, alumni_program=True).
    Groups them by program_cover and shows relevant info.
    """
    # Fetch all relevant programs, prefetch the cover & type for efficiency
    all_programs = Program.objects.filter(
        alumni_program=True,
        flag=True
    ).select_related('program_cover', 'program_type').order_by('program_cover__name', 'program_name')

    # Group programs by their ProgramCover
    cover_dict = {}
    for prog in all_programs:
        cover = prog.program_cover  # can be None if not set
        if cover not in cover_dict:
            cover_dict[cover] = []
        cover_dict[cover].append(prog)

    # We'll pass today to the template so we can check if the program ended
    today = timezone.now().date()

    # Build a list of covers actually used (excluding None)
    used_covers = []
    for cover in cover_dict.keys():
        if cover:
            used_covers.append(cover)
    used_covers.sort(key=lambda c: c.name)  # Sort by name

    context = {
        'cover_dict': cover_dict,  # { ProgramCover or None : [Program, ...] }
        'today': today,
        'used_covers': used_covers,  # For the cover dropdown
    }
    return render(request, 'student_grading/layouts/student_grades_overview.html', context)


def export_program_grades(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    courses = Course.objects.filter(program=program)

    # Create a Pandas Excel writer using openpyxl as the engine
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{program.program_name}_Grades.xlsx"'
    writer = pd.ExcelWriter(response, engine='openpyxl')

    # Prepare an empty DataFrame to hold all courses data
    all_courses_df = pd.DataFrame()

    for course in courses:
        # Fetch grades for the current course
        grades = StudentGrade.objects.filter(course=course, program=program).select_related('student', 'grade')

        # Prepare data for the current course
        data = {
            'Student ID': [grade.student.unique_id for grade in grades],
            'Student Name': [f"{grade.student.first_name} {grade.student.last_name}" for grade in grades],
            'Score': [grade.student_score for grade in grades],
            'Grade': [grade.grade.grade if grade.grade else '' for grade in grades],
        }
        df = pd.DataFrame(data)

        # Add a course header
        course_header_df = pd.DataFrame({'Student ID': [f'Course: {course.course_name}'], 'Student Name': [''], 'Score': [''], 'Grade': ['']})

        # Add empty rows for separation
        empty_rows_df = pd.DataFrame(columns=df.columns, index=range(2))  # Create two empty rows

        # Append the course header, the data, and empty rows to the main DataFrame
        all_courses_df = pd.concat([all_courses_df, course_header_df, df, empty_rows_df], ignore_index=True)

    # Write the entire DataFrame to a single sheet
    all_courses_df.to_excel(writer, sheet_name='Program Grades', index=False)

    # Save and close the writer
    writer.save()

    return response


def export_student_details(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    grades = StudentGrade.objects.filter(program=program).select_related('course', 'student')

    # Create a DataFrame for detailed student grades
    data = {
        'Student ID': [],
        'Student Name': [],
        'Course Name': [],
        'Score': [],
        'Grade': [],
    }

    for grade in grades:
        data['Student ID'].append(grade.student.unique_id)
        data['Student Name'].append(f"{grade.student.first_name} {grade.student.last_name}")
        data['Course Name'].append(grade.course.course_name)
        data['Score'].append(grade.student_score)
        data['Grade'].append(grade.grade.grade if grade.grade else '')

    df = pd.DataFrame(data)

    # Pivot the DataFrame to create a student-centric view
    pivot_df = df.pivot_table(
        index=['Student ID', 'Student Name'],
        columns='Course Name',
        values=['Score', 'Grade'],
        aggfunc='first'
    ).reset_index()

    # Flatten the columns
    pivot_df.columns = [' '.join(col).strip() for col in pivot_df.columns.values]

    # Export to Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{program.program_name}_student_details.xlsx"'
    pivot_df.to_excel(response, index=False, engine='openpyxl')

    return response


def ajax_fetch_grade(request):
    """
    Expects a 'score' GET parameter, returns JSON with 'grade' and 'remarks'.
    """
    score_str = request.GET.get('score', '')
    try:
        score = int(score_str)
    except ValueError:
        return JsonResponse({'error': 'Invalid score'}, status=400)

    if score < 0 or score > 100:
        return JsonResponse({'error': 'Score must be between 0 and 100'}, status=400)

    # Find matching GradeSystem
    grade_obj = GradeSystem.objects.filter(min_score__lte=score, max_score__gte=score).first()
    if grade_obj:
        return JsonResponse({
            'grade': grade_obj.grade,
            'remarks': grade_obj.remarks
        })
    else:
        return JsonResponse({'grade': '', 'remarks': ''})


def grade_statistics(request):
    """
    Renders the main analytics page:
      - bar chart (avg score by program)
      - line chart (multi programs)
      - pie chart (grade distribution)
    The ranking table is loaded by AJAX.
    """

    all_programs = Program.objects.filter(flag=True).order_by('program_name')

    # 1) Bar chart: average score by program
    program_stats_qs = (StudentGrade.objects
                        .values('program__program_name')
                        .annotate(avg_score=Avg('student_score'))
                        .order_by('program__program_name'))
    program_bar_labels = [item['program__program_name'] for item in program_stats_qs]
    program_bar_data = [round(item['avg_score'] or 0, 2) for item in program_stats_qs]
    top_program_data = None
    if program_stats_qs:
        top_program_data = max(program_stats_qs, key=lambda x: x['avg_score'] or 0)

    # 2) Multi-line chart
    line_program_ids = request.GET.getlist('line_program_ids')
    if line_program_ids:
        line_programs = Program.objects.filter(pk__in=line_program_ids, flag=True)
    else:
        line_programs = all_programs

    line_datasets = []
    all_years_set = set()
    for prog in line_programs:
        qs = (StudentGrade.objects.filter(program=prog)
              .annotate(year=ExtractYear('program__start_date'))
              .values('year')
              .annotate(avg_score=Avg('student_score'))
              .order_by('year'))
        years = []
        data = []
        for entry in qs:
            if entry['year']:
                yr_str = str(entry['year'])
                years.append(yr_str)
                data.append(round(entry['avg_score'] or 0, 2))
                all_years_set.add(yr_str)
        line_datasets.append({
            'program_name': prog.program_name,
            'slug': slugify(prog.program_name),
            'labels': years,
            'data': data,
        })
    unified_years = sorted(all_years_set, key=lambda y: int(y))
    for ds in line_datasets:
        transformed = []
        for y in unified_years:
            if y in ds['labels']:
                idx = ds['labels'].index(y)
                transformed.append(ds['data'][idx])
            else:
                transformed.append(0)
        ds['labels'] = unified_years
        ds['data'] = transformed

    # 3) Grade distribution (pie)
    dist_program_id = request.GET.get('dist_program_id', '')
    if dist_program_id:
        try:
            dist_program = Program.objects.get(pk=dist_program_id, flag=True)
        except Program.DoesNotExist:
            dist_program = None
    else:
        dist_program = None
    if dist_program:
        dist_qs = StudentGrade.objects.filter(program=dist_program)
    else:
        dist_qs = StudentGrade.objects.all()
    grade_dist = dist_qs.values('grade__grade').annotate(count=Count('id')).order_by('grade__grade')
    grade_labels = [g['grade__grade'] if g['grade__grade'] else 'Unassigned' for g in grade_dist]
    grade_counts = [g['count'] for g in grade_dist]

    context = {
        'all_programs': all_programs,

        'program_bar_labels': program_bar_labels,
        'program_bar_data': program_bar_data,
        'top_program_data': top_program_data,

        'line_program_ids': line_program_ids,
        'line_datasets': line_datasets,
        'line_years': unified_years,

        'dist_program_id': dist_program_id,
        'grade_labels': grade_labels,
        'grade_counts': grade_counts,
    }
    return render(request, 'student_grading/layouts/grade_statistics.html', context)


def ajax_load_courses(request):
    program_id = request.GET.get('program_id')
    if not program_id:
        return JsonResponse({'courses': []})

    try:
        program_id = int(program_id)
    except ValueError:
        return JsonResponse({'courses': []})

    courses_qs = Course.objects.filter(program__id=program_id, flag=True).order_by('course_name')
    courses_list = [{'id': c.id, 'name': c.course_name} for c in courses_qs]
    return JsonResponse({'courses': courses_list})


def ajax_load_ranking(request):
    program_id = request.GET.get('program_id')
    course_id = request.GET.get('course_id')

    if not program_id or not course_id:
        # Return empty snippet
        html = '<tr><td colspan="3">No data</td></tr>'
        return JsonResponse({'html': html})

    try:
        program_id = int(program_id)
        course_id = int(course_id)
    except ValueError:
        html = '<tr><td colspan="3">Invalid IDs</td></tr>'
        return JsonResponse({'html': html})


    try:
        program = Program.objects.get(pk=program_id, flag=True)
        course = Course.objects.get(pk=course_id, program=program, flag=True)
    except (Program.DoesNotExist, Course.DoesNotExist):
        html = '<tr><td colspan="3">Program or Course not found</td></tr>'
        return JsonResponse({'html': html})

    rank_qs = (StudentGrade.objects
               .filter(program=program, course=course)
               .select_related('student')
               .order_by('-student_score'))

    # Build a context for partial template
    ranking_list = []
    current_rank = 1
    for row in rank_qs:
        s_name = f"{row.student.first_name} {row.student.last_name}"
        ranking_list.append({
            'rank': current_rank,
            'student_name': s_name,
            'score': row.student_score,
        })
        current_rank += 1

    # We'll render a snippet from e.g. 'students/snippets/_ranking_rows.html'
    html_rows = render_to_string('student_grading/snippets/ranking_rows.html', {'ranking_list': ranking_list})
    return JsonResponse({'html': html_rows})








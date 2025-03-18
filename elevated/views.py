import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from academic_program.models import Program
from events.models import Event
from students.models import StudentEnrollment, StudentDetail


@login_required(login_url='account:login')
def home(request):
    students = StudentDetail.objects.all()
    events = Event.objects.all()
    all_programs = Program.objects.filter(alumni_program=True)

    # Prepare events data for FullCalendar
    events_data = []
    for event in events:
        events_data.append({
            'title': event.name,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'url': f'events/event_detail/{event.id}/'
        })

    labels = []
    data = []
    for program in all_programs:
        labels.append(program.program_name)
        count_for_program = StudentEnrollment.objects.filter(program=program).count()
        data.append(count_for_program)

    context = {
        'students': students,
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'events_json': json.dumps(events_data),
    }
    return render(request, "index.html", context=context)

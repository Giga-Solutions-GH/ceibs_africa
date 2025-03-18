import tempfile

from django.db.models.functions import ExtractQuarter, TruncMonth
from django.shortcuts import render

# Create your views here.
import io

import openpyxl
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.utils.timezone import make_naive

from events.forms import AddEventForm, AddEventParticipantForm, UploadParticipantsForm, EventParticipantForm
from events.models import Event, EventParticipant
from .tasks import process_participant_excel_task, send_event_participant_added_email, send_event_contact_email


@login_required(login_url='account:login')
def add_event(request):
    if request.method == "POST":
        form = AddEventForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract key details from the form.
            event_name = form.cleaned_data.get('name')
            event_date = form.cleaned_data.get('date')
            venue = form.cleaned_data.get('venue')
            new_start = form.cleaned_data.get('start_time')
            new_end = form.cleaned_data.get('end_time')

            # Check for duplicate event based on name, date, and venue.
            if Event.objects.filter(name=event_name, date=event_date, venue=venue).exists():
                messages.error(request, "An event with these details already exists. Please modify the event details.")
                return render(request, 'events/add_event.html', {'form': form})

            # Check if any active event at the same venue overlaps with the new event's times.
            overlapping_events = Event.objects.filter(
                venue=venue,
                active=True,
                start_time__lt=new_end,
                end_time__gt=new_start
            )
            if overlapping_events.exists():
                messages.error(
                    request,
                    "An event with overlapping times at the same venue already exists. Please choose a different time or venue."
                )
                return render(request, 'events/add_event.html', {'form': form})

            # Save the event.
            event = form.save(user=request.user)

            # Check which button was pressed.
            if "save_and_send_email" in request.POST:
                # Queue the Celery task to send the contact email asynchronously.
                send_event_contact_email.delay(event.id)
                messages.success(request, "Event added successfully and contact email is being sent.")
            else:
                messages.success(request, "Event added successfully.")

            return redirect('event:events_overview')
        else:
            messages.error(request, "There were errors in the form. Please correct them.")
    else:
        form = AddEventForm()

    return render(request, 'events/add_event.html', {'form': form})



def event_overview(request):
    events = Event.objects.all()
    context = {'events': events}
    return render(request, 'events/event_overview.html', context)


@login_required
def add_participant(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = AddEventParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.event = event
            participant.save()
            messages.success(request, 'Participant added successfully.')
            return redirect('event:add_participants')
    else:
        form = AddEventParticipantForm()

    context = {'form': form, 'event': event}
    return render(request, 'events/add_participant.html', context)


def generate_qr_code(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    qr_data = request.build_absolute_uri(reverse('event:register_participant_external', args=[event_id]))
    qr = qrcode.make(qr_data)
    response = HttpResponse(content_type="image/png")
    qr.save(response, "PNG")
    return response


def upload_participants_excel_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = UploadParticipantsForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['participants_excel']
            try:
                df = pd.read_excel(excel_file)

                # Assuming the Excel file has columns: 'last_name', 'first_name', 'other_names', 'phone_contact', 'email', 'company_organization', 'position'
                for index, row in df.iterrows():
                    EventParticipant.objects.create(
                        event=event,
                        last_name=row['last_name'],
                        first_name=row['first_name'],
                        other_names=row['other_names'],
                        phone_contact=row['phone_contact'],
                        email=row['email'],
                        company_organization=row['company_organization'],
                        position=row['position']
                    )
                messages.success(request, 'Participants uploaded successfully.')
            except Exception as e:
                messages.error(request, f'Error uploading participants: {str(e)}')
            return redirect(add_participant)
    else:
        form = UploadParticipantsForm()

    context = {
        'form': form,
        'event': event
    }
    return redirect('add_participants')


def export_participants_excel_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = EventParticipant.objects.filter(event=event)

    # Create a DataFrame from the participants queryset
    data = []
    for participant in participants:
        data.append({
            'Last Name': participant.last_name,
            'First Name': participant.first_name,
            'Other Names': participant.other_names,
            'Phone Contact': participant.phone_contact,
            'Email': participant.email,
            'Company/Organization': participant.company_organization,
            'Position': participant.position,
        })

    df = pd.DataFrame(data)

    # Convert DataFrame to Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=participants_{event.name}.xlsx'
    df.to_excel(response, index=False)

    return response


@login_required(login_url='account:login')
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    ParticipantFormSet = modelformset_factory(EventParticipant, form=AddEventParticipantForm, extra=1, can_delete=True)

    # Check for participant file upload first
    if request.method == 'POST' and 'participant_file' in request.FILES:
        file = request.FILES.get('participant_file')
        print(file)
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            process_participant_excel_task.delay(tmp_path, event.id)
            messages.success(request, "Participant file uploaded successfully. The records are being processed in the background.")
            return redirect('event:event_detail', pk=pk)
        else:
            messages.info(request, "No file found, Upload a valid excel file")
            return redirect('event:event_detail', pk=pk)

    # Existing event and participant form handling
    if request.method == 'POST':
        if 'save_event' in request.POST:
            # Handle event details form submission
            event_form = AddEventForm(request.POST, instance=event, files=request.FILES)
            if event_form.is_valid():
                event_form.save()
                return redirect('event:event_detail', pk=pk)
        elif 'save_participants' in request.POST:
            # Handle participants formset submission
            event_form = AddEventForm(instance=event)  # Use the current instance for context
            formset = ParticipantFormSet(request.POST, request.FILES, queryset=EventParticipant.objects.filter(event=event))
            if formset.is_valid():
                for form in formset:
                    if form.cleaned_data:
                        # For new participants, check required fields...
                        if not form.instance.pk:
                            first_name = form.cleaned_data.get('first_name')
                            last_name = form.cleaned_data.get('last_name')
                            company = form.cleaned_data.get('company')
                            if not (first_name and last_name and company):
                                # Skip saving this form if required fields are missing.
                                continue
                        participant = form.save(commit=False)
                        if not participant.pk:
                            participant.event = event
                        participant.save()
                        # Queue the email notification for the new participant
                        send_event_participant_added_email.delay(participant.id, event.id)
                messages.success(request, "Participants updated successfully!")
                return redirect('event:event_detail', pk=pk)
            else:
                print(formset.errors)
    else:
        event_form = AddEventForm(instance=event)
        formset = ParticipantFormSet(queryset=EventParticipant.objects.filter(event=event))

    event_form = AddEventForm(instance=event)
    formset = ParticipantFormSet(queryset=EventParticipant.objects.filter(event=event))

    context = {
        'event_form': event_form,
        'formset': formset,
        'event': event,
    }
    return render(request, 'events/event_detail.html', context)



def export_participants(request, pk):
    # Get the event
    event = get_object_or_404(Event, pk=pk)

    # Query participants
    participants = EventParticipant.objects.filter(event=event).values(
        'last_name', 'first_name', 'other_names', 'phone_contact', 'email_address', 'company', 'position'
    )

    # Convert to DataFrame
    df = pd.DataFrame(participants)

    # Convert event date to naive datetime if timezone-aware
    event_date = make_naive(event.start_time) if event.start_time.tzinfo else event.start_time

    # Add event name and date to DataFrame
    df['Event Name'] = event.name
    df['Event Date'] = event_date

    # Save to Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{event.name}_{event.start_time}_participants.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Participants', index=False)

    return response


def event_statistics(request):
    # --- Original Metrics ---
    # Consider the most recent 10 events (or adjust as needed)
    recent_events = Event.objects.order_by('-date')[:10]
    total_participants = EventParticipant.objects.filter(event__in=recent_events).count()

    # Participants by event (from the recent events)
    events_qs = Event.objects.order_by('-date')[:10]
    event_participant_counts = (EventParticipant.objects.filter(event__in=events_qs)
                                .values('event__name')
                                .annotate(count=Count('id'))
                                .order_by('event__name'))
    event_names = [item['event__name'] for item in event_participant_counts]
    participant_counts = [item['count'] for item in event_participant_counts]

    # Frequent participants (across all events)
    frequent_participants_qs = (EventParticipant.objects
                                .values('email_address', 'first_name', 'last_name', 'other_names')
                                .annotate(count=Count('id'))
                                .order_by('-count'))
    frequent_participant_data = [
        (
            f"{item['first_name']} {item['last_name']}" + (f" {item['other_names']}" if item['other_names'] else ""),
            item['email_address'],
            item['count']
        )
        for item in frequent_participants_qs
    ]

    # --- New Insights ---

    # 1. Events per Month (using the event.date field)
    events_by_month_qs = (Event.objects
                          .annotate(month=TruncMonth('date'))
                          .values('month')
                          .annotate(count=Count('id'))
                          .order_by('month'))
    events_by_month_labels = [entry['month'].strftime("%Y-%m") for entry in events_by_month_qs if entry['month']]
    events_by_month_data = [entry['count'] for entry in events_by_month_qs]

    # 2. Events by Company (assume Event has a 'company' field)
    events_by_company_qs = (Event.objects
                            .exclude(company__isnull=True)
                            .exclude(company__exact="")
                            .values('company')
                            .annotate(count=Count('id'))
                            .order_by('-count'))
    events_by_company_labels = [entry['company'] for entry in events_by_company_qs]
    events_by_company_data = [entry['count'] for entry in events_by_company_qs]

    # 3. Events by Quarter
    events_by_quarter_qs = (Event.objects
                            .annotate(quarter=ExtractQuarter('date'))
                            .values('quarter')
                            .annotate(count=Count('id'))
                            .order_by('quarter'))
    events_by_quarter_labels = [f"Q{entry['quarter']}" for entry in events_by_quarter_qs if entry['quarter']]
    events_by_quarter_data = [entry['count'] for entry in events_by_quarter_qs]

    context = {
        'total_participants': total_participants,
        'event_names': event_names,
        'participant_counts': participant_counts,
        'frequent_participants': frequent_participant_data,
        'events_by_month_labels': events_by_month_labels,
        'events_by_month_data': events_by_month_data,
        'events_by_company_labels': events_by_company_labels,
        'events_by_company_data': events_by_company_data,
        'events_by_quarter_labels': events_by_quarter_labels,
        'events_by_quarter_data': events_by_quarter_data,
    }
    return render(request, 'events/event_statistics.html', context)



def export_event_statistics(request):
    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Event Statistics'

    # Add headers
    headers = ['Event Name', 'Total Participants']
    sheet.append(headers)

    # Get the last 10 events
    recent_events = Event.objects.order_by('-date')[:10]

    # Add data to sheet
    for event in recent_events:
        participant_count = EventParticipant.objects.filter(event=event).count()
        sheet.append([event.name, participant_count])

    # Set up the HTTP response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=event_statistics.xlsx'

    # Save workbook to response
    workbook.save(response)
    return response


def register_participant(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.event = event
            participant.save()
            return redirect('event:event_thank_you', event_id=event.id)  # Redirect to a thank you page or event list

    else:
        form = EventParticipantForm()

    context = {
        'event': event,
        'form': form
    }
    return render(request, 'events/register_participant_external.html', context)


def event_thank_you(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    context = {
        'event': event
    }
    return render(request, 'events/thank_you.html', context)


@login_required(login_url='account:login')
def send_event_contact_email_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    send_event_contact_email.delay(event_id)
    messages.success(request, "Contact email has been sent to the event contact.")
    return redirect('event:event_detail', pk=event_id)













import os
from io import BytesIO

import pandas as pd
from celery import shared_task
from django.conf.urls.static import static
from django.core.files.storage import default_storage
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage

from .models import Event, EventParticipant


@shared_task
def process_participant_excel_task(temp_file_path, event_id):
    """
    Reads an uploaded Excel file from temp_file_path and creates EventParticipant
    records for the given event.
    Expected columns: 'last name', 'first name', 'other names', 'phone contact',
    'email address', 'company', 'position'
    After creating a participant, it queues a task to send a notification email.
    """
    try:
        event = Event.objects.get(id=event_id)
    except ObjectDoesNotExist:
        # Clean up file if event no longer exists
        os.remove(temp_file_path)
        return

    try:
        df = pd.read_excel(temp_file_path)
    except Exception as e:
        # Log error if needed, then clean up file.
        os.remove(temp_file_path)
        return

    # Iterate over each row and create a participant if required fields exist.
    for index, row in df.iterrows():
        # Retrieve and clean the expected columns.
        last_name = str(row.get('Title', '')).strip()
        first_name = str(row.get('First Name', '')).strip()
        first_name = str(row.get('Other Names', '')).strip()
        email_address = str(row.get('Email Address', '')).strip()
        phone_contact = str(row.get('Phone Contact', '')).strip()

        # Only create a participant if required fields are present.
        if last_name and first_name and email_address and phone_contact:
            try:
                participant = EventParticipant.objects.create(
                    event=event,
                    last_name=last_name,
                    first_name=first_name,
                    other_names=str(row.get('Other Names', '')).strip(),
                    phone_contact=phone_contact,
                    email_address=email_address,
                    company=str(row.get('Company', '')).strip(),
                    position=str(row.get('Position', '')).strip()
                )
            except Exception as e:
                print(e)
                continue
            # Queue an email task to notify this participant.
            send_event_participant_added_email.delay(participant.id, event.id)

    # Remove the temporary file after processing.
    os.remove(temp_file_path)


@shared_task
def send_event_participant_added_email(participant_id, event_id):
    """
    Sends an email notification about the addition of a participant to an event.
    The email includes event details such as venue, date, start and end times, and the event image.
    """
    try:
        participant = EventParticipant.objects.get(id=participant_id)
        event = Event.objects.get(id=event_id)
    except (EventParticipant.DoesNotExist, Event.DoesNotExist):
        # Optionally log error here
        return

    # Build context for the email template.
    context = {
        'participant': participant,
        'event': event,
        'venue': event.venue,
        'start_date': event.start_time.strftime("%Y-%m-%d") if event.start_time else "TBA",
        'end_date': event.end_time.strftime("%Y-%m-%d") if event.end_time else "TBA",
        'start_time': event.start_time.strftime("%H:%M") if event.start_time else "TBA",
        'end_time': event.end_time.strftime("%H:%M") if event.end_time else "TBA",
        'now': timezone.now(),
    }

    # Render the email template.
    email_body = render_to_string('events/emails/participant_added.html', context)
    email = EmailMessage(
        subject=f"You are added as a participant for {event.name}",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[participant.email_address]
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


def generate_event_participant_excel(event):
    # For demonstration, we create a simple Excel file in memory.
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Participant Template"
    # Create headers
    ws.append(["Title", "Last Name", "First Name", "Other Names", "Phone Contact", "Email Address", "Company", "Position"])
    # Save workbook to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


@shared_task
def send_event_contact_email(event_id):
    from .models import Event
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return
    domain = "ab71-41-215-169-36.ngrok-free.app"
    # Build the student portal link (if needed)
    # portal_link = f"https://{domain}" + reverse('event:events_overview')

    # Prepare context for the email template
    context = {
        'event': event,
        # 'portal_link': portal_link,
        'current_time': timezone.now(),
        'ceibs_logo_url': "https://ab71-41-215-169-36.ngrok-free.app/static/assets/images/ceibs_on_white.png",
    }
    email_body = render_to_string('events/emails/event_contact_email.html', context)
    email = EmailMessage(
        subject=f"Your Event '{event.name}' has been added successfully",
        body=email_body,
        to=[event.event_contact_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.content_subtype = 'html'
    # Attach the Excel file template
    excel_file = generate_event_participant_excel(event)
    if excel_file:
        email.attach(f'{event.name} Participants.xlsx', excel_file.getvalue(),
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send(fail_silently=False)


@shared_task
def send_event_contact_email(event_id):
    """
    Sends an email to the event contact email with event details,
    the CEIBS logo, and an attachment of an Excel template for participant details.
    """
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    # Build the context for the email template.
    context = {
        'event': event,
        'ceibs_logo_url': 'https://ab71-41-215-169-36.ngrok-free.app/static/assets/images/ceibs_on_white.png',
        'current_time': timezone.now(),
    }
    # Render the email body from the template.
    email_body = render_to_string('events/emails/event_contact_email.html', context)

    # Build and send the email.
    if event.event_contact_email:
        email = EmailMessage(
            subject=f"Event Confirmation: {event.name}",
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[event.event_contact_email],
        )
        email.content_subtype = 'html'
        # Optionally attach the Excel template if needed:
        excel_template_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'ceibsTemplate.xlsx')
        if os.path.exists(excel_template_path):
            email.attach_file(excel_template_path)
        email.send(fail_silently=False)













from django.db import models

from account.models import CustomUser


# Create your models here.
class Event(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=250, null=False, blank=False)
    description = models.CharField(max_length=500, null=False, blank=False)
    date = models.DateTimeField(null=True, blank=True)
    event_start_time = models.TimeField(null=True, blank=True)
    duration = models.CharField(max_length=100, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    number_of_participants = models.PositiveIntegerField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    venue = models.CharField(null=True, blank=True, max_length=250)
    event_type = models.CharField(null=True, blank=True, max_length=250, choices=(("In House", "In House"), ("External", "External")))
    department = models.CharField(null=True, blank=True, max_length=200)
    presence_choices = (
        ('Virtual', 'Virtual'),
        ('In-person', 'In-person'),
    )
    presence = models.CharField(max_length=250, null=True, blank=True, choices=presence_choices)
    active = models.BooleanField(default=True)
    event_contact_name = models.CharField(max_length=250, null=True, blank=True)
    event_contact_email = models.CharField(max_length=250, null=True, blank=True)
    event_contact_phone = models.CharField(max_length=250, null=True, blank=True)
    event_image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    company = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.end_time and self.end_time.date() > self.start_time.date():
            # Ensure end_time is set to midnight of the day after the end date
            self.end_time = self.end_time.replace(hour=23, minute=59, second=59)
        super().save(*args, **kwargs)

    def calculate_duration(self):
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return duration.days + 1
        return None


class EventDocument(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    document = models.FileField(upload_to='event_documents/', null=True, blank=True)
    document_name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.document_name



class EventParticipant(models.Model):
    event = models.ForeignKey(Event, related_name='participants', on_delete=models.CASCADE)
    title = models.CharField(max_length=250, null=True, blank=True)
    last_name = models.CharField(max_length=250, null=False, blank=False)
    first_name = models.CharField(max_length=250, null=False, blank=False)
    other_names = models.CharField(max_length=250, null=True, blank=True)
    phone_contact = models.CharField(max_length=250, null=False, blank=False, unique=True)
    email_address = models.EmailField(null=False, blank=False, unique=True)
    company = models.CharField(max_length=250, null=True, blank=True)
    position = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"











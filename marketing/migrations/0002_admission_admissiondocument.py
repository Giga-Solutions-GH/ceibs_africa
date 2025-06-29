# Generated by Django 5.1.6 on 2025-03-15 17:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Admission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=250)),
                ('last_name', models.CharField(max_length=250)),
                ('other_names', models.CharField(blank=True, max_length=250, null=True)),
                ('phone_number', models.PositiveBigIntegerField()),
                ('email', models.EmailField(max_length=254)),
                ('company', models.CharField(blank=True, max_length=300, null=True)),
                ('position', models.CharField(blank=True, max_length=250, null=True)),
                ('date_submitted', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('under_review', 'Under Review'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AdmissionDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate', models.FileField(blank=True, null=True, upload_to='admissions/certificates/')),
                ('transcript', models.FileField(blank=True, null=True, upload_to='admissions/transcripts/')),
                ('other_document', models.FileField(blank=True, null=True, upload_to='admissions/others/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('review_status', models.CharField(choices=[('pending', 'Pending'), ('under_review', 'Under Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('admission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='marketing.admission')),
            ],
        ),
    ]

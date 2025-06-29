# Generated by Django 5.1.6 on 2025-02-24 12:54

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attendance_date', models.DateField(blank=True, default=django.utils.timezone.now, null=True)),
                ('comment', models.CharField(blank=True, max_length=500, null=True)),
                ('is_present', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_name', models.CharField(max_length=250)),
                ('course_description', models.CharField(blank=True, max_length=250, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('flag', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flag', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='GeneratedTranscriptRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transcript_file', models.FileField(upload_to='generated_transcripts/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('show_transcript', models.BooleanField(default=False)),
                ('flag', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Lecturer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=200)),
                ('other_names', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=250)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.PositiveBigIntegerField(blank=True, null=True)),
                ('department', models.CharField(blank=True, max_length=250, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='lecturers/')),
                ('flag', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='LecturerType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('ceibs_professor', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_name', models.CharField(max_length=250)),
                ('program_code', models.CharField(blank=True, max_length=200, null=True)),
                ('duration', models.CharField(blank=True, max_length=250, null=True)),
                ('description', models.CharField(blank=True, max_length=250, null=True)),
                ('number_of_modules', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('alumni_program', models.BooleanField(blank=True, default=False, null=True)),
                ('program_ended', models.BooleanField(blank=True, default=False, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('flag', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramCover',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=200)),
                ('other_names', models.CharField(blank=True, max_length=200, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone_number', models.PositiveBigIntegerField(blank=True, null=True)),
                ('position', models.CharField(blank=True, max_length=200, null=True)),
                ('company', models.CharField(blank=True, max_length=250, null=True)),
                ('flag', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=250)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('flag', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='TranscriptRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year_of_completion', models.CharField(max_length=250)),
                ('generated', models.BooleanField(default=False)),
            ],
        ),
    ]

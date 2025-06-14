# Generated by Django 5.1.6 on 2025-03-19 14:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_program', '0008_alter_program_assistant_program_officer_and_more'),
        ('marketing', '0003_admission_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='admission',
            name='cv',
            field=models.FileField(blank=True, null=True, upload_to='admissions/cvs/'),
        ),
        migrations.AddField(
            model_name='admission',
            name='passport_front_page',
            field=models.ImageField(blank=True, null=True, upload_to='admissions/passport_front_pages/'),
        ),
        migrations.AddField(
            model_name='admission',
            name='passport_picture',
            field=models.ImageField(blank=True, null=True, upload_to='admissions/passport_pictures/'),
        ),
        migrations.AddField(
            model_name='prospect',
            name='program_of_interest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='academic_program.programcover'),
        ),
        migrations.AlterField(
            model_name='prospectfeedback',
            name='prospect',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='marketing.prospect'),
        ),
        migrations.CreateModel(
            name='AdmissionCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate', models.FileField(upload_to='admissions/certificates/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('review_status', models.CharField(choices=[('pending', 'Pending'), ('under_review', 'Under Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('admission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='marketing.admission')),
            ],
        ),
        migrations.CreateModel(
            name='AdmissionTranscript',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transcript', models.FileField(upload_to='admissions/transcripts/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('review_status', models.CharField(choices=[('pending', 'Pending'), ('under_review', 'Under Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('admission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transcripts', to='marketing.admission')),
            ],
        ),
        migrations.DeleteModel(
            name='AdmissionDocument',
        ),
    ]

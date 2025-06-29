# Generated by Django 5.1.6 on 2025-03-21 13:33

import marketing.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0007_remove_admissiontranscript_admission_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admission',
            name='certificate_files',
            field=models.FileField(blank=True, null=True, upload_to=marketing.models.certificate_files_upload),
        ),
        migrations.AlterField(
            model_name='admission',
            name='cv',
            field=models.FileField(blank=True, null=True, upload_to=marketing.models.cv_upload),
        ),
        migrations.AlterField(
            model_name='admission',
            name='other_files',
            field=models.FileField(blank=True, null=True, upload_to=marketing.models.other_files_upload),
        ),
        migrations.AlterField(
            model_name='admission',
            name='passport_front_page',
            field=models.ImageField(blank=True, null=True, upload_to=marketing.models.passport_front_page_upload),
        ),
        migrations.AlterField(
            model_name='admission',
            name='passport_picture',
            field=models.ImageField(blank=True, null=True, upload_to=marketing.models.passport_picture_upload),
        ),
        migrations.AlterField(
            model_name='admission',
            name='transcript_files',
            field=models.FileField(blank=True, null=True, upload_to=marketing.models.transcript_files_upload),
        ),
    ]

# Generated by Django 5.1.6 on 2025-03-15 22:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_program', '0007_alter_coursecovers_program_cover'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='assistant_program_officer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assistant_program_officer', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='program',
            name='program_officer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='program_officer', to=settings.AUTH_USER_MODEL),
        ),
    ]

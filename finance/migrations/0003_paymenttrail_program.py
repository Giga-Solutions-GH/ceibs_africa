# Generated by Django 5.1.6 on 2025-03-12 18:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_program', '0002_initial'),
        ('finance', '0002_paymenttrail'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymenttrail',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='academic_program.program'),
        ),
    ]

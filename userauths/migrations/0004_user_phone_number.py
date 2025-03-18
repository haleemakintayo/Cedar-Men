# Generated by Django 5.0.1 on 2025-03-15 15:29

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userauths', '0003_alter_user_fullname'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region='GB', unique=True),
        ),
    ]

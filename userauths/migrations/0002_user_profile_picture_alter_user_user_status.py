# Generated by Django 5.0.1 on 2025-03-10 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauths', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='staff_images/'),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_status',
            field=models.CharField(choices=[('staffs', 'Staff'), ('customers', 'Customer')], default='customers', max_length=20),
        ),
    ]

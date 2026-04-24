# Generated migration for Royal Mail shipping fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_add_guest_session_key'),  # Depends on latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='label_file',
            field=models.FileField(
                blank=True,
                help_text='Stored PDF label from Royal Mail',
                null=True,
                upload_to='shipping_labels/%Y/%m/%d/'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='label_url',
            field=models.URLField(
                blank=True,
                help_text='URL to the generated shipping label',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_created_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the shipping label was created',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_error_message',
            field=models.TextField(
                blank=True,
                help_text='Error details if shipping creation failed',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_reference',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Unique reference returned by Royal Mail API',
                max_length=100,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('label_generated', 'Label Generated'),
                    ('manifested', 'Manifested'),
                    ('in_transit', 'In Transit'),
                    ('delivered', 'Delivered'),
                    ('failed', 'Failed'),
                ],
                db_index=True,
                default='pending',
                help_text='Current shipping status from Royal Mail',
                max_length=20
            ),
        ),
    ]
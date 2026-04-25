# Generated migration for product weight field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0013_product_extra_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='product_weight',
            field=models.PositiveIntegerField(default=500, help_text='Weight in grams for shipping calculations'),
        ),
    ]
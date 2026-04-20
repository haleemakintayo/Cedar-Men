from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
from ecommerce.models import Product, Color, Size

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    SHIPPING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('label_generated', 'Label Generated'),
        ('manifested', 'Manifested'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    order_number = models.CharField(max_length=32, unique=True, db_index=True, blank=True, null=True)
    guest_session_key = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Royal Mail Click & Drop Shipping Fields
    shipping_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Unique reference returned by Royal Mail API"
    )
    label_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to the generated shipping label"
    )
    label_file = models.FileField(
        upload_to='shipping_labels/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Stored PDF label from Royal Mail"
    )
    shipping_status = models.CharField(
        max_length=20,
        choices=SHIPPING_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current shipping status from Royal Mail"
    )
    shipping_created_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the shipping label was created"
    )
    shipping_error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error details if shipping creation failed"
    )

    @classmethod
    def generate_order_number(cls):
        date_part = timezone.now().strftime('%Y%m%d')
        while True:
            token = secrets.token_hex(4).upper()
            order_number = f"ORD-{date_part}-{token}"
            if not cls.objects.filter(order_number=order_number).exists():
                return order_number

    def get_total_weight_grams(self):
        """Calculate total weight of order items in grams.
        Defaults to 500g per item if product weight not available."""
        total_weight = 0
        for item in self.items.all():
            product_weight = getattr(item.product, 'weight_grams', 500)
            total_weight += product_weight * item.quantity
        return total_weight or 500  # Default to 500g if empty

    def __str__(self):
        return self.order_number or f"Order {self.id}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

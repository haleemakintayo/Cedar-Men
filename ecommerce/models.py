from django.db import models
from django.utils.text import slugify 
from django.shortcuts import reverse 
from django.conf import settings
from django.utils import timezone
from userauths.models import User
from django.apps import apps
from userauths.utils import generate_invoice_number
from decimal import Decimal
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    image = models.ImageField(upload_to='category/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    icon_class = models.CharField(max_length=100, blank=True, null=True) 

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        

class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, blank=True, null=True,
                                help_text="Optional hex code, e.g., #FFFFFF")

    def __str__(self):
        return self.name
class Size(models.Model):
    label = models.CharField(max_length=10, unique=True)
    order = models.PositiveIntegerField(help_text="Ordering value: lower numbers come first.")

    class Meta:
        ordering = ['order']  # Ensures that when you query Size objects, they are sorted by 'order'

    def __str__(self):
        return self.label        

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, default=1)
    stock = models.IntegerField()
    colors = models.ManyToManyField(Color, blank=True)
    image = models.ImageField(upload_to='products/')
    product_cart = models.BooleanField(default=False)
    sizes = models.ManyToManyField(Size, blank=True)
    description = models.TextField(blank=True, null=True)
    more_info = models.TextField(blank=True, null=True)
    composition = models.CharField(max_length=255, blank=True, null=True)
    style = models.CharField(max_length=255, blank=True, null=True)
    properties = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_url(self):
        return reverse("product_detail", kwargs={
            'slug': self.slug
        })
    

class Wishlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wishlist for {self.user.username}"
    
    def add_product(self, product):
        """Add a product to the wishlist."""
        self.products.add(product)
    
    def remove_product(self, product):
        """Remove a product from the wishlist."""
        self.products.remove(product)   







class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    rating = models.PositiveIntegerField(default=5)  
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username if self.user else 'Anonymous'}"
  


 

class Blog(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='blog_images/')
    publish_date = models.DateField()

    def __str__(self):
        return self.title

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    image = models.ImageField(upload_to='team_images/')
    bio = models.TextField()
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    google_plus = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Invoice(models.Model):
    # Order = apps.get_model('orders', 'Order')

    status_choices = [
        ("pending", "Pending"), 
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, default=generate_invoice_number, blank=False, null=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE,   null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=status_choices, default="pending")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.invoice_number 

    def calculate_total(self):
        total = sum(Decimal(item.total_price) for item in self.invoiceitem_set.all() if item.total_price is not None)
        self.total_amount = total
        self.save()

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255, default='Nil')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return Decimal(self.unit_price or 0) * Decimal(self.quantity or 0)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) # Save the item first
        self.invoice.calculate_total()

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
    

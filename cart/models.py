from django.db import models
from django.conf import settings
from ecommerce.models import Product, Color, Size

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user and isinstance(self.user.fullname, str) and self.user.fullname.strip(): 
            names = self.user.fullname.split() # Auto handles mutiple spaces 
            if len(names) > 1: 
                return f"Cart for {names[1]}"
            return f"Cart for {names[0]}"
        return f"Cart {self.session_key}"

    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())
    
    def total_weight(self):
        """Calculate total weight of all items in cart in grams."""
        return sum(item.total_weight() for item in self.items.all())
    
    def total_weight_kg(self):
        """Return total weight in kilograms."""
        return self.total_weight() / 1000
    
    def get_shipping_weight_category(self):
        """Get shipping weight category for Royal Mail.
        Returns: 'small' (<1kg), 'medium' (1-2kg), 'large' (2-5kg), 'xlarge' (>5kg)"""
        weight_kg = self.total_weight_kg()
        if weight_kg < 1:
            return 'small'
        elif weight_kg < 2:
            return 'medium'
        elif weight_kg < 5:
            return 'large'
        else:
            return 'xlarge'

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, blank=True, null=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, blank=True, null=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def subtotal(self):
        return self.product.price * self.quantity
    
    def weight(self):
        """Get weight of this cart item in grams.
        Uses product's product_weight field (default 500g)."""
        return getattr(self.product, 'product_weight', 500)
    
    def total_weight(self):
        """Get total weight of this cart item (weight × quantity) in grams."""
        return self.weight() * self.quantity
    
    def total_weight_kg(self):
        """Get total weight in kilograms."""
        return self.total_weight() / 1000

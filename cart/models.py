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

from django.db import models
from django.utils.text import slugify
from django.shortcuts import reverse 



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
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
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
    


 #Im waiting for the auth to finish before implementing it   
# class Review(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     comment = models.TextField()
#     rating = models.PositiveIntegerField(default=5)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"Review by {self.user.username} on {self.product.name}"    


 

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
  


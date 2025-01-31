from django.db import models

# Create your models here.

from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='products/')
    product_cart = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    


 

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
  


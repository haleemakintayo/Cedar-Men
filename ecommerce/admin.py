from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'old_price', 'product_cart')
    search_fields = ('name',)
    list_filter = ('product_cart',)



from .models import Blog, TeamMember

# Register the Blog model with the admin site
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date', 'description', 'image')  # Fields to display in the admin list view
    search_fields = ('title', 'description')  # Fields to search within the admin panel
    list_filter = ('publish_date',)  # Filters for the admin panel


admin.site.register(TeamMember)    


# OR (Alternative)
# admin.site.register(Product)

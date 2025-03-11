from django.contrib import admin

# Register your models here.
from django import forms
from django.contrib import admin
from .models import(
    Product,Color,
    Blog, TeamMember,
    Size,Category, Invoice, InvoiceItem
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'old_price', 'product_cart')
    search_fields = ('name',)
    list_filter = ('product_cart',)


admin.site.register(Color)
admin.site.register(Size)
admin.site.register(Category)
# Register the Blog model with the admin site
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date', 'description', 'image')  # Fields to display in the admin list view
    search_fields = ('title', 'description')  # Fields to search within the admin panel
    list_filter = ('publish_date',)  # Filters for the admin panel


admin.site.register(TeamMember)

# Invoices:
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'created_at', 'status', 'total_amount')
    list_filter = ('status', 'created_at')
    search_fields =  ('invoice_number', 'customer__fullname', 'customer__email')
    inlines = [InvoiceItemInline]

# OR (Alternative)
# admin.site.register(Product)
admin.site.register(Invoice, InvoiceAdmin)
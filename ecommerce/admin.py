from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Blog, Category, Color, Invoice, InvoiceItem, Product, Size, TeamMember


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "price", "weight_grams", "tax_class", "shipping_format")
    list_filter = ("tax_class", "shipping_format")
    ordering = ("name",)

    @admin.display(description="Weight (g)", ordering="product_weight")
    def weight_grams(self, obj):
        return obj.product_weight

    def get_search_fields(self, request):
        model_field_names = {field.name for field in self.model._meta.fields}
        secondary_field = "sku" if "sku" in model_field_names else "slug"
        return ("name", secondary_field)


@admin.register(Color)
class ColorAdmin(ModelAdmin):
    search_fields = ("name", "hex_code")
    list_display = ("name", "hex_code")


@admin.register(Size)
class SizeAdmin(ModelAdmin):
    list_display = ("label", "order")
    ordering = ("order", "label")
    search_fields = ("label",)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Blog)
class BlogAdmin(ModelAdmin):
    list_display = ("title", "publish_date", "description", "image")
    search_fields = ("title", "description")
    list_filter = ("publish_date",)


@admin.register(TeamMember)
class TeamMemberAdmin(ModelAdmin):
    list_display = ("name", "role")
    search_fields = ("name", "role", "bio")


class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ("invoice_number", "customer", "created_at", "status", "total_amount")
    list_filter = ("status", "created_at")
    search_fields = ("invoice_number", "customer__fullname", "customer__email")
    inlines = [InvoiceItemInline]

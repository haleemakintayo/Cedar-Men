from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "color", "size", "quantity", "price")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_number", "customer_name", "total", "shipping_status", "created_at")
    list_filter = ("shipping_status", "created_at")
    search_fields = ("order_number", "email", "first_name", "last_name", "shipping_reference")
    readonly_fields = ("order_number", "created_at", "shipping_reference", "label_file")
    inlines = [OrderItemInline]
    ordering = ("-created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order_number",
                    "user",
                    "status",
                    "created_at",
                    "paid_at",
                    "total",
                )
            },
        ),
        (
            "Customer Details",
            {
                "fields": (
                    ("first_name", "last_name"),
                    "email",
                    "address",
                    ("city", "state"),
                    ("postcode", "country"),
                )
            },
        ),
        (
            "Payment Data",
            {
                "fields": (
                    "guest_session_key",
                    "stripe_session_id",
                    "stripe_payment_intent_id",
                )
            },
        ),
        (
            "Royal Mail Shipping Data",
            {
                "fields": (
                    "shipping_reference",
                    "label_url",
                    "label_file",
                    "shipping_status",
                    "shipping_created_at",
                    "shipping_error_message",
                )
            },
        ),
    )

    @admin.display(description="Customer")
    def customer_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name or obj.email


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ("order", "product", "quantity", "price", "color", "size")
    list_filter = ("color", "size")
    search_fields = ("order__order_number", "product__name")

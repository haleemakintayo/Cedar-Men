from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "color", "size", "quantity")


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("id", "cart_owner", "session_key", "item_count", "cart_total", "created_at", "updated_at")
    search_fields = ("user__email", "user__fullname", "session_key")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CartItemInline]
    ordering = ("-updated_at",)

    @admin.display(description="Owner")
    def cart_owner(self, obj):
        if obj.user:
            return obj.user.fullname or obj.user.email
        return "Guest"

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.total_items()

    @admin.display(description="Total")
    def cart_total(self, obj):
        return obj.total_price()


@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ("cart", "product", "quantity", "color", "size", "subtotal")
    search_fields = ("cart__session_key", "cart__user__email", "product__name")

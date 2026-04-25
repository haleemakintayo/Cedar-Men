from django.urls import path
from .views import checkout, order_confirmation, stripe_checkout_success, stripe_checkout_cancel, order_tracking, calculate_checkout_totals_api

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('checkout/calculate-totals/', calculate_checkout_totals_api, name='calculate_checkout_totals_api'),
    path('checkout/success/', stripe_checkout_success, name='stripe-checkout-success'),
    path('checkout/cancel/', stripe_checkout_cancel, name='stripe-checkout-cancel'),
    path('order-confirmation/<str:order_number>/', order_confirmation, name='order_confirmation'),
    path('tracking/', order_tracking, name='order_tracking'),
]

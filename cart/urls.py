from django.urls import path
from .views import cart_summary, update_cart_item, remove_cart_item,add_to_cart

urlpatterns = [
    path('', cart_summary, name='cart_summary'),
    path('update/', update_cart_item, name='update_cart_item'),
    path('remove/', remove_cart_item, name='remove_cart_item'),
    path('add/<slug:product_slug>/', add_to_cart, name='add_to_cart'),

]

from django.urls import path,include



from .views import (
    home, shop, blog_list,
    about_us, contact_us,blog_details,
    product_details,checkout

    )

urlpatterns = [
    path('', home, name='home'),
    path('ecommerce/shop/', shop, name='shop'),
    path('ecommerce/about/', about_us, name='about_us'),
    path('ecommerce/contact/', contact_us, name='contact_us'),
    path('blog/', blog_list, name='blog'),  # Listing of all blogs
    path('blog/<int:id>/', blog_details, name='blog_details'),  
    path('product/<slug:slug>/', product_details, name='product_detail'),
    path('cart/', include('cart.urls')),
    path('ecommerce/checkout/', checkout, name='checkout'),
]






from django.urls import path,include
# from .views import home



# urlpatterns = [
#     path('', home, name='home'),
    
   
   
# ]


from django.urls import path
from . import views 
from .views import home, shop_page, blog_list,about_us, contact_us

urlpatterns = [
    path('', home, name='home'),
    path('ecommerce/shop/', shop_page, name='shop_page'),
    path('ecommerce/about/', about_us, name='about_us'),
    path('ecommerce/contact/', contact_us, name='contact_us'),
    path('blog/', blog_list, name='blog'),  # Listing of all blogs
    path('blog/<int:id>/', views.blog_details, name='blog_details'),  # Ensure 'blog_details' is the correct name here
]






from django.urls import path, include
from . import views

urlpatterns = [
  path('login/', views.login_view, name='login'), 
  path('register/', views.register, name='register'),
  path('logout/', views.logout_view, name='logout'),

  #admin urls: 
  path('dashboard-admin/', views.dashboard_admin, name='admin-dashboard'),
  path('dashboard-admin/login', views.login_admin, name='login-admin'),
  path('dashboard-admin/register', views.register_admin, name='register-admin'),
  path('dashboard-admin/breadcrumb', views.dashboard_breadcrumb, name='dashboard-breadcrumb'),

  # Admin products views 
  path('dashboard-admin/products', views.dashboard_products, name='dashboard-products'),
  path('dashboard-admin/delete-product/<int:product_id>', views.delete_products, name='delete-products'),
  path('dashboard-admin/edit-product/<int:product_id>', views.edit_products, name='edit-products'),
  path('dashboard-admin/create-product', views.create_product, name='create-product'),
  path('dashboard-admin/orders', views.order_list, name='dashboard-orders'),

  #Invoices
  path('invoices/', views.invoice_list, name='invoice-list'), # Invoice list
  path('invoices/<int:invoice_id>/', views.view_invoice, name='view-invoice'), # Invoice detail 
  path('invoices-admin/<int:invoice_id>/', views.view_invoice_admin, name='view-invoice-admin'), # Invoice detail admin
  path('orders/<int:order_id>/generate-invoice/', views.generate_invoice, name='generate-invoice'), # Generate invoice 

  # Staff urls
  path('dashboard-admin/staffs', views.staff_list, name='staff-list'), 
  path('dashboard-admin/add-staff', views.register_staff, name='add-staff'),
  path('staff/<int:staff_id>/', views.staff_detail_view, name='staff-detail'),
  path('staff/delete-staff/<int:staff_id>/', views.delete_staff, name='delete-staff'),
  path('staff/edit-profile', views.edit_staff_profile, name='edit-profile'),
  path('staff/change_password', views.change_password, name='change-password'),
]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login, authenticate, update_session_auth_hash
from django.contrib import messages
from .forms import UserForm, LoginForm, StaffLoginForm, StaffProfileForm, ChangePasswordForm
from .models import User
from ecommerce.models import Product, InvoiceItem, Invoice
from orders.models import Order
from .utils import staff_required, generate_invoice_number, render_to_pdf
from django.core.paginator import Paginator
from ecommerce.forms import ProductForm, InvoiceItemForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

# Add your views here:

# Test cases: 
def is_admin(user):
  return user.is_superuser or user.has_perm('auth.view_user')

def login_view(request):
  if request.user.is_authenticated: 
    return redirect('home') # Redirect if already logged in 
  
  if request.method == "POST":
    form = LoginForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data['email']
      password = form.cleaned_data['password']

      # Find the user by email
      try: 
        user = User.objects.get(email=email)
      except User.DoesNotExist: 
        user = None

      # Authenticate using email instead of username: 
      if user is not None and user.check_password(password): 
        login(request, user)
        messages.success(request, "Login successful!")
        return redirect('home') # Redirect to home page after logging in. 
      else: 
        messages.error(request, "Invalid email or password.")
  else: 
    form = LoginForm()

  return render(request, 'login.html', {'form':form})

def register(request):
  if request.method == 'POST': 
    form = UserForm(request.POST, request=request)
    if form.is_valid():
      user = form.save()

      # Authenticate and log in the user
      email = form.cleaned_data.get('email')
      password = form.cleaned_data.get('password1')

      user = authenticate(email=email, password=password)
      if user is not None: 
        login(request, user)
        return redirect('home')
  else: 
    form = UserForm(request=request)
  return render(request, 'register.html', {'form':form})

    
def logout_view(request): 
  if request.user.is_authenticated: 
    is_staff = request.user.is_staff

    logout(request)

    if is_staff: 
      return redirect('login-admin')
    
  return redirect('login')

# Admin and Staffs:
@staff_required
def dashboard_admin(request):
  user = request.user

  return render(request, 'theme/index.html')

def register_admin(request):
  return render(request, 'theme/sign-up.html')

def dashboard_breadcrumb(request):
  return render(request, 'theme/breadcrumb.html')

# Login admin
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import StaffLoginForm
from .models import User

def login_admin(request):
    if request.method == "POST":
        form = StaffLoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Find the user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            # Authenticate using email instead of username
            if user is not None and user.is_staff and user.check_password(password):
                login(request, user)

                if user.force_password_change:
                    return redirect('change-password')
                
                return redirect('admin-dashboard')  # Redirect to dashboard after logging in.
            else:
                form.add_error(None, "Invalid email or password.")  # Add non-field error
        else:
            messages.error(request, "Please correct the errors below.")  # Generic error message

    else:
        form = StaffLoginForm()

    return render(request, 'theme/sign-in.html', {'form': form})


@login_required
def change_password(request):
    user = request.user
    
    if request.method == "POST":
        form = ChangePasswordForm(user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password1"]  # Corrected syntax
            user.set_password(new_password)  # Update password
            user.force_password_change = False  # Mark password as changed
            print("Form submitted")
            print(f"User Status Before Save: {user.force_password_change}")
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            
            messages.success(request, "Your password has been successfully updated.")
            return redirect("admin-dashboard")  # Ensure this URL exists
        
        else:  # Debug why the form is failing
            print(form.errors)  # Logs errors in the terminal
            messages.error(request, "Please correct the errors below.")
    
    else:
        form = ChangePasswordForm(user)

    return render(request, "theme/change_password.html", {"form": form})
# Product management: 
def dashboard_products(request):
  product_queryset = Product.objects.all().order_by('-created_at') # Get all products, newest first.

  query = request.GET.get("q", "")
  
  if query: 
    product_queryset = product_queryset.filter(name__icontains=query) # Search by product name

  # Paginate with 10 products per page: 
  paginator = Paginator(product_queryset, 10)
  page_number = request.GET.get('page') # Get page number from URL
  products = paginator.get_page(page_number) # Get paginated products

  return render(request, 'theme/products.html', {'products': products, "query": query}) 

def create_product(request):
  if request.method == 'POST':
    form = ProductForm(request.POST, request.FILES)
    if form.is_valid():
      form.save()
      messages.success(request, "Product created successfully!")
      return redirect('dashboard-products')
    else: 
      messages.error(request, "Please correct the errors below.")
  else: 
    form = ProductForm()

  return render(request, 'theme/create_product.html', {'form':form})

def edit_products(request, product_id):
  product = get_object_or_404(Product, id=product_id)

  if request.method == 'POST':
    form = ProductForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
      form.save()
      messages.success(request, "Product updated successfully!")
      return redirect('dashboard-products')
  else: 
    form = ProductForm(instance=product)

  return render(request, 'theme/edit_product.html', {'form': form, 'product':product})

def delete_products(request, product_id):
  product = get_object_or_404(Product, id=product_id)
  product.delete()
  messages.success(request, "Product deleted sucessfully!")

  return redirect('dashboard-products')


##################### Invoice views:
def generate_invoice(request, order_id):
  order = get_object_or_404(Order, id=order_id, user=request.user)

  # Check if invoice already exists
  invoice, created = Invoice.objects.get_or_create(
    order=order,
    defaults={
      'invoice_number': generate_invoice_number(),
      'customer': request.user,
      'status': 'pending', 
    }
  )

  # If new invoice, create invoice items
  if created: 
    for order_item in order.items.all():
      InvoiceItem.objects.create(
        invoice=invoice,
        product_name=order_item.product.name,
        quantity=order_item.quantity,
        unit_price=order_item.product.price
      )
  
  return redirect('view-invoice', invoice_id=invoice.id)

@login_required
def view_invoice(request, invoice_id):
  invoice = get_object_or_404(Invoice, id=invoice_id, customer=request.user)

  return render(request, 'theme/invoice_detail.html', {'invoice': invoice})

@login_required
def view_invoice_admin(request, invoice_id):
  invoice = get_object_or_404(Invoice, id=invoice_id, customer=request.user)

  return render(request, 'theme/invoice_detail_admin.html', {'invoice': invoice})

@login_required
def invoice_list(request):
  if request.user.is_staff:
    invoices = Invoice.objects.all().order_by('-created_at')
  else: 
    invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')

  query = request.GET.get("q", "")

  if query: 
    invoices = invoices.filter(invoice_number__icontains=query)

  # Paginate with 10 products per page:  
  paginator = Paginator(invoices, 10)
  page_number = request.GET.get('page') # Get page number from URL
  invoice = paginator.get_page(page_number) # Get paginated products

  return render(request, 'theme/invoice_list.html', {'invoice': invoice, 'invoices': invoices, "query": query}) 

def download_invoice_pdf(request, invoice_id):
  invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

  data = {
    'invoice': invoice,
    'company_name': 'Cedar Men',
    'company_address': '123 Business Street',
    'company_city': 'Business city',
    'company_phone': '+1234567890',
    'company_email': 'info@cedarmen.com',
  }

  pdf = render_to_pdf('theme/invoices_pdf.html', data)

  if pdf: 
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Invoice_{invoice.invoice_number}.pdf"
    content = f'inline; filename={filename}'
    response['Content-Disposition'] = content
    return response
  
  return HttpResponse("Eror generating PDF", status=400)

@login_required 
def order_list(request):
  orders = Order.objects.all().order_by('-created_at')

  query = request.GET.get("q", "")

  if query:
    orders = orders.filter(customer__fullname__icontains=query) 

  # Paginate with 10 products per page:
  paginator = Paginator(orders, 10)
  page_number = request.GET.get('page')
  order = paginator.get_page(page_number)

  return render(request, 'theme/order_list.html', {'query':query, 'orders': orders, 'order': order})

def staff_list(request):
  users = User.objects.all()
  staff_queryset = users.filter(is_staff=True).order_by('-date_joined')

  query = request.GET.get("q", "")
  
  if query: 
    staff_queryset = staff_queryset.filter(fullname__icontains=query) # Search by product name

  # Paginate with 10 products per page: 
  paginator = Paginator(staff_queryset, 10)
  page_number = request.GET.get('page') # Get page number from URL
  staffs = paginator.get_page(page_number) # Get paginated products

  return render(request, 'theme/staff_list.html', {'staffs': staffs, "query": query}) 

@login_required
@user_passes_test(is_admin)
def staff_detail_view(request, staff_id):
  staff = get_object_or_404(User, id=staff_id, is_staff=True)

  return render(request, 'theme/staff_detail.html', {'staff': staff})

@login_required
def edit_staff_profile(request):
  staff = request.user

  if request.method == "POST":
    form = StaffProfileForm(request.POST, request.FILES, instance=staff)
    if form.is_valid():
      form.save()
      return redirect("admin-dashboard")
  else:
    form = StaffProfileForm(instance=staff)

  return render(request, "theme/edit_profile.html", {'form': form, 'staff': staff}) 

def register_staff(request):
  if request.method == 'POST': 
    form = UserForm(request.POST or None, request=request, is_staff_form=True)
    if form.is_valid():
      staff = form.save(commit=False)
      staff.set_password("Staff@1234")
      staff.user_status = 'staff'
      staff.is_staff = True
      staff.force_password_change = True
      staff.save()
      return redirect('staff-list')
  else: 
    form = UserForm(request=request, is_staff_form=True)

  return render(request, 'theme/add_staff.html',{'form':form})

def delete_staff(request, staff_id):
  staff = get_object_or_404(User, id=staff_id)
  staff.delete()
  messages.success(request, "Staff deleted sucessfully!")

  return redirect('staff-list')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from .forms import UserForm, LoginForm, StaffLoginForm
from .models import User
from ecommerce.models import Product, InvoiceItem, Invoice
from orders.models import Order
from .utils import staff_required, generate_invoice_number, render_to_pdf
from django.core.paginator import Paginator
from ecommerce.forms import ProductForm, InvoiceItemForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Add your views here:
 
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
    form = UserForm(request.POST)
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
    form = UserForm()
  return render(request, 'register.html', {'form':form})

def register_staff(request):
  if request.method == 'POST': 
    form = UserForm(request.POST, show_user_status=True)
    if form.is_valid():
      form.save()
  else: 
    form = UserForm(show_user_status=True)

  return render(request, 'theme/add_staff.html',{'form':form})
    
def logout_view(request): 
  logout(request) # Logs the user out
  return redirect('login') # Redirect to the Login page

# Admin and Staffs:
@staff_required
def dashboard_admin(request):
  user = request.user
  names = user.fullname.split(' ')

  if len(names) > 1:
    middlename = names[1];
  else: 
    middlename = 'Anonymous'

  return render(request, 'theme/index.html', {'middlename': middlename})

def register_admin(request):
  return render(request, 'theme/sign-up.html')

def dashboard_breadcrumb(request):
  return render(request, 'theme/breadcrumb.html')

# Login admin
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

      # Authenticate using email instead of username: 
      if user is not None and user.is_staff and user.check_password(password): 
        login(request, user)
        messages.success(request, "Login successful!")
        return redirect('admin-dashboard') # Redirect to dashboard after logging in. 
      else: 
        messages.error(request, "Invalid email or password.")
  else: 
    form = StaffLoginForm()

  return render(request, 'theme/sign-in.html', {'form':form})

# Product management: 
def dashboard_products(request):
  product_queryset = Product.objects.all().order_by('-created_at') # Get all products, newest first. 
  
  # Paginate with 10 products per page: 
  paginator = Paginator(product_queryset, 10)
  page_number = request.GET.get('page') # Get page number from URL
  products = paginator.get_page(page_number) # Get paginated products

  return render(request, 'theme/products.html', {'products': products}) 

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
    invoices = Invoice.objects.all(). order_by('-created_at')
  else: 
    invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')

  # Paginate with 10 products per page:  
  paginator = Paginator(invoices, 10)
  page_number = request.GET.get('page') # Get page number from URL
  invoice = paginator.get_page(page_number) # Get paginated products

  return render(request, 'theme/invoice_list.html', {'invoice': invoice, 'invoices': invoices}) 

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
  return render(request, "theme/order_list.html", {"orders": orders})

  
# @login_required 
# def edit_invoice(request, invoice_id):
#   invoice = get_object_or_404(Invoice, id=invoice_id)
#   items = InvoiceItem.objects.filter(invoice=invoice)

#   if request.method == "POST": 
#     form = InvoiceItemForm(request.POST)
#     if form.is_valid():
#       item = form.save(commit=False)
#       item.invoice = invoice
#       item.save()
#       invoice.calculate_total() # Recalculate total amount
#       return redirect("edit-invoice", invoice_id=invoice.id)
#   else: 
#     form = InvoiceItemForm()

#   return render(request, "theme/edit_invoice.html", {"invoice": invoice, "items": items, "form": form})
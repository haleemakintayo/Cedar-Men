
from django.shortcuts import render,redirect,get_object_or_404
from .forms import ContactForm
from .models import (
    Product, Blog,TeamMember,
    
    ) 

from django.core.mail import send_mail
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

def home(request):
    # Get all products
    products = Product.objects.all()

    # Get all blogs
    blogs = Blog.objects.all()

    # Pass both products and blogs to the template
    return render(request, 'index.html', {'products': products, 'blogs': blogs})


def about_us(request):
    team_members = TeamMember.objects.all()
    return render(request, 'about-us.html', {'team_members': team_members})


def shop(request):
    products = Product.objects.all()
    
    return render(request, 'shop.html',{'products': products})

def product_details(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:6] 
    range_list = range(1, 6)  # List to simulate range(0, 5)
    context = {
        'product': product,
        'range_list': range_list,
        'related_products': related_products,
    }
    return render(request, 'product-details.html', context)


def blog_list(request):
    return render(request, 'blog.html')


def blog_details(request, id):
    blog = Blog.objects.get(id=id)
    return render(request, 'blog_details.html', {'blog': blog})

def contact_us(request):
    return render(request, 'contact-us.html')




# def contact_us(request):
#     if request.method == "POST":
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             name = form.cleaned_data["name"]
#             email = form.cleaned_data["email"]
#             message = form.cleaned_data["message"]

#             # Send an email
#             send_mail(
#                 subject=f"New Message from {name}",
#                 message=message,
#                 from_email=email,
#                 recipient_list=["TheCedarBrand@outlook.com"],  # Change to your email
#             )

#             return redirect("contact_us")  # Redirect after successful form submission
#     else:
#         form = ContactForm()

#     return render(request, "contact-us.html", {"form": form})









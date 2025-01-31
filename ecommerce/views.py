from django.shortcuts import render,redirect

# Create your views here.


from django.shortcuts import render
# from .models import Product

# def home(request):
#     products = Product.objects.all()
#     return render(request, 'index.html', {'products': products})



from django.shortcuts import render
from .models import Product, Blog,TeamMember 

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


def shop_page(request):
    return render(request, 'shop.html')


def blog_list(request):
    return render(request, 'blog.html')


def blog_details(request, id):
    blog = Blog.objects.get(id=id)
    return render(request, 'blog_details.html', {'blog': blog})

def contact_us(request):
    return render(request, 'contact-us.html')









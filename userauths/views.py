from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from .forms import UserForm, LoginForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import User

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
    
def logout_view(request): 
  logout(request) # Logs the user out
  return redirect('login') # Redirect to the Login page
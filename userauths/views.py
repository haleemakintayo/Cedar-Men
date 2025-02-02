from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, CustomAuthenticationForm

# Sign up view
def register(request):
  if request.method == 'POST': 
    form = UserRegistrationForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, 'Account created successfully!')
      return redirect('login')
    else: 
      # Even if form is invalid, we still render the page with the form
      return render(request, 'register.html', {'form': form})
  else: 
    # For GET requests, display empty form
    form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


# Login view
def login_view(request):
    # if request.user.is_authenticated:
    #     return redirect('home')  # Redirect already logged-in users

    form = CustomAuthenticationForm(request, data=request.POST) if request.method == 'POST' else CustomAuthenticationForm()


    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)  # Corrected login function usage
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', {'form': form})

# Logout view
@login_required
def logout_view(request):
  logout(request)
  messages.success(request, 'You have been successfully logged out.')
  return redirect('login') #Replace 'login' with your login URL name
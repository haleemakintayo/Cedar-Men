from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import authenticate

class UserRegistrationForm(forms.Form): 
  # Define custom error messages
  error_messages = {
    'required': 'This field is required.', 
    'invalid': 'Please enter a valid value',
    'password_mismatch': 'The two password fields do not match.',
    'emial_exists': 'This email is already registered.',
    'username_exists': 'This username is already taken.', 
  }

  # Form fields with built-in validation 
  username = forms.CharField(
    min_length=3, 
    max_length=30,
    required=True,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Enter username'
    }),
    error_messages={
      'required': error_messages['required'], 
      'min_length': 'Username must be at least 3 characters long.',
      'max_length': 'Username cannot exceed 30 characters.'
    }
  )

  email = forms.EmailField(
    required=True, 
    widget=forms.EmailInput(attrs={
      'class': 'form-control', 
      'placeholder': 'Enter email'
    }), 
    error_messages={
      'required': error_messages['required'],
      'invalid': 'Pleae enter a valid email address'
    }
  )

  password1 = forms.CharField(
    required=True,
    widget=forms.PasswordInput(attrs={
      'class': 'form-control', 
      'placeholder': 'Enter password',
    }), 
    error_messages={
      'required': error_messages['required']
    }
  )

  password2 = forms.CharField(
    required=True,
    widget=forms.PasswordInput(attrs={
      'class': 'form-control', 
      'placeholder': 'Confirm password',
    }), 
    error_messages={
      'required': error_messages['required']
    }
  )

  phone_number = forms.CharField(
    required=True, 
    validators=[
      RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message='Phone number must be entered in the format: "+99999999". Up to 15 digits allowed.'
      )
    ], 
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Enter phone number'
    })
  )

  def clean_username(self):
    """Custom validation for username"""
    username = self.cleaned_data.get('username')

    # Example: Check if username contains only allowed characters
    if not username.isalnum():
      raise forms.ValidationError('Username can only contain letters and numbers.')

    # Example: Check if username exists in database
    from django.contrib.auth.models import User
    if User.objects.filter(username=username).exists():
      raise form.ValidationError(self.error_message['username_exists'])
    
    return username
  
  def clean_email(self): 
    """Custom validation for email"""
    email = self.cleaned_data.get('email')

    # Example: Check if email exists in database
    from django.contrib.auth.models import User
    if User.objects.filter(email=email).exists(): 
      raise forms.ValidationError(self.error_messages['email_exists'])

    return email
  
  def clean(self): 
    """Cross-field validation"""
    cleaned_data = super().clean()
    password1 = cleaned_data.get('password1')
    password2 = cleaned_data.get('password2')

    if password1 and password2: 
      # Validate password complexity
      try: 
        validate_password(password1)
      except forms.ValidationError as e: 
        self.add_error('password1', e)

        #Check if password match: 
        if password1 == password2: 
          raise forms.ValidationError({
            'password2': self.error_mesages['password_mismatch']
          })

    return cleaned_data

  def save(self):
    """Save the user data"""
    if self.is_valid():
      cleaned_data = self.cleaned_data
      # Create user object (example)
      from django.contrib.auth.models import User
      user = User.objects.create_user(
        username=cleaned_data['username'],
        email=cleaned_data['email'],
        password=cleaned_data['password1']
      )
      # Add additional fields as needed
      user.phone_number = cleaned_data['phone_number']
      user.save()
      return user
    return None

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )


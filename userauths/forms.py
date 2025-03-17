from django.forms import ModelForm
from django import forms
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm

class UserForm(ModelForm):
  class Meta: 
    model = User
    fields = [
      "fullname", 
      "email", 
      "phone_number",
      "password1", 
      "password2",
    ]

    widgets = {
      "fullname": forms.TextInput(attrs={
        'placeholder': "Full Name",
        'class': 'form-control',
      }),
      "email": forms.EmailInput(attrs={
        'placeholder': "Email",
        'class': 'form-control',
      }),
      'phone_number': forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter Phone Number',
      }),
      "password1": forms.PasswordInput(attrs={
        'placeholder': 'Password',
        'class': 'form-control',
      }), 
      "password2": forms.PasswordInput(attrs={
        'placeholder': "Confirm Password",
        'class': 'form-control',
      }),      
    }

  def __init__(self, *args, **kwargs):
    self.request = kwargs.pop('request', None)
    is_staff_form = kwargs.pop('is_staff_form', False)
    super().__init__(*args, **kwargs)

    if is_staff_form: 
       self.fields.pop('password1', None)
       self.fields.pop('password2', None)

    self.is_staff_form = is_staff_form # Store flag for later use

  def clean_fullname(self):
    fullname = self.cleaned_data.get('fullname')
    print("DEBUG: Raw Fullname from Form:", fullname)

    if fullname: 
      # Split the name into parts and filter out empty strings
      name_parts = [part.strip() for part in fullname.split() if part.strip()]

      # Check if there are at least two parts
      if len(name_parts) < 2: 
        raise ValidationError("Please enter your full name (first name, last name and or any other names.)")
      
      # Capitalize each part of the name
      fullname = ' '.join(part.capitalize() for part in name_parts)

      print("DEBUG: Cleaned Fullname:", fullname)

      return fullname

  def clean_email(self):
    email = self.cleaned_data.get('email')
    if User.objects.filter(email=email).exists():
      raise ValidationError('A user with that email already exists')
    return email
  
  def clean_password2(self):
    password1 = self.cleaned_data.get('password1')
    password2 = self.cleaned_data.get('password2')
    if password1 and password2 and password1 != password2: 
      raise ValidationError("Passwords do not match.")
    return password2
  
  def clean(self):
    cleaned_data = super().clean()
    password1 = cleaned_data.get('password1')

    if password1:
      try:    
        #Run the password through Django's validators
        validate_password(password1)
      except ValidationError as e:
        self.add_error('password1', e) 
    
    return cleaned_data
  
  def save(self, commit=True):
    # Stall the save process
    user = super().save(commit=False)

    # Ensure all fields are set correctly
    user.fullname = self.cleaned_data.get("fullname")
    user.email = self.cleaned_data.get("email")

    # Check where the form is submitted from (admin dashboard or frontend)
    if self.is_staff_form or (self.request and self.request.user.is_staff): 
        user.user_status = 'staff'  # Admin-created users get 'staff'
    else:
        user.user_status = 'customer'  # Frontend users get 'customer'

    # Set password securely
    if 'password1' in self.cleaned_data: 
       user.set_password(self.cleaned_data['password1'])

    # Assign staff permissions if the user is a staff member
    if user.user_status == "staff":
        user.is_staff = True
        user.is_superuser = False
    else:
        user.is_staff = False  

    if commit:
        user.save()

    return user

# Login form
class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}),
    )

class StaffLoginForm(forms.Form):
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={'class': 'form-control input-lg', 'placeholder': 'Enter your email', 'id': 'email', 'aria-describedby': 'emailHelp'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control inpout-lg', 'placeholder': 'Enter your password', 'id': 'password'}),
    )
    # account_type = forms.ChoiceField()
class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture', 'fullname', 'email', 'phone_number']

        widgets = {
            'fullname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Fullname',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email Address',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Phone Number',
            }),
        }

    # Custom styling for the image field
    profile_picture = forms.ImageField(
        required=False, 
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': "image/*",  
        })
    )

from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class ChangePasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

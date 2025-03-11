from django.forms import ModelForm
from django import forms
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserForm(ModelForm):
  class Meta: 
    model = User
    fields = [
      "fullname", 
      "email", 
      "user_status",
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
    show_user_status = kwargs.pop("show_user_status", False)
    super().__init__(*args, **kwargs)

    if show_user_status: 
      self.fields["user_status"] = forms.ChoiceField(
        choices=User.USER_CHOICES_FIELD, 
        widget=forms.Select(attrs={"class": "form-control"})
      )

    # for field in self.fields.items(): 
    #   field.widgets.attrs.update({"class": "form-control"})

  def clean_fullname(self):
    fullname = self.cleaned_data.get('fullname')
    if fullname: 
      # Split the name into parts and filter out empty strings
      name_parts = [part.strip() for part in fullname.split() if part.strip()]

      # Check if there are at least two parts
      if len(name_parts) < 2: 
        raise ValidationError("Please enter your full name (first name, last name and or any other names.)")
      
      # Capitalize each part of the name
      fullname = ' '.join(part.capitalize() for part in name_parts)

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

    email = self.cleaned_data['email']
    password = self.cleaned_data['password1']
    user_status = self.cleaned_data['user_status']

    if commit and user_status == 'staffs':
      user = User.objects.create_staff_user(email=email, password=password)

      user.save()

    else:
      user = User.objects.create_user(email=email, password=password)

      user.save()
    # # Set the password properly to hash it
    # user.set_password(self.cleaned_data['password1'])
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

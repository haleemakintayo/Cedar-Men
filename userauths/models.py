from django.db import models
from django.contrib.auth.models import  UserManager, AbstractBaseUser, PermissionsMixin
from model_utils import FieldTracker
from django.utils import timezone
from django.contrib.auth.models import Group
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class CustomUserManager(UserManager):
  def _create_user(self, email, password, **extra_fields):


    email = self.normalize_email(email)
    if not email: 
      raise ValueError("You have not provided a valid e-mail ")

    if self.model.objects.filter(email=email).exists():
      raise ValueError("A user with this email already exists.")
    
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)

    return user
  
  def create_user(self, email=None, password=None, **extra_fields): 
    extra_fields.setdefault('is_staff', False)
    extra_fields.setdefault('is_superuser', False)

    return self._create_user(email, password, **extra_fields)

  def create_superuser(self, email=None, password=None, **extra_fields): 
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)

    return self._create_user(email, password, **extra_fields)
  
  def create_staff_user(self, email=None, password=None, **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', False)
    extra_fields.setdefault('user_status', 'staffs')

    return self._create_user(email, password, **extra_fields)
  
class User(AbstractBaseUser, PermissionsMixin):
  USER_CHOICES_FIELD = [
    ('staffs', 'Staff'),
    ('customers', 'Customer'),
  ]

  email = models.EmailField(blank=True, default='', unique=True)
  fullname = models.CharField(max_length=225, blank=True, null=True)
  phone_number=PhoneNumberField(unique=True, blank=True, null=True, region="GB") # Change region as needed
  user_status = models.CharField(max_length=20, choices=USER_CHOICES_FIELD, default='customers')
  password1 = models.CharField(max_length=20, null=True)
  password2 = models.CharField(max_length=20, null=True)
  tracker=FieldTracker(fields=['user_status'])
  profile_picture=models.ImageField(upload_to='staff_images/', default="staff_images/blank_user_profile.png", blank=True, null=True)

  is_active = models.BooleanField(default=True)
  is_superuser = models.BooleanField(default=False)
  is_staff = models.BooleanField(default=False)
  force_password_change = models.BooleanField(default=False)

  date_joined = models.DateTimeField(default=timezone.now)
  last_login = models.DateTimeField(blank=True, null=True)
 
  objects = CustomUserManager()

  USERNAME_FIELD = 'email'
  EMAIL_FIELD = 'email'
  REQUIRED_FIELDS = []

  class Meta: 
    verbose_name = 'User'
    verbose_name_plural = 'Users'

  def __str__(self):
    return self.fullname or self.email

  def save(self, *args, **kwargs): 
    # First save the user instance 
    is_new = self.pk is None
    super(User, self).save()

    # Handle group assignment
    if is_new or self.tracker.has_changed('user_status'): 
      # Remove from all existing groups first
      self.groups.clear()
      # Create/get group based on user_status and add user to it
      group, _ = Group.objects.get_or_create(name=self.user_status)
      self.groups.add(group)

  def get_name(self):
    """Returns the middle name if available, otherwise returns the only name present."""
    if not self.fullname: 
      return ""
    
    name_parts = self.fullname.split()

    if len(name_parts) == 1 or len(name_parts) == 2: 
      return name_parts[0]
    if len(name_parts) >= 3:
      return name_parts[1]
    
    return ""

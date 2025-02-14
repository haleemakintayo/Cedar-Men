from django.db import models
from django.contrib.auth.models import  UserManager, AbstractBaseUser, PermissionsMixin
from model_utils import FieldTracker
from django.utils import timezone
from django.contrib.auth.models import Group

# Create your models here.

class CustomUserManager(UserManager):
  def _create_user(self, email, password, **extra_fields):


    email = self.normalize_email(email)
    if not email: 
      raise ValueError("You have not provided a valid e-mail ")
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
    extra_fields.setdefault('is_superuser', True)

    return self._create_user(email, password, **extra_fields)
  
class User(AbstractBaseUser, PermissionsMixin):
  USER_CHOICES_FIELD = [
    ('owner', 'Shop Owner'),
    ('managers', 'Manager'),
    ('staffs', 'Staff'),
    ('customers', 'Customer'),
  ]

  email = models.EmailField(blank=True, default='', unique=True)
  fullname = models.CharField(max_length=50, blank=True)
  user_status = models.CharField(max_length=20, choices=USER_CHOICES_FIELD, default='customers')
  password1 = models.CharField(max_length=20, null=True)
  password2 = models.CharField(max_length=20, null=True)
  tracker=FieldTracker(fields=['user_status'])

  is_active = models.BooleanField(default=True)
  is_superuser = models.BooleanField(default=False)
  is_staff = models.BooleanField(default=False)

  date_joined = models.DateTimeField(default=timezone.now)
  last_login = models.DateTimeField(blank=True, null=True)
 
  objects = CustomUserManager()

  USERNAME_FIELD = 'email'
  EMAIL_FIELD = 'email'
  REQUIRED_FIELDS = []

  class Meta: 
    verbose_name = 'User'
    verbose_name_plural = 'Users'

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

  def get_full_name(self):
    return self.fullname or self.email.split('@'[0])

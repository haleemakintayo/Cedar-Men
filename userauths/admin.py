from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .forms import UserForm
from .models import User

# Register your models here.
class CustomUserAdmin(UserAdmin):
  add_form = UserForm
  model = User

  fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('profile_picture', 'fullname', 'phone_number', 'user_status')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
  
  add_fieldsets = (
    (None, {
      'classes': ('wide',),
      'fields': ('email', 'fullname', 'user_status', 'password1', 'password2'),  # Replace username with email
    }),
  )

  # Fields to display in Django Admin
  list_display = ("fullname", "email", "user_status", "is_staff", "date_joined", "last_login",)
  list_display_links = ('email', 'fullname')
  ordering = ("email",)
  search_fields = ("email", "fullname")

  def save_model(self, request, obj, form, change):
    # Handle password only if provided in the form
    if form.cleaned_data.get("password1"):
      obj.set_password(form.cleaned_data['password1'])
    obj.save()

# Unregister any existing registration first to avoid conflicts
try: 
  admin.site.unregister(User)
except admin.sites.NotRegistered: 
  pass

# Register with our custom admin class
admin.site.register(User, CustomUserAdmin)

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ("email", "fullname", "phone_number", "user_status", "profile_picture")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        if password1:
            validate_password(password1, self.instance)

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class AdminUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see the user's password."),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "fullname",
            "phone_number",
            "user_status",
            "profile_picture",
            "password",
            "force_password_change",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean_email(self):
        email = self.cleaned_data["email"]
        queryset = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def clean_password(self):
        return self.initial.get("password")


class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm
    change_password_form = AdminPasswordChangeForm
    model = User

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("profile_picture", "fullname", "phone_number", "user_status", "force_password_change")},
        ),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "fullname",
                    "phone_number",
                    "user_status",
                    "profile_picture",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    list_display = ("fullname", "email", "user_status", "is_staff", "is_active", "date_joined", "last_login")
    list_display_links = ("email", "fullname")
    list_filter = ("user_status", "is_staff", "is_active", "is_superuser", "date_joined")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")
    search_fields = ("email", "fullname", "phone_number")

class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

# Unregister any existing registration first to avoid conflicts
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# Register with our custom admin class
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, GroupAdmin)

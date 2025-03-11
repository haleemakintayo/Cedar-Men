from django import forms
from django.forms import ModelForm
from .models import Product, Invoice, InvoiceItem, Size, Color
from userauths.models import User


class ProductForm(forms.ModelForm):
  colors = forms.ModelMultipleChoiceField(
    queryset = Color.objects.all(), # Fetch categories from the database
    widget=forms.CheckboxSelectMultiple, 
    required=True, 
  )

  sizes = forms.ModelMultipleChoiceField(
    queryset = Size.objects.all(),
    widget = forms.CheckboxSelectMultiple,
    required=True, 
  )
  class Meta:
    model = Product

    fields = [
      'name', 'price', 'old_price', 'stock', 'colors', 'image', 
      'sizes', 'description', 'more_info', 'composition', 'style', 'properties'
    ]
        
    widgets = {
      'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
      'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
      'old_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter old price'}),
      'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter stock quantity'}),
      'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter product description'}),
      'more_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter additional information'}),
      'composition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter composition details'}),
      'style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter style details'}),
      'properties': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product properties'}),
      'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),  # Image Upload with Bootstrap styling
    }

# class ContactForm(forms.Form):
#     name = forms.CharField(max_length=100)
#     email = forms.EmailField()
#     message = forms.CharField(widget=forms.Textarea

class InvoiceForm(forms.ModelForm):
  customer_name = forms.CharField(
    label='Customer Full Name',
    max_length=255,
    widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter full name"})
  )

  status = forms.ChoiceField(
    choices=[
      ("pending", "Pending"),
      ("paid", "Paid"), 
      ("failed", "Failed"),
    ],
    widget=forms.Select(attrs={"class": "form-control"})
  )

  class Meta: 
    model = Invoice 
    fields = ['customer_name', 'status']

    # widgets = {
    #   "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    # }

  def save(self, commit=True):
    customer_name= self.cleaned_data.get("customer")
    customer, created = User.objects.get(name=customer_name)

    invoice = super().save(commit=False)
    invoice.customer = customer

    if commit: 
      invoice.save()

    return invoice
   
class InvoiceItemForm(forms.ModelForm):
  class Meta: 
    model = InvoiceItem
    fields = ['product_name', 'quantity', 'unit_price']
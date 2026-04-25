from django import forms

class CheckoutForm(forms.Form):
    COUNTRY_CHOICES = [
        ('GB', 'United Kingdom'),
        ('US', 'United States'),
        ('FR', 'France'),
        ('DE', 'Germany'),
        ('AU', 'Australia'),
    ]
    
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address = forms.CharField(max_length=250, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postcode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_country'}))
# cart/utils.py
from cart.models import Cart
from decimal import Decimal

def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def calculate_cart_totals(cart, destination_country_code='GB'):
    subtotal = Decimal('0.00')
    tax = Decimal('0.00')
    total_weight = 0
    
    format_hierarchy = {'large_letter': 1, 'small_parcel': 2, 'medium_parcel': 3}
    max_format_val = 0
    cart_format = 'large_letter'
    
    for item in cart.items.select_related('product'):
        item_subtotal = item.subtotal()
        subtotal += item_subtotal
        total_weight += item.total_weight()
        
        fmt = item.product.shipping_format or 'small_parcel'
        fmt_val = format_hierarchy.get(fmt, 2)
        if fmt_val > max_format_val:
            max_format_val = fmt_val
            cart_format = fmt
        
        if destination_country_code == 'GB' and item.product.tax_class == 'standard':
            tax += item_subtotal * Decimal('0.20')
            
    shipping = Decimal('0.00')
    if cart.items.exists():
        if destination_country_code == 'GB':
            if cart_format == 'large_letter' and total_weight <= 750:
                shipping = Decimal('3.50')
            elif cart_format in ['large_letter', 'small_parcel'] and total_weight <= 2000:
                shipping = Decimal('5.00')
            else:
                shipping = Decimal('8.00')
        else:
            if cart_format == 'large_letter' and total_weight <= 750:
                shipping = Decimal('8.00')
            elif cart_format in ['large_letter', 'small_parcel'] and total_weight <= 2000:
                shipping = Decimal('15.00')
            else:
                shipping = Decimal('25.00')
                
    total = subtotal + tax + shipping
    
    return {
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'tax': tax.quantize(Decimal('0.01')),
        'shipping': shipping.quantize(Decimal('0.01')),
        'total': total.quantize(Decimal('0.01'))
    }

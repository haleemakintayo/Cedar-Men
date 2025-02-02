from django.shortcuts import render, get_object_or_404,redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from cart.models import CartItem
from cart.utils import get_cart
from ecommerce.models import Product, Color, Size

def cart_summary(request):
    """
    Render the cart summary page.
    """
    cart = get_cart(request)
    context = {'cart': cart}
    return render(request, 'cart.html', context)

@require_POST
def update_cart_item(request):
    """
    Update a cart item’s quantity.
    Expects POST data with:
      - 'item_id': ID of the CartItem to update
      - 'quantity': The new quantity
    """
    item_id = request.POST.get('item_id')
    quantity = request.POST.get('quantity')
    
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid quantity'}, status=400)
    
    cart_item = get_object_or_404(CartItem, id=item_id)
    if quantity <= 0:
        cart_item.delete()
        new_quantity = 0
        subtotal = 0
    else:
        cart_item.quantity = quantity
        cart_item.save()
        new_quantity = cart_item.quantity
        subtotal = float(cart_item.subtotal())
    
    cart = cart_item.cart
    return JsonResponse({
        'quantity': new_quantity,
        'subtotal': subtotal,
        'total': float(cart.total_price()),
    })

@require_POST
def remove_cart_item(request):
    """
    Remove a cart item.
    Expects POST data with 'item_id'.
    """
    item_id = request.POST.get('item_id')
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    cart = cart_item.cart
    return JsonResponse({
        'total': float(cart.total_price())
    })

@require_POST
def add_to_cart(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    cart = get_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    # Get the selected color and size from POST data.
    color_id = request.POST.get('color')  # expecting an ID (as string)
    size_id = request.POST.get('size')    # expecting an ID (as string)
    
    color = None
    size = None
    if color_id:
        try:
            color = Color.objects.get(id=color_id)
        except Color.DoesNotExist:
            color = None  # or handle the error as needed
    if size_id:
        try:
            size = Size.objects.get(id=size_id)
        except Size.DoesNotExist:
            size = None

    # Use color and size in the filter so that the same product with different options are distinct
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        color=color,
        size=size
    )
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    data = {
        'total_items': cart.total_items(),
        'total_price': float(cart.total_price()),
        # Optionally, return additional info about the item just added:
        'item': {
            'id': cart_item.id,
            'product': cart_item.product.name,
            'quantity': cart_item.quantity,
            'color': cart_item.color.name if cart_item.color else None,
            'size': cart_item.size.label if cart_item.size else None,
            'subtotal': float(cart_item.subtotal()),
        }
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(data)
    else:
        return redirect('cart_summary')

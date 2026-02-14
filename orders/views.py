from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from orders.models import Order, OrderItem
from cart.utils import get_cart  
from cart.models import CartItem
from django.conf import settings

def checkout(request):
    cart = get_cart(request)
    if cart.items.count() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('cart_summary')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postcode = request.POST.get('postcode')
        country = request.POST.get('country')


        total = cart.total_price()

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            city=city,
            state=state,
            postcode=postcode,
            country=country,
            total=total
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                color=item.color,
                size=item.size
            )
        cart.items.all().delete()
        messages.success(request, "Your order has been placed successfully!")
        return redirect('generate-invoice', order_id=order.id)
    else:
        context = {
            'cart': cart,
        }
        return render(request, 'checkout.html', context)



def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order
    }
    return render(request, 'order-confirmation.html', context)

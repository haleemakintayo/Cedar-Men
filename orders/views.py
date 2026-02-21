from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from orders.models import Order, OrderItem
from orders.payment_utils import finalize_order_payment
from cart.utils import get_cart
from ecommerce.models import Invoice

def _to_stripe_amount(amount: Decimal) -> int:
    return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _get_or_create_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _can_access_order(request, order):
    if order.user_id:
        return request.user.is_authenticated and request.user.id == order.user_id
    session_key = request.session.session_key
    if session_key and order.guest_session_key and session_key == order.guest_session_key:
        return True
    verified_orders = request.session.get('verified_order_numbers', [])
    return order.order_number in verified_orders


def _mark_order_verified(request, order_number):
    verified_orders = request.session.get('verified_order_numbers', [])
    if order_number not in verified_orders:
        verified_orders.append(order_number)
        request.session['verified_order_numbers'] = verified_orders[-20:]
        request.session.modified = True


def checkout(request):
    cart = get_cart(request)
    session_key = _get_or_create_session_key(request)
    cart_items = list(cart.items.select_related('product', 'color', 'size'))
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('cart_summary')

    if request.method == 'POST':
        if not settings.STRIPE_SECRET_KEY:
            messages.error(request, "Stripe is not configured. Please contact support.")
            return redirect('checkout')

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
            total=total,
            guest_session_key=session_key if not request.user.is_authenticated else None,
            status='pending',
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                color=item.color,
                size=item.size
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': _to_stripe_amount(item.product.price),
                },
                'quantity': item.quantity,
            })

        success_url = request.build_absolute_uri(reverse('stripe-checkout-success'))
        success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(reverse('stripe-checkout-cancel'))
        cancel_url = f"{cancel_url}?order_number={order.order_number}"

        try:
            session = stripe.checkout.Session.create(
                mode='payment',
                line_items=line_items,
                client_reference_id=order.order_number,
                metadata={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'user_id': str(request.user.id) if request.user.is_authenticated else '',
                },
                customer_email=email,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except stripe.error.StripeError:
            order.delete()
            messages.error(request, "Unable to initialize payment. Please try again.")
            return redirect('checkout')

        order.stripe_session_id = session.id
        order.stripe_payment_intent_id = session.payment_intent
        order.save(update_fields=['stripe_session_id', 'stripe_payment_intent_id'])

        return redirect(session.url)
    else:
        context = {
            'cart': cart,
        }
        return render(request, 'checkout.html', context)


def stripe_checkout_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, "Missing Stripe session.")
        return redirect('checkout')

    order = get_object_or_404(Order, stripe_session_id=session_id)
    if not _can_access_order(request, order):
        messages.error(request, "You are not authorized to view this order.")
        return redirect('checkout')

    if order.status != 'paid' and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.get('payment_status') == 'paid':
                finalize_order_payment(
                    order,
                    stripe_session_id=session.get('id'),
                    stripe_payment_intent_id=session.get('payment_intent'),
                )
                order.refresh_from_db(fields=['status'])
        except stripe.error.StripeError:
            pass

    if order.status != 'paid':
        messages.info(request, "Payment is processing. Please refresh in a moment.")

    return redirect('order_confirmation', order_number=order.order_number)


def stripe_checkout_cancel(request):
    order_number = request.GET.get('order_number')
    if order_number:
        order = Order.objects.filter(order_number=order_number).first()
        if order and _can_access_order(request, order) and order.status == 'pending':
            order.status = 'canceled'
            order.save(update_fields=['status'])
    messages.warning(request, "Payment was canceled. Your cart is still intact.")
    return redirect('checkout')


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _can_access_order(request, order):
        messages.error(request, "You are not authorized to view this order.")
        return redirect('checkout')

    invoice = Invoice.objects.filter(order=order).first()
    context = {
        'order': order,
        'invoice': invoice,
    }
    return render(request, 'order-confirmation.html', context)


def order_tracking(request):
    query = request.GET.get('q', '').strip()
    track_order_number = request.GET.get('order_number', '').strip().upper()
    track_email = request.GET.get('email', '').strip()
    tracked_order = None
    tracked_invoice = None

    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    else:
        session_key = _get_or_create_session_key(request)
        orders = Order.objects.filter(user__isnull=True, guest_session_key=session_key).order_by('-created_at')

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(status__icontains=query)
        )

    if track_order_number or track_email:
        if track_order_number and track_email:
            tracked_order = (
                Order.objects
                .filter(order_number__iexact=track_order_number, email__iexact=track_email)
                .prefetch_related('items__product', 'items__size', 'items__color')
                .first()
            )
            if tracked_order:
                _mark_order_verified(request, tracked_order.order_number)
                tracked_invoice = Invoice.objects.filter(order=tracked_order).first()
            else:
                messages.error(request, "No order found with that order number and email.")
        else:
            messages.error(request, "Enter both order number and email to track an order.")

    context = {
        'orders': orders,
        'query': query,
        'track_order_number': track_order_number,
        'track_email': track_email,
        'tracked_order': tracked_order,
        'tracked_invoice': tracked_invoice,
    }
    return render(request, 'order-tracking.html', context)

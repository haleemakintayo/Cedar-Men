from django.utils import timezone

from cart.models import Cart
from ecommerce.models import Invoice, InvoiceItem
from userauths.utils import generate_invoice_number


def finalize_order_payment(order, stripe_session_id=None, stripe_payment_intent_id=None):
    update_fields = []

    if order.status != 'paid':
        order.status = 'paid'
        update_fields.append('status')

    if stripe_session_id and order.stripe_session_id != stripe_session_id:
        order.stripe_session_id = stripe_session_id
        update_fields.append('stripe_session_id')

    if stripe_payment_intent_id and order.stripe_payment_intent_id != stripe_payment_intent_id:
        order.stripe_payment_intent_id = stripe_payment_intent_id
        update_fields.append('stripe_payment_intent_id')

    if not order.paid_at:
        order.paid_at = timezone.now()
        update_fields.append('paid_at')

    if update_fields:
        order.save(update_fields=update_fields)

    if order.user:
        invoice, _ = Invoice.objects.get_or_create(
            order=order,
            defaults={
                'invoice_number': generate_invoice_number(),
                'customer': order.user,
                'status': 'paid',
            },
        )

        if invoice.status != 'paid':
            invoice.status = 'paid'
            invoice.save(update_fields=['status'])

        # Ensure invoice items exist exactly once.
        if not invoice.invoiceitem_set.exists():
            for order_item in order.items.all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product_name=order_item.product.name,
                    quantity=order_item.quantity,
                    unit_price=order_item.price,
                )

        cart = Cart.objects.filter(user=order.user).first()
        if cart:
            cart.items.all().delete()
    elif order.guest_session_key:
        guest_cart = Cart.objects.filter(user__isnull=True, session_key=order.guest_session_key).first()
        if guest_cart:
            guest_cart.items.all().delete()


def mark_order_failed(order):
    if order and order.status != 'paid' and order.status != 'failed':
        order.status = 'failed'
        order.save(update_fields=['status'])

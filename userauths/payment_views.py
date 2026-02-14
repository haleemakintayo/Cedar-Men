import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from orders.payment_utils import finalize_order_payment, mark_order_failed


@csrf_exempt
def payment_webhook(request):
  payload = request.body
  sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
  if not settings.STRIPE_WEBHOOK_SECRET:
    return HttpResponse(status=400)

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
  except (ValueError, TypeError, stripe.error.SignatureVerificationError):
    return HttpResponse(status=400)

  event_type = event.get('type')
  data = event.get('data', {}).get('object', {})

  if event_type == 'checkout.session.completed':
    order_ref = (
      data.get('client_reference_id')
      or data.get('metadata', {}).get('order_number')
      or data.get('metadata', {}).get('order_id')
    )
    if not order_ref:
      return HttpResponse(status=200)

    order = Order.objects.filter(order_number=order_ref).select_related('user').prefetch_related('items').first()
    if not order and str(order_ref).isdigit():
      order = Order.objects.filter(id=int(order_ref)).select_related('user').prefetch_related('items').first()
    if not order:
      return HttpResponse(status=200)

    finalize_order_payment(
      order,
      stripe_session_id=data.get('id'),
      stripe_payment_intent_id=data.get('payment_intent'),
    )

  elif event_type in ('checkout.session.async_payment_failed', 'payment_intent.payment_failed'):
    order = None
    if event_type == 'payment_intent.payment_failed':
      payment_intent_id = data.get('id')
      if payment_intent_id:
        order = Order.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
    else:
      order_ref = (
        data.get('client_reference_id')
        or data.get('metadata', {}).get('order_number')
        or data.get('metadata', {}).get('order_id')
      )
      if order_ref:
        order = Order.objects.filter(order_number=order_ref).first()
        if not order and str(order_ref).isdigit():
          order = Order.objects.filter(id=int(order_ref)).first()

    mark_order_failed(order)

  return HttpResponse(status=200)

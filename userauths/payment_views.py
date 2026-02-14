from django.http import HttpResponse
from orders.models import Order
from .utils import generate_invoice_number
from ecommerce.models import Invoice, InvoiceItem

def payment_webhook(request):
  # Process the webhook data from your payment processor
  # ...

  if payment_succesful: 
    order_id = extract_order_id_from_webhook_data()
    order = Order.objects.get(id=order_id)

    # Create Invoice: 
    invoice = Invoice.objects.create(
      invoice_number=generate_invoice_number(),
      user=order.user,
      order=order,
      status = 'paid' # Set status to paid since payment is successful
    )

    # Create invoice items
    for order_item in order. orderitem_set.all():
      InvoiceItem.objects.create(
        invoice=invoice,
        product=order_item.product,
        quantity=order_item.quantity,
        unit_price=order_item.price
      )

    # Update order status
    order.status = 'paid'
    order.save()

  return HttpResponse(status=200)
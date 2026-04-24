"""
Celery async tasks for Royal Mail Click & Drop integration.
Triggers after successful payment to create shipments without blocking the main thread.
"""
import logging
from celery import shared_task
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_royal_mail_shipment(self, order_id):
    """
    Async task to create Royal Mail shipment after successful payment.
    
    This task is triggered after checkout completes successfully.
    It handles the entire shipping label generation process in the background.
    
    Args:
        order_id (int): The ID of the Order to process
        
    Returns:
        dict: Task result with status and details
    """
    from orders.models import Order
    from orders.services import (
        RoyalMailService,
        RoyalMailServiceException,
        RoyalMailBadRequestException,
        RoyalMailServiceUnavailableException,
    )
    from orders.validators import RoyalMailValidator
    
    try:
        # Fetch the order
        order = Order.objects.get(id=order_id)
        
        logger.info(f"Starting Royal Mail shipment creation for order {order.order_number}")
        
        # Step 1: Validate order data before API call
        try:
            validation_result = RoyalMailValidator.validate_order_for_shipping(order)
            if validation_result['warnings']:
                logger.warning(
                    f"Order {order.order_number} validation warnings: "
                    f"{validation_result['warnings']}"
                )
        except ValidationError as e:
            # Mark order as shipping failed
            order.shipping_status = 'failed'
            order.shipping_error_message = f"Validation error: {str(e)}"
            order.save(update_fields=['shipping_status', 'shipping_error_message'])
            
            logger.error(f"Order {order.order_number} failed validation: {e}")
            return {
                'status': 'failed',
                'order_id': order_id,
                'error': str(e),
            }
        
        # Step 2: Create Royal Mail service instance
        try:
            royal_mail_service = RoyalMailService()
        except RoyalMailServiceException as e:
            logger.error(f"Royal Mail service initialization failed: {e}")
            raise self.retry(exc=e)
        
        # Step 3: Create shipment via API
        try:
            shipment_result = royal_mail_service.create_shipment(order)
            
            logger.info(
                f"Shipment created for order {order.order_number}: "
                f"{shipment_result['shipping_reference']}"
            )
            
        except RoyalMailBadRequestException as e:
            # Bad request - don't retry, mark as failed
            order.shipping_status = 'failed'
            order.shipping_error_message = f"API validation error: {str(e)}"
            order.save(update_fields=['shipping_status', 'shipping_error_message'])
            
            logger.error(f"Royal Mail API rejected order {order.order_number}: {e}")
            return {
                'status': 'failed',
                'order_id': order_id,
                'error': f"API validation error: {str(e)}",
            }
            
        except RoyalMailServiceUnavailableException as e:
            # Service unavailable - retry with backoff
            logger.warning(f"Royal Mail service unavailable, scheduling retry: {e}")
            raise self.retry(exc=e)
            
        except RoyalMailServiceException as e:
            # Other service errors - retry
            logger.error(f"Royal Mail service error for order {order.order_number}: {e}")
            raise self.retry(exc=e)
        
        # Step 4: Update order with shipping details
        try:
            royal_mail_service.update_order_shipping(
                order=order,
                shipping_reference=shipment_result['shipping_reference'],
                label_base64=shipment_result['label_base64'],
            )
            
            logger.info(
                f"Successfully processed order {order.order_number}. "
                f"Label generated, status: {order.shipping_status}"
            )
            
            return {
                'status': 'success',
                'order_id': order_id,
                'order_number': order.order_number,
                'shipping_reference': shipment_result['shipping_reference'],
                'label_url': order.label_url,
            }
            
        except Exception as e:
            # Shipment created but failed to update order
            logger.critical(
                f"CRITICAL: Shipment created but order update failed for "
                f"{order.order_number}. Shipment ID: {shipment_result['shipping_reference']}. "
                f"Error: {e}"
            )
            # Still return success but with warning
            return {
                'status': 'partial_success',
                'order_id': order_id,
                'shipping_reference': shipment_result['shipping_reference'],
                'warning': f"Shipment created but order update failed: {str(e)}",
            }
    
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {
            'status': 'error',
            'order_id': order_id,
            'error': 'Order not found',
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error processing order {order_id}: {e}")
        return {
            'status': 'error',
            'order_id': order_id,
            'error': str(e),
        }


@shared_task
def cleanup_old_shipping_orders():
    """
    Periodic task to clean up old pending shipping orders.
    Runs daily at 2:00 AM to find and process stale shipping requests.
    
    Returns:
        dict: Cleanup results
    """
    from orders.models import Order
    from datetime import timedelta
    
    # Find orders stuck in 'pending' shipping status for more than 24 hours
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    stale_orders = Order.objects.filter(
        shipping_status='pending',
        paid_at__isnull=False,
        paid_at__lt=cutoff_time,
    )
    
    count = stale_orders.count()
    
    if count > 0:
        logger.warning(f"Found {count} stale shipping orders")
        
        # You could add notification logic here or auto-retry
        # For now, just log them for manual review
        for order in stale_orders:
            logger.info(
                f"Stale order: {order.order_number} - "
                f"Paid: {order.paid_at}, Status: {order.shipping_status}"
            )
    
    return {
        'status': 'completed',
        'stale_orders_found': count,
        'cleanup_time': timezone.now().isoformat(),
    }


@shared_task(bind=True, max_retries=5)
def retry_failed_shipment(self, order_id):
    """
    Manual retry task for failed shipments.
    Can be triggered from admin or API endpoint.
    
    Args:
        order_id (int): The ID of the Order to retry
        
    Returns:
        dict: Retry result
    """
    from orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        
        if order.shipping_status != 'failed':
            return {
                'status': 'skipped',
                'order_id': order_id,
                'message': f"Order status is '{order.shipping_status}', not failed",
            }
        
        # Reset status and clear previous error
        order.shipping_status = 'pending'
        order.shipping_error_message = None
        order.save(update_fields=['shipping_status', 'shipping_error_message'])
        
        # Trigger the main shipment task
        return create_royal_mail_shipment.delay(order_id)
        
    except Order.DoesNotExist:
        return {
            'status': 'error',
            'order_id': order_id,
            'error': 'Order not found',
        }
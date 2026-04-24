# Royal Mail Click & Drop Integration - Technical Documentation

> **Project:** Cedar-Men E-commerce Platform  
> **Date:** April 2026  
> **Django Version:** 5.0.1  
> **Status:** ✅ Complete

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Flow](#architecture-flow)
3. [Database Models](#database-models)
4. [API Service Layer](#api-service-layer)
5. [Validation Utilities](#validation-utilities)
6. [Celery Async Tasks](#celery-async-tasks)
7. [Payment Integration](#payment-integration)
8. [Configuration](#configuration)
9. [Running the System](#running-the-system)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

This integration adds **Royal Mail Click & Drop REST API** support to your existing Django e-commerce platform. The system automatically creates shipping labels after successful payment, processing everything asynchronously via Celery and Redis.

### Key Features

| Feature | Description |
|---------|-------------|
| **Auto Label Generation** | Labels created automatically after payment |
| **Async Processing** | Non-blocking via Celery - no delay to checkout |
| **Strict Validation** | Address/weight validation before API calls |
| **Base64 Label Decoding** | Converts Royal Mail response to PDF |
| **Error Handling** | Automatic retries with exponential backoff |
| **Status Tracking** | 6 shipping statuses tracked in database |

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORDER FLOW                                        │
└─────────────────────────────────────────────────────────────────────────────┘

1. CUSTOMER CHECKOUT
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │   Cart       │ ──► │   Checkout   │ ──► │   Stripe    │
   │   Selection  │     │   Form       │     │   Payment   │
   └──────────────┘     └──────────────┘     └──────────────┘
                                                      │
                                                      ▼
2. PAYMENT SUCCESS                                          ┌─────────────────────┐
   ┌─────────────────────┐                                  │  finalize_order_    │
   │  stripe_checkout_   │ ──► Calls ──►                   │  payment()          │
   │  success()         │     finalize_order_payment()     │                     │
   └─────────────────────┘                                  └─────────┬─────────┘
                                                                       │
                                                                       ▼
3. ASYNC TRIGGER                                          ┌─────────────────────┐
   ┌─────────────────────┐                                  │  Check if Royal     │
   │  Checks for         │ ◄──────────────────────────────── │  Mail API keys      │
   │  ROYAL_MAIL_API_URL │     settings.ROYAL_MAIL_API_URL  │  are configured     │
   └─────────┬───────────┘                                  └─────────┬─────────┘
             │                                                      │
             ▼                                                      ▼
   ┌─────────────────────┐                          ┌─────────────────────────┐
   │  create_royal_mail_ │                          │  If configured:        │
   │  shipment.delay()   │ ◄────────────────────── │  create_royal_mail_     │
   │  (non-blocking)     │     .delay(order.id)    │  shipment.delay(order.id)│
   └─────────────────────┘                          └─────────────────────────┘
             │
             ▼
4. CELERY WORKER PROCESSING
   ┌────────────────────────────────────────────────────────────────────────┐
   │                         CELERY WORKER                                  │
   │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
   │  │  Validate   │ ──► │  Call Royal  │ ──► │  Decode     │              │
   │  │  Order Data │    │  Mail API    │    │  Base64     │              │
   │  └──────────────┘    └──────────────┘    └──────────────┘              │
   │        │                   │                   │                       │
   │        ▼                   ▼                   ▼                       │
   │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
   │  │  Check      │    │  Create      │    │  Save PDF    │              │
   │  │  Address    │    │  Shipment    │    │  Label       │              │
   │  │  Limits     │    │  + Label     │    │  to Media    │              │
   │  └──────────────┘    └──────────────┘    └──────────────┘              │
   └────────────────────────────────────────────────────────────────────────┘
             │
             ▼
5. ORDER UPDATED
   ┌────────────────────────────────────────────────────────────────────────┐
   │                          DATABASE UPDATE                               │
   │  • shipping_reference = "RM123456789"                                 │
   │  • label_file = "shipping_labels/2026/04/24/ORD-20260424-ABC123.pdf" │
   │  • shipping_status = "label_generated"                                 │
   │  • shipping_created_at = 2026-04-24 12:34:56                          │
   └────────────────────────────────────────────────────────────────────────┘
```

---

## Database Models

### Order Model Enhancements

Located in: [`orders/models.py`](orders/models.py)

```python
class Order(models.Model):
    # ... existing fields ...
    
    # =========================================
    # Royal Mail Shipping Fields (NEW)
    # =========================================
    
    shipping_reference = models.CharField(
        max_length=100,
        blank=True, null=True,
        db_index=True,
        help_text="Unique reference returned by Royal Mail API"
    )
    
    label_url = models.URLField(
        blank=True, null=True,
        help_text="URL to the generated shipping label"
    )
    
    label_file = models.FileField(
        upload_to='shipping_labels/%Y/%m/%d/',
        blank=True, null=True,
        help_text="Stored PDF label from Royal Mail"
    )
    
    shipping_status = models.CharField(
        max_length=20,
        choices=SHIPPING_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current shipping status from Royal Mail"
    )
    
    shipping_created_at = models.DateTimeField(
        blank=True, null=True,
        help_text="When the shipping label was created"
    )
    
    shipping_error_message = models.TextField(
        blank=True, null=True,
        help_text="Error details if shipping creation failed"
    )
    
    # =========================================
    # Helper Method (NEW)
    # =========================================
    
    def get_total_weight_grams(self):
        """Calculate total weight of order items in grams."""
        total_weight = 0
        for item in self.items.all():
            product_weight = getattr(item.product, 'weight_grams', 500)
            total_weight += product_weight * item.quantity
        return total_weight or 500  # Default to 500g if empty
```

### Shipping Status Choices

| Status | Description |
|--------|-------------|
| `pending` | Awaiting shipment creation |
| `label_generated` | Label created, awaiting collection |
| `manifested` | Submitted to Royal Mail |
| `in_transit` | Package in transit |
| `delivered` | Successfully delivered |
| `failed` | Shipment creation failed |

---

## API Service Layer

Located in: [`orders/services.py`](orders/services.py)

### RoyalMailService Class

```python
class RoyalMailService:
    """
    Handles all interactions with Royal Mail Click & Drop REST API.
    """
    
    def create_shipment(self, order):
        """
        Create a shipment in Royal Mail and generate a label.
        
        Returns:
            dict: {
                'shipping_reference': str,
                'label_base64': str,
                'tracking_number': str
            }
        """
    
    def decode_and_save_label(self, order, label_base64):
        """
        Decode Base64 label from Royal Mail and save as PDF file.
        """
    
    def update_order_shipping(self, order, shipping_reference, label_base64):
        """
        Update order with shipping details after successful API call.
        """
    
    def handle_shipment_error(self, order, error_message):
        """
        Update order with error status and message.
        """
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `create_shipment()` | POST to Royal Mail API, returns shipment ID + Base64 label |
| `_build_shipment_payload()` | Formats order data to Royal Mail's strict schema |
| `_truncate_string()` | Ensures address fields stay within character limits |
| `decode_and_save_label()` | Converts Base64 → PDF, saves to `media/shipping_labels/` |
| `update_order_shipping()` | Updates Order model with shipping reference + status |
| `handle_shipment_error()` | Marks order as failed, stores error message |

### Error Handling

| Exception | HTTP Code | Handling |
|-----------|-----------|----------|
| `RoyalMailBadRequestException` | 400 | Don't retry - mark order as failed |
| `RoyalMailServiceUnavailableException` | 503 | Retry with backoff (max 3 times) |
| `RoyalMailServiceException` | Other | Retry with backoff |
| `RequestException` | Network | Retry with backoff |

---

## Validation Utilities

Located in: [`orders/validators.py`](orders/validators.py)

### RoyalMailValidator

```python
class RoyalMailValidator:
    """Validates order data against Royal Mail API requirements."""
    
    ADDRESS_LIMITS = {
        'line1': 35,    # Max 35 characters
        'line2': 35,    # Max 35 characters
        'line3': 30,    # Max 30 characters
        'postcode': 8,  # Max 8 characters
    }
    
    NAME_LIMIT = 30    # Max 30 characters
    
    MIN_WEIGHT_GRAMS = 1
    MAX_WEIGHT_GRAMS = 20000  # 20kg
```

### Validation Checks

| Check | Rule |
|-------|------|
| Recipient Name | Required, max 30 chars |
| Address Line 1 | Required, max 35 chars |
| City | Required, max 35 chars |
| State + Postcode | Combined max 30 chars |
| Postcode | Required, max 8 chars |
| Country | Required |
| Weight | 1g - 20kg (integer grams) |
| Order Items | At least 1 item required |

### Usage

```python
from orders.validators import RoyalMailValidator
from django.core.exceptions import ValidationError

try:
    validation_result = RoyalMailValidator.validate_order_for_shipping(order)
    if validation_result['valid']:
        # Proceed with API call
except ValidationError as e:
    # Handle validation failure
    print(e.message)  # "First name and last name are required"
```

---

## Celery Async Tasks

Located in: [`orders/tasks.py`](orders/tasks.py)

### Task Definitions

#### 1. `create_royal_mail_shipment`

**Main async task** - triggered after payment success.

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_royal_mail_shipment(self, order_id):
    """
    Async task to create Royal Mail shipment after successful payment.
    
    Flow:
    1. Fetch order from database
    2. Validate order data
    3. Create Royal Mail service instance
    4. Call Royal Mail API
    5. Decode Base64 label to PDF
    6. Save label to media/shipping_labels/
    7. Update order with shipping details
    
    Retry Behavior:
    - Max 3 retries
    - 60 second delay between retries
    - Exponential backoff on service unavailable
    """
```

#### 2. `cleanup_old_shipping_orders`

**Periodic task** - runs daily at 2:00 AM.

```python
@shared_task
def cleanup_old_shipping_orders():
    """
    Finds orders stuck in 'pending' shipping status for > 24 hours.
    Logs for manual review.
    """
```

#### 3. `retry_failed_shipment`

**Manual retry task** - for failed shipments.

```python
@shared_task(bind=True, max_retries=5)
def retry_failed_shipment(self, order_id):
    """
    Reset shipping status and retry shipment creation.
    Can be triggered from admin or API.
    """
```

---

## Payment Integration

Located in: [`orders/payment_utils.py`](orders/payment_utils.py)

### Trigger Point

```python
def finalize_order_payment(order, stripe_session_id=None, stripe_payment_intent_id=None):
    # ... existing payment logic ...
    
    # =============================================
    # Trigger Royal Mail async shipping task
    # =============================================
    if settings.ROYAL_MAIL_API_URL and settings.ROYAL_MAIL_API_KEY:
        try:
            from orders.tasks import create_royal_mail_shipment
            create_royal_mail_shipment.delay(order.id)  # Non-blocking!
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to queue Royal Mail task: {e}")
```

### Safety Features

- ✅ Only triggers if API credentials are configured
- ✅ Uses `.delay()` for non-blocking execution
- ✅ Wrapped in try/except - **won't fail checkout** if Celery is down
- ✅ Logs errors without interrupting payment flow

---

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# =============================================
# Redis Configuration
# =============================================
REDIS_URL=redis://localhost:6379/0

# =============================================
# Royal Mail API Configuration
# =============================================
ROYAL_MAIL_API_URL=https://api.royalmail.com/v1
ROYAL_MAIL_API_KEY=your_bearer_token_here
ROYAL_MAIL_REQUEST_TIMEOUT=30
```

### Django Settings

Located in: [`Cedarmen/settings.py`](Cedarmen/settings.py)

```python
# =============================================
# Royal Mail Click & Drop API Configuration
# =============================================
ROYAL_MAIL_API_URL = os.getenv('ROYAL_MAIL_API_URL', '')
ROYAL_MAIL_API_KEY = os.getenv('ROYAL_MAIL_API_KEY', '')
ROYAL_MAIL_REQUEST_TIMEOUT = int(os.getenv('ROYAL_MAIL_REQUEST_TIMEOUT', '30'))

# =============================================
# Celery Configuration with Redis Broker
# =============================================
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

CELERY_RESULT_EXPIRES = 60 * 60 * 24 * 7  # 7 days

CELERY_TASK_ROUTES = {
    'orders.tasks.create_royal_mail_shipment': {'queue': 'shipping'},
    'orders.tasks.retry_failed_shipment': {'queue': 'shipping'},
    'orders.tasks.cleanup_old_shipping_orders': {'queue': 'main'},
}

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### Celery App Configuration

Located in: [`Cedarmen/celery.py`](Cedarmen/celery.py)

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cedarmen.settings')

app = Celery('Cedarmen')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-old-shipping-orders': {
        'task': 'orders.tasks.cleanup_old_shipping_orders',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
}
```

---

## Running the System

### Prerequisites

Ensure these are installed:

```txt
# requirements.txt additions
celery==5.3.6
django-celery-beat==2.5.0
redis==6.4.0        # Already installed
requests==2.32.3   # Already installed
```

### Step 1: Database Migration

```bash
python manage.py migrate
```

Or apply the migration manually:

```bash
python manage.py makemigrations orders
python manage.py migrate orders
```

### Step 2: Start Redis

```bash
# Windows
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### Step 3: Start Celery Worker

```bash
# Basic worker
celery -A Cedarmen worker -l info

# With specific queue (recommended)
celery -A Cedarmen worker -l info -Q shipping

# With concurrency
celery -A Cedarmen worker -l info -Q shipping --concurrency=4
```

### Step 4: Start Celery Beat (Optional)

For periodic tasks (cleanup job):

```bash
celery -A Cedarmen beat -l info
```

### Step 5: Verify Setup

```bash
# Test Celery connectivity
celery -A Cedarmen inspect ping

# List active tasks
celery -A Cedarmen inspect active

# List scheduled tasks
celery -A Cedarmen inspect scheduled
```

---

## File Structure

```
Cedar-Men/
├── Cedarmen/
│   ├── __init__.py          # Added: Celery app import
│   ├── celery.py            # NEW: Celery configuration
│   └── settings.py          # UPDATED: Celery + Royal Mail config
│
├── orders/
│   ├── models.py            # UPDATED: Shipping fields
│   ├── services.py          # NEW: RoyalMailService
│   ├── validators.py        # NEW: Validation utilities
│   ├── tasks.py             # NEW: Celery async tasks
│   ├── payment_utils.py    # UPDATED: Task trigger
│   └── migrations/
│       └── 0002_add_royal_mail_shipping.py  # NEW: DB migration
│
├── media/
│   └── shipping_labels/    # NEW: Where labels are stored
│       └── %Y/%m/%d/       # Organized by date
│
└── .env                     # ADD: Royal Mail credentials
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'celery'` | Install: `pip install celery==5.3.6` |
| `ConnectionError: Cannot connect to Redis` | Start Redis: `redis-server` |
| `ROYAL_MAIL_API_KEY not set` | Add to `.env` file |
| `Task not executing` | Check worker: `celery -A Cedarmen inspect active` |
| `400 Bad Request` | Check address validation in admin |
| `503 Service Unavailable` | Royal Mail API down - task will auto-retry |

### Monitoring Commands

```bash
# View worker logs
celery -A Cedarmen worker -l info

# View task results in Django admin
# Navigate to: /admin/

# Check order shipping status
# In Django shell:
from orders.models import Order
order = Order.objects.get(order_number='ORD-20260424-ABC')
print(order.shipping_status)
print(order.shipping_reference)
print(order.label_file.url)
```

### Manual Retry

```python
# From Django shell
from orders.tasks import retry_failed_shipment
retry_failed_shipment.delay(order_id=1)
```

---

## API Reference

### Royal Mail Payload Schema

```json
{
  "recipient": {
    "name": "John Smith",
    "address": {
      "line1": "123 Main Street",
      "line2": "London",
      "line3": "Greater London SW1A 1AA",
      "postcode": "SW1A1AA",
      "country": "GB"
    }
  },
  "weight": {
    "value": 500,
    "unit": "grams"
  },
  "reference": "ORD-20260424-ABC123",
  "serviceCode": "ST1D"
}
```

### Response Schema

```json
{
  "shipmentId": "RM123456789",
  "label": "JVBERi0xLjQKJe...",
  "trackingNumber": "TRK123456789"
}
```

---

## Summary

| Component | File | Status |
|-----------|------|--------|
| Order Model | `orders/models.py` | ✅ Complete |
| API Service | `orders/services.py` | ✅ Complete |
| Validation | `orders/validators.py` | ✅ Complete |
| Celery Tasks | `orders/tasks.py` | ✅ Complete |
| Payment Trigger | `orders/payment_utils.py` | ✅ Complete |
| Celery Config | `Cedarmen/celery.py` | ✅ Complete |
| Django Settings | `Cedarmen/settings.py` | ✅ Complete |
| Database Migration | `orders/migrations/0002_*.py` | ✅ Complete |

---

> **Note:** This integration assumes you have a Royal Mail Click & Drop API account. Contact Royal Mail developer support to obtain your API credentials.
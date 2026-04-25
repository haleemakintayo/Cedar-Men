"""
Celery configuration for Cedarmen Django project.
Handles async task processing via Redis broker.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cedarmen.settings')

# Create the Celery app
app = Celery('Cedarmen')

# Load configuration from Django settings with namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f'Request: {self.request!r}')


# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-shipping-orders': {
        'task': 'orders.tasks.cleanup_old_shipping_orders',
        'schedule': crontab(hour=2, minute=0),  # Run at 2:00 AM daily
    },
}
# Celery configuration for async tasks
# This imports the Celery app when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
"""Celery tasks for Snob Group platform."""

from app.core.celery_app import celery_app

# Expose for: celery -A app.tasks worker
app = celery_app

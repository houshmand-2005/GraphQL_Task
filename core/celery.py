"""
Celery configuration.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
app = Celery("GraphQL_Task")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Task for debugging.
    """
    print(f"Request: {self.request!r}")

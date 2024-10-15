# your_app_name/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/email-status/$', consumers.EmailStatusConsumer.as_asgi()),
]
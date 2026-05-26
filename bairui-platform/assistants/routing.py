from django.urls import path

from .consumers import AgentStatusConsumer

websocket_urlpatterns = [
    path("ws/agent/status/", AgentStatusConsumer.as_asgi()),
]

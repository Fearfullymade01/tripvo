from django.urls import re_path
from . import consumers
from .chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/itinerary/(?P<plan_id>[^/]+)/$', consumers.ItineraryConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<plan_id>[^/]+)/$', ChatConsumer.as_asgi()),
]

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class ItineraryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.plan_id = self.scope['url_route']['kwargs']['plan_id']
        self.group_name = f'itinerary_{self.plan_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'add_item':
            await self.add_item(data)
        elif action == 'comment':
            await self.add_comment(data)
        # Add more actions as needed

    @sync_to_async
    def get_itinerary(self):
        from .models import ItineraryItem
        from .serializers import ItineraryItemSerializer
        items = ItineraryItem.objects.filter(plan_id=self.plan_id)
        return ItineraryItemSerializer(items, many=True).data

    async def add_item(self, data):
        # Implement item creation logic here
        # Broadcast new item to group
        itinerary = await self.get_itinerary()
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'itinerary_update',
                'itinerary': itinerary
            }
        )

    async def add_comment(self, data):
        # Implement comment creation logic here
        itinerary = await self.get_itinerary()
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'itinerary_update',
                'itinerary': itinerary
            }
        )

    async def itinerary_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'itinerary_update',
            'itinerary': event['itinerary']
        }))

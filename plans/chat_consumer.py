from channels.generic.websocket import AsyncWebsocketConsumer
import json
import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan_id = None
        self.room_group_name = None

    async def connect(self):
        self.plan_id = self.scope['url_route']['kwargs']['plan_id']
        self.room_group_name = f'chat_{self.plan_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def receive(self, text_data=None):
        data = json.loads(text_data)
        if data['type'] == 'message':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'user': data['user'],
                        'content': data['content'],
                        'timestamp': self.get_timestamp(),
                    }
                }
            )
        elif data['type'] == 'image':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'user': data['user'],
                        'content': data['content'],
                        'filename': data['filename'],
                        'timestamp': self.get_timestamp(),
                    }
                }
            )
        elif data['type'] == 'reaction':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'reaction_message',
                    'user': data['user'],
                    'msgIdx': data['msgIdx'],
                    'reaction': data['reaction'],
                }
            )
        elif data['type'] == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user': data['user']
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def reaction_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'user': event['user'],
            'msgIdx': event['msgIdx'],
            'reaction': event['reaction'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'users': [event['user']]
        }))

    def get_timestamp(self):
        return datetime.datetime.now().isoformat()


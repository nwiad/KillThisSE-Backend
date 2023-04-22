import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from user.models import User
from utils.utils_verify import *


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['userid']
                
        # Join room group
        await self.channel_layer.group_add(str(self.user_id), self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(str(self.user_id), self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        receiver_id = text_data_json["receiver"]
        message = text_data_json["message"]
        # Send message to room group
        await self.channel_layer.group_send(
            str(receiver_id), {"type": "chat_message", "message": message, "sender": self.user_id}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        print(event)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))
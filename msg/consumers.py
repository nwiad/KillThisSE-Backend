import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from user.models import User
from utils.utils_verify import *


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "HELLO"
        self.room_group_name = "chat_%s" % self.room_name
        
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # token = text_data_json["token"]
        # sender = async_get_user_by_token(token)
        # receiver_id = text_data_json["id"]
        # receiver = async_get_user_by_id(receiver_id)

        message = text_data_json["message"]
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        print(message)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))
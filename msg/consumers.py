import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from user.models import User
from msg.models import Conversation, Message
from utils.utils_verify import *


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        # Join room group
        await self.channel_layer.group_add(str(self.conversation_id), self.channel_name)
        await self.accept()


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(str(self.conversation_id), self.channel_name)


    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        token = text_data_json["token"]
        sender = await async_get_user_by_token(token)
        # Send message to room group
        await self.channel_layer.group_send(
            str(self.conversation_id), {"type": "chat_message", "message": message, "sender": sender.user_id}
        )


    # Receive message from room group
    async def chat_message(self, event):
        sender_id = event["sender"]
        message = event["message"]
        print(event)
        Message.objects.create(msg_body=message, conversation_id=self.id, sender_id=sender_id)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "messages": [
                
            ]
        }))

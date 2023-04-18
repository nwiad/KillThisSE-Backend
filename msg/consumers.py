import json
from channels.generic.websocket import AsyncWebsocketConsumer

from utils.utils_verify import async_get_user


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(self.scope)
        self.accept()

    async def disconnect(self, close_code):
        pass

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        token = text_data_json['message']['token']
        self.user = await async_get_user(token)
        

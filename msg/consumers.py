import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from user.models import User
from msg.models import Message
from utils.utils_verify import *


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        await self.channel_layer.group_add(str(self.conversation_id), self.channel_name)
        await self.channel_layer.group_send(str(self.conversation_id), {"type": "chat_message"})
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(str(self.conversation_id), self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        token = text_data_json["token"]
        heartbeat = text_data_json.get("heartbeat")
        image_url = text_data_json.get("image_url")  # 检查传入消息是否包含 image_url
        # Check_for_login
        if not token:
            # TODO: Add more info
            await self.disconnect()
        sender = await async_get_user_by_token(token)
        if not sender:
            # TODO: Add more info
            await self.disconnect()
        # Send message to current conversation
        if (heartbeat is None) or (heartbeat == False):
            await Message.objects.acreate(
                msg_body=message, 
                conversation_id=self.conversation_id, 
                sender_id=sender.user_id,
                image_url=image_url,  # 将 image_url 存储在 Message 对象中
                )
            await self.channel_layer.group_send(
                str(self.conversation_id), {"type": "chat_message"}
            )

    # Receive message
    async def chat_message(self, event):
        # 向该会话的所有用户发送聊天信息
        await self.send(text_data=json.dumps({
            "messages": [
                {
                    "conversation_id": self.conversation_id,
                    "msg_id": msg.msg_id,
                    "msg_body": msg.msg_body,
                    "sender_id": msg.sender_id,
                    "sender_name": (await User.objects.aget(user_id=msg.sender_id)).name,
                    "sender_avatar": (await User.objects.aget(user_id=msg.sender_id)).avatar,
                    "image_url": msg.image_url,  # 将 image_url 添加到消息中
                }
                async for msg in Message.objects.filter(conversation_id=self.conversation_id).all()
            ]
        }))

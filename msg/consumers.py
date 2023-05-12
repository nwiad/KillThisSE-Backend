import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from user.models import User
from msg.models import Message
from utils.utils_verify import *
import pytz


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
        is_image = text_data_json.get("is_image")  # 检查传入消息是否包含 image_url
        image_url = text_data_json.get("image_url")  # 检查传入消息是否包含 image_url
        is_file = text_data_json.get("is_file")  # 检查传入消息是否包含 image_url
        file_url = text_data_json.get("file_url")  # 检查传入消息是否包含 image_url
        
        withdraw_msg_id = text_data_json.get("withdraw_msg_id")  # 检查传入消息是否包含 withdraw
        quote_with = text_data_json.get("quote_with") if text_data_json.get("quote_with") is not None else -1 # 检查传入消息是否引用了其他消息
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
            if withdraw_msg_id:
                msg_to_withdraw = await Message.objects.aget(msg_id=withdraw_msg_id)
                msg_to_withdraw.is_withdraw = True  # 将消息标记为已撤回
                await msg_to_withdraw.save()
                await self.channel_layer.group_send(
                    str(self.conversation_id), {"type": "chat_message"}
                )
            else:  # 如果没有收到撤回消息的请求，则发送普通聊天消息
                await Message.objects.acreate(
                    msg_body=message, 
                    conversation_id=self.conversation_id, 
                    sender_id=sender.user_id,
                    image_url=image_url,
                    is_image=is_image,
                    is_file=is_file,
                    file_url=file_url,
                    quote_with=quote_with
                )
                await self.channel_layer.group_send(
                    str(self.conversation_id), {"type": "chat_message"}
                )

    # Receive message
    async def chat_message(self, event):
        messages = []
        async for msg in Message.objects.filter(conversation_id=self.conversation_id).all():
            if not msg.is_withdraw:  # 如果消息没有被撤回，则将其添加到消息列表中
                if msg.create_time is not None:
                    create_time = msg.create_time.astimezone(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    create_time = "N/A"  # or some other default value
                messages.append({
                    "conversation_id": self.conversation_id,
                    "msg_id": msg.msg_id,
                    "msg_body": msg.msg_body,
                    "sender_id": msg.sender_id,
                    "sender_name": (await User.objects.aget(user_id=msg.sender_id)).name,
                    "sender_avatar": (await User.objects.aget(user_id=msg.sender_id)).avatar,
                    "create_time": create_time,
                    "is_image": msg.is_image,
                    "image_url": msg.image_url,
                    "is_file": msg.is_file,
                    "file_url": msg.file_url,
                    "quote_with": msg.quote_with
                })
            else:  # 如果消息已经被撤回，则将其从数据库中删除
                await msg.delete()
        await self.send(text_data=json.dumps({"messages": messages}))

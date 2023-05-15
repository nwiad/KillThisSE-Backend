import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from user.models import User
from msg.models import Message, Conversation
from utils.utils_verify import *
import pytz
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.conversation = await Conversation.objects.aget(conversation_id=self.conversation_id)
        self.user = await User.objects.aget(user_id=self.user_id)
        await self.channel_layer.group_add(str(self.conversation_id), self.channel_name)
        await self.channel_layer.group_send(str(self.conversation_id), {"type": "chat_message"})
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(str(self.conversation_id), self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        @sync_to_async
        def withdraw_message(withdraw_msg_id):
            msg_to_withdraw = Message.objects.get(msg_id=withdraw_msg_id)
            msg_to_withdraw.is_withdraw = True
            msg_to_withdraw.msg_body = "[该消息已被撤回]"
            msg_to_withdraw.save()

        @sync_to_async
        def delete_msg(deleted_msg_id,sender):
            deleted_msg = Message.objects.get(msg_id=deleted_msg_id)            
            deleted_msg.delete_members.add(sender)
            deleted_msg.save()
        
        @sync_to_async
        def create_message():
            new_message = Message.objects.create(
                msg_body=message,
                conversation_id=self.conversation_id,
                sender_id=sender.user_id,
                image_url=image_url,
                is_image=is_image,
                is_video=is_video,
                is_file=is_file,
                is_audio=is_audio,
                video_url=video_url,
                file_url=file_url,
                quote_with=quote_with
            )
            for member_name in mentioned_members:
                if member_name is not None:
                    member = User.objects.filter(name=member_name)
                    new_message.mentioned_members.aadd(member)
                    self.conversation.mentioned_members.aadd(member)

            self.conversation.save()
            new_message.asave()
            return new_message
        
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        token = text_data_json["token"]
        heartbeat = text_data_json.get("heartbeat")
        is_image = text_data_json.get("is_image")  # 检查传入消息是否包含 image_url
        image_url = text_data_json.get("image_url")  # 检查传入消息是否包含 image_url
        is_video = text_data_json.get("is_video")
        video_url = text_data_json.get("video_url") 
        is_file = text_data_json.get("is_file")
        file_url = text_data_json.get("file_url")
        is_audio = text_data_json.get("is_audio")
        
        
        deleted_msg_id = text_data_json.get("deleted_msg_id")
        withdraw_msg_id = text_data_json.get("withdraw_msg_id")  # 检查传入消息是否包含 withdraw
        quote_with = text_data_json.get("quote_with") if text_data_json.get("quote_with") is not None else -1 # 检查传入消息是否引用了其他消息
        # 这条消息提到了谁 返回一个name的列表
        mentioned_members: list = text_data_json.get("mentioned_members")
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
                await withdraw_message(withdraw_msg_id)
                await self.channel_layer.group_send(
                    str(self.conversation_id), {"type": "chat_message"}
                )
            else :
                if deleted_msg_id:  # 如果是一个删除
                    await delete_msg(deleted_msg_id, sender)
                    await self.channel_layer.group_send(
                        str(self.conversation_id), {"type": "chat_message"}
                    )
                else:  # 如果不是一个删除操作 则发送普通聊天消息
                    await create_message()
                    await self.channel_layer.group_send(
                        str(self.conversation_id), {"type": "chat_message"}
                    )

    # Receive message
    async def chat_message(self, event):
        @sync_to_async
        def del_message():        
            return [one.user_id for one in msg.delete_members.all()]
        
        @sync_to_async
        def get_mentioned_groups():
            """
            获取被mentioned的群聊
            """
            conversations = Conversation.objects.filter(is_Private=False, mentioned_members__in=[self.user]).all()
            conversation_ids = [conversation.conversation_id for conversation in conversations]
            return conversation_ids

            
        messages = []
        mentioned_groups = await get_mentioned_groups()
        
        
        # 将获取会话成员的同步操作包装为异步函数
        @sync_to_async
        def get_members(conversation_id):
            cov = Conversation.objects.filter(conversation_id=conversation_id).first()
            members = []
            for member in cov.members.all():
                if member.user_id != nowpeople.user_id:
                    members.append({
                        "user_id": member.user_id,
                        "user_name": member.name,
                        "user_avatar": member.avatar
                    })
            return members
        
        
        messages = []
        members = []
            
        nowpeople = self.user
        
        async for msg in Message.objects.filter(conversation_id=self.conversation_id).all():
            if msg.create_time is not None:
                create_time = msg.create_time.astimezone(pytz.timezone('Asia/Shanghai')).strftime("%m-%d %H:%M")
            else:
                create_time = "N/A"  # or some other default value
        
            deletemsgusers = await del_message()
            # 给前端传递的消息列表
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
                "is_audio": msg.is_audio,
                "is_video": msg.is_video,
                "quote_with": msg.quote_with,
                "delete_members": deletemsgusers,
                "mentioned_members": [member.user_id async for member in msg.mentioned_members.all()]
            })
        
        # 获取本会话的所有成员
        members = await get_members(self.conversation_id)
        await self.send(text_data=json.dumps({"messages": messages, "members": members, "mentioned": mentioned_groups}))

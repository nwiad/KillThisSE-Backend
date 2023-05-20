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
        @sync_to_async
        def get_user():
            user = User.objects.filter(user_id=self.user_id).first()
            return user
        
        @sync_to_async
        def get_conversation():
            conversation = Conversation.objects.filter(conversation_id=self.conversation_id).first()
            return conversation

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.conversation = await get_conversation()
        self.user = await get_user()
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
                quote_with=quote_with,
                is_transmit=is_transmit,
            )
            
            if mentioned_members is not None:
                for member_name in mentioned_members:
                    member = User.objects.filter(name=member_name).first()
                    new_message.mentioned_members.add(member)
                    self.conversation.mentioned_members.add(member)
            
            if is_transmit:
                for msg_id in transmit_with_id:
                    msg = Message.objects.filter(msg_id=msg_id).first()
                    new_message.transmit_with.add(msg)
                    # print("加一个转发的消息++++++++=" + str(msg_id))

            self.conversation.save()
            new_message.save()
            return new_message
        
        @sync_to_async
        def set_quote_info():
            if quote_with != -1:
                quoted_msg = Message.objects.get(msg_id=quote_with)
                quoted_msg.quoted_num += 1
                quoted_msg.save()
                
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
        
        # 检查传入消息是否引用了其他消息 quote_with是被回复的消息的id
        quote_with = text_data_json.get("quote_with") if text_data_json.get("quote_with") is not None else -1 
        # print("quote!!!!\n\n\n\n")
        # print(quote_with)
        await set_quote_info()
        # @ 这条消息提到了谁 返回一个name的列表
        mentioned_members: list = text_data_json.get("mentioned_members")
        # 转发消息
        is_transmit = False
        if(text_data_json.get("forward")):
            is_transmit = text_data_json.get("forward") # 检查传入消息是否是多条转发消息
        transmit_with_id = text_data_json.get("message") # 检查传入消息包含的转发的消息的id

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
        
        # 将序列化包装成异步函数
        @sync_to_async
        def async_serialize(msg: Message):
            return msg.serialize()
        
        @sync_to_async
        def get_last_msg():
            last_msg = Message.objects.filter(conversation_id=self.conversation_id).order_by("-create_time").first()
            return last_msg
        
        @sync_to_async
        def get_conversation(user_id):
            """
            获取这个用户目前的所有会话
            """
            conversations = Conversation.objects.filter(members__in=[user_id]).all()
            # 满足disabled=False的会话
            conversations = conversations.filter(disabled=False).all()
            conv = []
            for conversation in conversations:
                if conversation.is_Private:
                    # Private chat
                    # member的成员是User, 应当用members里面的User对象的user_id和我的user_id比较
                    other_member = conversation.members.exclude(user_id=user_id).first()
                    name = other_member.name if other_member else "Unknown User"
                else:
                    # Group chat
                    name = conversation.conversation_name
                
                conv.append({
                    'id': conversation.conversation_id,
                    'name': name,
                    'avatar': conversation.conversation_avatar,
                    'is_group': not conversation.is_Private,
                })

            return conv

        @sync_to_async
        def get_unread_messages():
            conversation_id = self.conversation_id
            user = self.user
            msg_list = Message.objects.filter(conversation_id=conversation_id).all()
            unread_msg_list = [msg for msg in msg_list if (user not in msg.read_members.all() and user.user_id != msg.sender_id)]
            return len(unread_msg_list)
        
        @sync_to_async
        def check_mentioned():
            user = self.user
            conversation = self.conversation
            return user in conversation.mentioned_members.all()
        
        messages = []
        members = []
        nowpeople = self.user
        
        async for msg in Message.objects.filter(conversation_id=self.conversation_id).order_by("create_time")[:1000]:
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
                "quoted_num": msg.quoted_num,
                "delete_members": deletemsgusers,
                "chosen": False,
                "mentioned_members": [
                    member.user_id async for member in msg.mentioned_members.all()
                ],
                "is_transmit": msg.is_transmit,
                "transmit_with": [
                    await async_serialize(m_msg) async for m_msg in msg.transmit_with.all()
                ],
            })
        
        # 获取本会话的所有其他成员
        members = await get_members(self.conversation_id)
        # 最后一条消息
        last_msg = await get_last_msg()
        if last_msg:
            last_msg_info = await async_serialize(last_msg)
        else:
            last_msg_info = {}

        conv = await get_conversation(nowpeople.user_id)
        # 给前端发送的消息
        await self.send(text_data=json.dumps({"messages": messages, 
                                              "members": members, 
                                              # "mentioned": mentioned_groups,
                                              "conversations": conv,
                                              "last_msg": last_msg_info,
                                              "len_of_msgs": len(messages),
                                              "unread_msgs": await get_unread_messages(),
                                              "mentioned": await check_mentioned()
                                              }))

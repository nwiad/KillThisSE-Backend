from django.db import models

import datetime, pytz

from user.models import User
from utils.utils_time import *
from utils.utils_constant import MAX_CHAR_LENGTH

class Conversation(models.Model):
    # 全局唯一的会话标志符
    conversation_id = models.BigAutoField(primary_key=True)
    # 会话名称
    conversation_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    # 会话头像
    conversation_avatar = models.CharField(max_length=MAX_CHAR_LENGTH, default="https://github.com/LTNSXD/LTNSXD.github.io/blob/main/img/favicon.jpg?raw=true")
    # 创建时间
    create_time = models.DateTimeField(default=datetime.datetime.now)
    # 更新时间
    update_time = models.DateTimeField(default=datetime.datetime.now)
    # 私聊标志
    is_Private = models.BooleanField(default=True)
    # 成员列表
    members = models.ManyToManyField(User, related_name="conversation_members")
    # 群主
    owner = models.IntegerField(default=-1)
    # 管理员
    administrators = models.ManyToManyField(User, related_name="group_conversation_administrators")
    # 是否弃用
    disabled = models.BooleanField(default=False)
    # 群公告
    announcement = models.CharField(max_length=MAX_CHAR_LENGTH)
    # 置顶的成员列表
    sticky_members = models.ManyToManyField(User, related_name="sticky_members")
    # 免打扰的成员列表
    silent_members = models.ManyToManyField(User, related_name="silent_members")


class Message(models.Model):
    # 全局唯一的消息标志符
    msg_id = models.BigAutoField(primary_key=True)
    # 消息内容
    msg_body = models.CharField(max_length=MAX_CHAR_LENGTH)
    # 全局唯一的会话标志符
    conversation_id = models.IntegerField()
    # 消息发送方用户标志符
    sender_id = models.IntegerField()
    # 消息创建时间
    create_time = models.DateTimeField(default=datetime.datetime.now)
    # 消息是否被撤回
    is_withdraw = models.BooleanField(default=False)
    # 是否是图片消息
    is_image = models.BooleanField(default=False, null=True)
    # 图片url
    image_url = models.CharField(max_length=MAX_CHAR_LENGTH, default=None, null=True)
    # 是否是视频消息
    is_video = models.BooleanField(default=False, null=True)
    # 视频url
    video_url = models.CharField(max_length=MAX_CHAR_LENGTH, default=None, null=True)
    # 是否是文件消息
    is_file = models.BooleanField(default=False, null=True)
    # 是否是音频消息
    is_audio = models.BooleanField(default=False, null=True)
    # 文件url
    file_url = models.CharField(max_length=MAX_CHAR_LENGTH, default=None, null=True)
    # 是否引用其他消息
    quote_with = models.IntegerField(default=-1)
    # 已读成员列表
    read_members = models.ManyToManyField(User, related_name="read_members")
    # 删除该消息的成员列表
    delete_members = models.ManyToManyField(User, related_name="delete_members")

    def serialize(self):
        return {
            "conversation_id": self.conversation_id,
            "msg_id": self.msg_id,
            "msg_body": self.msg_body,
            "sender_id": self.sender_id,
            "sender_name": User.objects.get(user_id=self.sender_id).name,
            "sender_avatar": User.objects.get(user_id=self.sender_id).avatar,
            "create_time": self.create_time.astimezone(pytz.timezone('Asia/Shanghai')).strftime("%m-%d %H:%M"),
            "is_image": self.is_image,
            "image_url": self.image_url,
            "is_file": self.is_file,
            "file_url": self.file_url,
            "is_audio": self.is_audio,
            "is_video": self.is_video,
            "quote_with": self.quote_with
        }

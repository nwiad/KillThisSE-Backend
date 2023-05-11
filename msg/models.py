from django.db import models

import datetime

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
    # 图片url
    image_url = models.CharField(max_length=MAX_CHAR_LENGTH, default=None, null=True)

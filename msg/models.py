from django.db import models

import datetime

from utils.utils_time import *
from utils.utils_constant import MAX_CHAR_LENGTH

class Conversation(models.Model):
    # 全局唯一的会话标志符
    conversation_id = models.BigAutoField(primary_key=True)
    # 会话名称
    conversation_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    # 创建时间
    create_time = models.DateTimeField(default=datetime.datetime.now)
    # 更新时间
    update_time = models.DateTimeField(default=datetime.datetime.now)


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

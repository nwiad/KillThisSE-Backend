from django.db import models

import datetime

from utils.utils_time import *
from utils.utils_constant import MAX_CHAR_LENGTH

class Conversation(models.Model):
    conversation_id = models.BigAutoField(primary_key=True)
    conversation_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    create_time = models.DateTimeField(default=datetime.datetime.now)
    update_time = models.DateTimeField(default=datetime.datetime.now)


class Message(models.Model):
    msg_id = models.BigAutoField(primary_key=True)
    msg_body = models.CharField(max_length=MAX_CHAR_LENGTH)
    


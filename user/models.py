from django.db import models

import datetime
from utils.utils_require import MAX_CHAR_LENGTH

class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    register_time = models.DateTimeField(default=datetime.datetime.now)
    login_time = models.DateTimeField(default=datetime.datetime.now)

    def serialize(self):
        return {
            "user_id": self.user_id, 
            "name": self.name, 
            "register_time": self.register_time,
        }

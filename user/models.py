from django.db import models

from utils import utils_time
from utils.utils_require import MAX_CHAR_LENGTH

class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    register_time = models.FloatField(default=utils_time.get_timestamp)
    login_time = models.FloatField(default=utils_time.get_timestamp)

    def serialize(self):
        return {
            "user_id": self.user_id, 
            "name": self.name, 
            "register_time": self.register_time,
        }
    
    def __str__(self):
        return self.name

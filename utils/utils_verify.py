import json

from django.http import HttpRequest
from user.models import User
from rest_framework.authtoken.models import Token
from asgiref.sync import sync_to_async

from utils.utils_request import *

def get_user(req: HttpRequest):
    body = json.loads(req.body)
    token = body.get("token")
    record = Token.objects.filter(token=token).first()
    if record is None:
        return None
    else:
        return record.user
    

@sync_to_async
def async_get_user(token: str):
    record = Token.objects.filter(token=token).first()
    if record is None:
        return None
    else:
        return record.user


def verify_user(user:User):
    return Token.objects.filter(user=user).first() is not None

import json

from django.http import HttpRequest
from user.models import User
from rest_framework.authtoken.models import Token
from asgiref.sync import sync_to_async

from utils.utils_request import *

def get_user(req: HttpRequest):
    """
    :param req:HttpRequest
    """
    body = json.loads(req.body.decode("utf-8"))
    token = body.get("token")
    record = Token.objects.filter(key=token).first()
    if record is None:
        return None
    else:
        return record.user
    

@sync_to_async
def async_get_user_by_token(token: str):
    record = Token.objects.filter(key=token).first()
    if record is None:
        return None
    else:
        return record.user
    

@sync_to_async
def async_get_user_by_id(id: int):
    user = User.objects.filter(user_id=id).first()
    return user


def verify_user(user:User):
    return Token.objects.filter(user=user).first() is not None

import json
import datetime
import pytz
from django.http import HttpRequest
from IMBackend.settings import TIME_ZONE

from user.models import User, SessionPool

def get_session_id(req: HttpRequest):

    return req.COOKIES.get('session')


def bind_session_id(sessionId: str, user_id: int):
    SessionPool.objects.create(sessionId=sessionId, user_id=user_id)


def disable_session_id(sessionId: str):
    record = SessionPool.objects.filter(sessionId=sessionId)
    record.delete()
        

def verify_session_id(sessionId):
    sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
    if sessionRecord:
        if sessionRecord.expireAt < datetime.datetime.now(pytz.timezone(TIME_ZONE)):
            SessionPool.objects.get(sessionId=sessionId).delete()
            return None
        else:
            user = User.objects.filter(user_id=sessionRecord.user_id).first()
            return user
    else:
        return None
    
def verify_user(user_id):
    sessionRecord = SessionPool.objects.filter(user_id=user_id).first()
    return sessionRecord

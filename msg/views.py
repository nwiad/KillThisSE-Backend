import json
from django.http import HttpRequest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from utils.utils_request import request_failed, request_success
from utils.utils_require import CheckLogin, return_field
from utils.utils_verify import get_user
import base64
from msg.models import Conversation, Message
from user.models import User
import requests
import hashlib
import time
import uuid

def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size-10:size]

def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest() 

class MsgViewSet(viewsets.ViewSet):
    """
    消息相关内容
    """
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_read_members(self, req: HttpRequest):
        """
        获取某条消息的已读列表
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        msg_id = body.get("message")
        msg = Message.objects.filter(msg_id=msg_id).first()
        # TODO: to make it safier
        if not msg:
            return request_failed(2, "Message you search does not exist")
        
        member_list = [return_field(member.serialize(), ["user_id", "name", "avatar"]) for member in msg.read_members.all()]

        return_data = {
            "read_members": member_list, 
            "members_num": len(member_list)
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def add_read_member(self, req: HttpRequest):
        pass
       
       
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def withdraw_msg(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        msg_id = body.get("msg")
        msg = Message.objects.filter(msg_id=msg_id).first()
        msg.is_withdraw = True
        msg.save()
        print("Message is withdraw: ")
        return request_success()
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def delete_msg_by_one(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        msg_id = body.get("msg")
        user_id = body.get("user")
        msg = Message.objects.filter(msg_id=msg_id).first()
        user = User.objects.filter(user_id=user_id).first()
        msg.delete_members.add(user)
        msg.save()
        print("Message is deleted by you successfully")
        return request_success()
    
    
    def youdao_api_proxy(req):
        audio_file_path = "http://killthisse-avatar.oss-cn-beijing.aliyuncs.com/1684060999727recording.wav"
        lang_type = 'zh-CHS'
        q = base64.b64encode(audio_file_path.encode('utf-8')).decode('utf-8')
        data = {}
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
        sign = encrypt(signStr)
        data['appKey'] = APP_KEY
        data['q'] = q
        data['salt'] = salt
        data['sign'] = sign
        data['signType'] = "v2"
        data['langType'] = lang_type
        data['rate'] = 16000
        data['format'] = 'wav'
        data['channel'] = 1
        data['type'] = 1
        YOUDAO_URL = 'https://openapi.youdao.com/asrapi'
        APP_KEY = '3c60ebd01606a5ca'
        APP_SECRET = 'RpS8mnChMx9pILX2TyhK69iyCPqnibrV'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(YOUDAO_URL, data=data, headers=headers)

        # 将响应的 JSON 转发回前端
        return response.json()
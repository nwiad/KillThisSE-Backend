import json
from django.http import HttpRequest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from utils.utils_request import request_failed, request_success
from utils.utils_require import CheckLogin, return_field
from utils.utils_verify import get_user

from msg.models import Conversation, Message

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
    def add_read_members(self, req: HttpRequest):
        pass

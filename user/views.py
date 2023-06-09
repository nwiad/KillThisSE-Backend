import json
from django.http import HttpRequest
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token

from user.models import User, Friendship, FriendshipRequest, Group, GroupFriend, GroupInvitation
from msg.models import Conversation, Message
from utils.utils_request import request_failed, request_success, return_field
from utils.utils_require import CheckLogin, require
from utils.utils_valid import name_valid, name_exist, password_valid, email_valid
from utils.utils_verify import get_user, verify_user
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
import random
import time
import TLSSigAPIv2

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models

api = TLSSigAPIv2.TLSSigAPIv2(1400811921, "d03af2f895d19f0f4f5fb180b3d79e9a8e6ae29e70a0553f5d8f0dd92d9bb693")

# 检查用户输入的验证码是否和之前发送的一致
def check_code(user, code):
    # 如果code的类型是string 转为数字
    if type(code) == str:
        code = int(code)
    if user.user_code == code:
        return True
    else:
        return False

class UserViewSet(viewsets.ViewSet):
# region 注册、注销相关功能
    @action(detail=False, methods=["POST"])
    # 不用邮箱注册
    def register_without_email(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        password = require(body, "password", "string", err_msg="Missing or error type of [password]")

        if not name_valid(name):
            return request_failed(1, "用户名不合法")
        elif name_exist(name):
            return request_failed(2, "用户名已经存在")    
        elif not password_valid(password):
            return request_failed(3, "密码不合法")        
        else: # Successful Create
            user = User(name=name)
            user.set_password(password)
            user.save()
        return request_success({"Created": True})
               
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def cancel_account(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        token = body.get("token")
        user = get_user(req)
        Token.objects.filter(key=token).delete()
        user.disabled = True
        user.save()
        return request_success({"Deleted": True})
# endregion

# region 登录、登出相关功能
    @action(detail=False, methods=["POST"])
    def auto_login(self, req: HttpRequest):
        """
        已经弃用
        """
        if get_user(req):
            return request_success({"Logged in": True})
        else:
            return request_failed(1, "Not logged in yet")
               
    @action(detail=False, methods=["POST"])
    def login(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        name = body.get('name')
        password = body.get('password')

        if not name_valid(name):
            return request_failed(1, "用户名不合法")
        user = name_exist(name)
        if not user:
            return request_failed(2, "用户不存在")
        if not user.check_password(password):
            return request_failed(3, "用户名或密码错误")
        if user.disabled:
            return request_failed(2, "用户不存在")
        if verify_user(user):
            Token.objects.filter(user=user).delete()
        
        # Successful login
        token = Token.objects.update_or_create(user=user)
        token = Token.objects.get(user=user).key
        return request_success({"Logged in": True, "Token": token})
   
    # 登录时 发送验证码
    @action(detail=False, methods=["POST"])
    def send_email_for_login(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        
        # 基本信息格式校验
        email = body.get('email')
        user = User.objects.filter(user_email=email).first()
        if not user:
            return request_failed(2, "该邮箱没有绑定任何用户！")
        # 生成六位数字验证码
        code = random.randint(100000, 999999)
               
        send_mail(
            'Verification Code --from SE2023 IM',
            'You are try to login SE2023 IM.\nYour login verification code is: ' + str(code)+'\nIf you did not try to login, please ignore this email.\n\n--from KillthisSE2023 Team',
            '15935695163@163.com',
            [email])
        
        user.user_code = code
        user.user_code_created_time = time.time()
        
        user.save()
        return request_success({"send": True, "code_send": code})
      
    @action(detail=False, methods=["POST"])
    def login_with_email(self, req: HttpRequest):
        # 只有邮箱和验证码
        body = json.loads(req.body.decode("utf-8"))
        email = body.get('email')
        user = User.objects.filter(user_email = email).first()
        if not user:
            return request_failed(2, "用户不存在")
        if user.disabled:
            return request_failed(2, "用户不存在")
        
        if(check_code(user, body.get('code_input'))):
            if time.time() - user.user_code_created_time > 120: # 验证码有效期2分钟
                return request_failed(6, "验证码已过期，请重新发送")
            if verify_user(user):
                Token.objects.filter(user=user).delete()
            # Successful login
            token = Token.objects.update_or_create(user=user)
            token = Token.objects.get(user=user).key
            user.user_code = 0
            user.save()
            return request_success({"Logged in": True, "Token": token})
        else:
            # 发一次验证码只能输入一次，输入错误就要重新发送验证码
            user.user_code = 0
            user.save()
            return request_failed(5, "验证码错误")
              
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def logout(self, req: HttpRequest):
        body = json.loads(req.body)
        token = body.get("token")
        Token.objects.filter(key=token).delete()
        return request_success({'Logged out': True})
# endregion

# region 修改个人信息相关功能        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_name(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        new_name = body.get('name')

        if not name_valid(new_name):
            return request_failed(2, "用户名不合法")
        elif name_exist(new_name):
            return request_failed(3, "用户名已经存在")
        else:
            user.name = new_name

        user.save()
        return request_success({"Modified": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_email(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        pwd = body.get("password")
        new_email = body.get("email")
        if not user.check_password(pwd):
            return request_failed(2, "密码错误")
        user.user_email = new_email
        user.save()
        return request_success({"Reset": True})
           
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_password(self, req: HttpRequest):
        # 新的格式正确性校验
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        old_password = body.get('old_pwd')

        # 旧的密码正确性校验
        if not user.check_password(old_password):
            return request_failed(2, "旧密码错误")
        else:
            new_password = body.get('new_pwd')
            user.password = make_password(new_password)
            user.save()
            return request_success({"Modified": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_avatar(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        new_avatar = body.get('avatar')

        user.avatar = new_avatar
        
        user.save()
        return request_success({"Modified": True})
# endregion

# region 加好友相关功能
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_friend_requests(self, req: HttpRequest):
        user = get_user(req)

        request_list = FriendshipRequest.objects.filter(friend_user_id=user.user_id)
        friend_id_list = [request.user_id for request in request_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]
        
        return_data = {
            "requests": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def send_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()
        if not friend:
            return request_failed(2, "搜索目标不存在")
        
        if isFriend(user, friend):
            return request_failed(3, "你们已经是好友啦！")
        
        if requestExists(user, friend):
            return request_failed(4, "请求已经存在，请耐心等待")
        elif requestExists(friend, user): 
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends successfully": True})
        
        if friend.disabled == True:
            return request_failed(5, "对方已经注销了ToT")
        
        sendFriendRequest(user, friend)
        return request_success({"Send request": True})
 
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def respond_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()
        if not friend:
            return request_failed(1, "用户不存在")
        
        if not requestExists(friend, user):
            return request_failed(2, "好友请求不存在")
        response = body.get('response')

        if response == "accept":
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends": True})
        elif response == "reject":
            requestExists(friend, user).delete()
            return request_success({"Become Friends": False})
        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def del_friend(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_id).first()

        if not friend:
            return request_failed(2, "用户不存在")
        
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).first()
        if not friendship:
            return request_failed(3, "Ta不是你的朋友T_T")
        
        Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).delete()
        Friendship.objects.filter(user_id=friend_id, friend_user_id=user.user_id).delete()
        conversation = Conversation.objects.filter(members__in=[user], is_Private=True).filter(members__in=[friend]).first()
        if conversation:
            conversation.disabled = True
            conversation.save()
        return request_success({"Deleted": True})

# endregion
           
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_profile(self, req: HttpRequest):
        user = get_user(req)

        sig = api.gen_sig(str(user.user_id))

        return_data = {
            "user_id": user.user_id,
            "name": user.name,
            "avatar": user.avatar,
            "email": user.user_email,
            "conversation_len": len(Conversation.objects.all()),
            "sig": sig
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_avatar(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        name = body.get("name")
        target = User.objects.filter(name=name).first()
        if not target:
            return request_failed(2, "目标用户不存在")
        return request_success({"avatar": target.avatar})

# region 搜好友相关功能    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_by_id(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()

        if not friend:
            return request_failed(2, "查找用户不存在")
        
        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_by_name(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        friend_name = body.get('friend_name')
        friend = User.objects.filter(name=friend_name).first()

        if not friend:
            return request_failed(2, "查找用户不存在")
        
        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_friends(self, req: HttpRequest):
        user = get_user(req)
        friendship_list = Friendship.objects.filter(user_id=user.user_id)
        friend_id_list = [friendship.friend_user_id for friendship in friendship_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]

        return_data = {
            "friends": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_friend_by_id(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get('friend_id')

        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(2, "查找用户不存在")
        else:
            friend = User.objects.filter(user_id=friend_id).first()

        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])

        return request_success(return_data)
       
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_friend_by_name(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_name = body.get('friend_name')

        friend = User.objects.filter(name=friend_name).first()
        if not friend:
            return request_failed(2, "查找用户不存在")
        
        friend_id = friend.user_id
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(2, "查找用户不存在")

        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])

        return request_success(return_data)
# endregion

# region 分组相关功能
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 创建分组
    def create_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_name = body.get('name')
        group = Group.objects.filter(group_name=group_name).first()
        if group:
            return request_failed(2, "分组已经存在！")
        
        new_group = Group.objects.create(group_name=group_name, admin_id=user.user_id) #admin是拥有这个群组的人
        new_group.save()
        new_group_id = new_group.group_id
        # 返回group_id
        return request_success({"group_id": new_group_id})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 删除分组
    def del_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_name = body.get('name')
        group = Group.objects.filter(group_name=group_name).first()
        if not group:
            return request_failed(2, "分组不存在")
        if group.admin_id != user.user_id:
            return request_failed(3, "你并不是分组的管理者O_o")
        
        Group.objects.filter(group_id=group.group_id).delete()
        return request_success({"Deleted": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 获取分组
    def get_group(self, req: HttpRequest):
        user = get_user(req)
        group_list = Group.objects.filter(admin_id=user.user_id)
        return_data = {
            "groups": [
                return_field(group.serialize(), ["group_id", "group_name", "admin_id"])
            for group in group_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 获取某组内的好友
    def get_group_friends(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        group = Group.objects.filter(group_id=group_id).first()
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")
        
        # 返回这个组内的所有好友
        group_friend_list = GroupFriend.objects.filter(group_id=group_id)
        friend_id_list = [group_friend.user_id for group_friend in group_friend_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]

        return_data = {
            "friends": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 添加好友到分组
    def add_friend_to_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        friend_id = body.get('friend_id')
        group = Group.objects.filter(group_id=group_id).first()
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")
        
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(4, "你们并不是好友T_T")
        
        group_friend = GroupFriend.objects.filter(group_id=group_id, user_id=friend_id)
        if group_friend:
            return request_failed(5, "Ta已经在这个分组里了")
        
        new_group_friend = GroupFriend.objects.create(group_id=group_id, user_id=friend_id)
        new_group_friend.save()
        return request_success({"Added": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 从分组中删除好友
    def del_friend_from_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        friend_id = body.get('friend_id')
        group = Group.objects.filter(group_id=group_id).first()
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(4, "你们并不是好友T_T")
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")        
        group_friend = GroupFriend.objects.filter(group_id=group_id, user_id=friend_id)
        if not group_friend:
            return request_failed(5, "Friend not in this group")
        
        GroupFriend.objects.filter(group_id=group_id, user_id=friend_id).delete()
        return request_success({"Deleted": True})
# endregion
   
# region 聊天相关功能
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_friend_by_conversation(self, req: HttpRequest):
        """
        通过（私聊）会话id获取对方信息
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=True).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if user not in conversation.members.all():
            return request_failed(3, "You are not in this conversation")
        friend = conversation.members.all().exclude(user_id=user.user_id).first()
        return_data = {
            "friend": friend.serialize(),
            "user": user.serialize()
        }
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_private_conversations(self, req: HttpRequest):
        """
        获取用户所有的私聊（不包括置顶的）
        """
        user = get_user(req)
        private_conversation_list = Conversation.objects.filter(members__in=[user], is_Private=True).exclude(sticky_members__in=[user])
        members = []
        r_member_list = [x.members.all() for x in private_conversation_list]
        for member_list in r_member_list:
            members += member_list
        copied_members = members[:]
        for member in members[:]:
            if member.user_id == user.user_id:
                members.remove(member)
        return_data = {
            "conversations": [ 
                {
                    "id": conversation.conversation_id,
                    "friend_id": friend.user_id,
                    "friend_name": friend.name,
                    "friend_avatar": friend.avatar,
                    "is_Private": conversation.is_Private,
                    "silent": user in conversation.silent_members.all(),
                    "sticked": False,
                    "disabled": conversation.disabled,
                    "validation": user in conversation.valid_members.all()
                }
                for conversation, friend in zip(private_conversation_list, members)
            ]
        }
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_or_create_private_conversation(self, req: HttpRequest):
        """
        用户获取或创建与某一用户的私聊
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get("friend")
        friend = User.objects.filter(user_id=friend_id).first()
        if not friend:
            return request_failed(2, "Friend does not exist")
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).first()
        if not friendship:
            return request_failed(3, "You are not friends")
        # Successful get
        if Conversation.objects.filter(members__in=[user], is_Private=True).filter(members__in=[friend]).first():
            conversation = Conversation.objects.filter(members__in=[user], is_Private=True).filter(members__in=[friend]).first()
            if conversation.disabled:
                conversation.disabled = False
            conversation.save()
            return request_success({"conversation_id": conversation.conversation_id, "silent": user in conversation.silent_members.all()})
        # Successful create
        conversation = Conversation.objects.create(is_Private=True)
        conversation.save()
        conversation.members.add(user, friend)
        return request_success({"conversation_id": conversation.conversation_id, "silent": user in conversation.silent_members.all()})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_conversations(self, req: HttpRequest):
        """
        用户获取所有群聊（不包括置顶的）
        """
        user = get_user(req)
        group_conversation_list = Conversation.objects.filter(members__in=[user], is_Private=False).exclude(sticky_members__in=[user])
        # To be modified
        return_data = {
            "conversations": [ 
                {
                    "id": conversation.conversation_id,
                    "name": conversation.conversation_name,
                    "avatar": conversation.conversation_avatar,
                    "is_Private": conversation.is_Private,
                    "silent": user in conversation.silent_members.all(),
                    "sticked": False,
                    "disabled": conversation.disabled,
                    "validation": user in conversation.valid_members.all()
                }
                for conversation in group_conversation_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def create_group_conversation(self, req: HttpRequest):
        """
        用户创建新的群聊
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        # To be modified
        members: list = body.get("members")
        name = body.get("name")
        # To be modified
        for member_id in members:
            member = User.objects.filter(user_id=member_id).first()
            if not member:
                return request_failed(2, "member not exist")
            friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=member_id).first()
            if not friendship:
                return request_failed(3, f"{member.name} is not your friend")
        
        # Successful create
        conversation = Conversation.objects.create(conversation_name=name, is_Private=False, owner=user.user_id)
        conversation.save()
        conversation.members.add(user)
        for member_id in members:
            member = User.objects.filter(user_id=member_id).first()
            conversation.members.add(member)

        return request_success({"conversation_id": conversation.conversation_id})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def admin_invite_member(self, req: HttpRequest):
        """
        管理员直接邀请用户进入群聊
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        invitee_ids: list = body.get("invitee")
        invitees = [User.objects.filter(user_id=invitee_id).first() for invitee_id in invitee_ids]
        if (user not in group_conversation.administrators.all()) and (user.user_id != group_conversation.owner):
            return request_failed(5, "Permission denied")
        for invitee in invitees:
            if not invitee:
                return request_failed(3, "The user you tried to invite does not exist")
            if invitee in group_conversation.members.all():
                return request_failed(4, "User is already in the group")
        # Successful invite
        for invitee in invitees:
            group_conversation.members.add(invitee)
        return request_success({"Invited": True})
        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def invite_member_to_group(self, req: HttpRequest):
        """
        用户邀请新用户进入群聊（需要得到群主/管理员的同意）
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        invitee_ids: list = body.get("invitee")
        invitees = [User.objects.filter(user_id=invitee_id).first() for invitee_id in invitee_ids]
        for invitee in invitees:
            if not invitee:
                return request_failed(3, "The user you tried to invite does not exist")
            if invitee in group_conversation.members.all():
                return request_failed(4, "User is already in the group")
        # Successful invite
        for invitee_id in invitee_ids:
            if GroupInvitation.objects.filter(invitee_id=invitee_id, group_id=group_id).first() is None:
                # 不重复创建邀请
                invitation = GroupInvitation.objects.create(inviter_id=user.user_id, invitee_id=invitee_id, group_id=group_id)
                invitation.save()
        return request_success({"Invited": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_invitations(self, req: HttpRequest):
        """
        获取所有群聊邀请
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        invitations = GroupInvitation.objects.filter(group_id=group_id)
        invitee_ids = [invitation.invitee_id for invitation in invitations]
        invitees = [User.objects.filter(user_id=invitee_id).first() for invitee_id in invitee_ids]
        inviter_ids = [invitation.inviter_id for invitation in invitations]
        inviters = [User.objects.filter(user_id=inviter_id).first() for inviter_id in inviter_ids]
        return_data = {
            "invitations": [
                {
                    "invitation_id": invitation.invitation_id,
                    "inviter_id": inviter.user_id,
                    "inviter_name": inviter.name,
                    "inviter_avatar": inviter.avatar,
                    "invitee_id": invitee.user_id,
                    "invitee_name": invitee.name,
                    "invitee_avatar": invitee.avatar
                }
                for invitee, inviter, invitation in zip(invitees, inviters, invitations)
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def respond_group_invitation(self, req: HttpRequest):
        """
        （群主/管理员）回应进群邀请
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "group does not exist")
        if (not user in group_conversation.administrators.all()) and (not user.user_id == group_conversation.owner):
            return request_failed(3, "Permission denied")
        invitation_id = body.get("invitation")
        invitation = GroupInvitation.objects.filter(invitation_id=invitation_id).first()
        if not invitation:
            return request_failed(4, "Invitation does not exist")
        response = body.get("response")
        if response == "accept":
            member_id = invitation.invitee_id
            member = User.objects.filter(user_id=member_id).first()
            group_conversation.members.add(member)
            group_conversation.save()
        elif response == "reject":
            pass

        invitation.delete()
        return request_success({"Responded": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def dismiss_group_conversation(self, req: HttpRequest):
        """
        用户解散群聊
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group not exist")
        if group_conversation.owner != user.user_id:
            return request_failed(3, "You are not the owner of this group")
        group_conversation.disabled = True
        group_conversation.save()
        return request_success({"Dismissed": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def leave_group_conversation(self, req: HttpRequest):
        """
        用户退出群聊
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group not exist")
        if user not in group_conversation.members.all():
            return request_failed(3, "You are not in the group")
        if user.user_id == group_conversation.owner:
            return request_failed(4, "Owner cannot leave the group")
        group_conversation.members.remove(user)
        if user in group_conversation.administrators.all():
            group_conversation.administrators.remove(user)
        if user in group_conversation.sticky_members.all():
            group_conversation.sticky_members.remove(user)
        if user in group_conversation.valid_members.all():
            group_conversation.valid_members.remove(user)
        group_conversation.save()
        return request_success({"Left": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def set_validation(self, req: HttpRequest):
        """
        为聊天增加/解除二次验证
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if not user in conversation.members.all():
            return request_failed(3, "You are not in this conversation")
        valid: str = body.get("valid")
        if valid == "True":
            conversation.valid_members.add(user)
        elif user in conversation.valid_members.all():
            conversation.valid_members.remove(user)
        return request_success({"Modified": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def secondary_validate(self, req: HttpRequest):
        """
        二次验证
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        password = body.get("password")
        if user.check_password(password):
            return request_success({"Valid": True})
        else:
            return request_failed(2, "密码错误")

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def remove_member_from_group(self, req: HttpRequest):
        """
        （群主/管理员）将成员移出群聊
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("group")
        member_ids: list = body.get("members")
        group_conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group not exist")
        if (not user.user_id == group_conversation.owner) and (not user in group_conversation.administrators.all()):
            return request_failed(3, "Permission denied")
        for member_id in member_ids:
            member = User.objects.filter(user_id=member_id).first()
            if not member:
                return request_failed(5, "用户不存在")
            if (not user.user_id == group_conversation.owner) and member in group_conversation.administrators.all():
                return request_failed(3, "Permission denied")
            if member not in group_conversation.members.all():
                return request_failed(4, f"{member.name} is not in the group")
            group_conversation.members.remove(member)
            # 撤销管理员身份
            if member in group_conversation.administrators.all():
                group_conversation.administrators.remove(member)
            # 删除置顶关系
            if member in group_conversation.sticky_members.all():
                group_conversation.sticky_members.remove(member)
            # 删除免打扰关系
            if member in group_conversation.silent_members.all():
                group_conversation.silent_members.remove(member)
        group_conversation.save()
        return request_success({"Removed": True})
        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def transfer_owner(self, req: HttpRequest):
        """
        转让群主
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("group")
        new_owner = body.get("owner")
        group_conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group not exist")
        if group_conversation.owner != user.user_id:
            return request_failed(3, "You are not the owner of this group")
        # successful transfer
        group_conversation.owner = new_owner
        group_conversation.save()
        return request_success({"transfered": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def add_administrators(self, req: HttpRequest):
        """
        增加群聊管理员
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("group")
        administrators: list = body.get("admins")
        group_conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group not exist")
        if group_conversation.owner != user.user_id:
            return request_failed(3, "You are not the owner of this group")
        # successful add
        # TODO: make it robust
        for admin_id in administrators:
            admin = User.objects.filter(user_id=admin_id).first()
            group_conversation.administrators.add(admin)

        group_conversation.save()
        return request_success({"Added": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def remove_administrator(self, req: HttpRequest):
        """
        删除群管理员
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("group")
        admin_ids: list = body.get("admin")
        group_conversation = Conversation.objects.filter(conversation_id=conversation_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group not exist")
        if group_conversation.owner != user.user_id:
            return request_failed(3, "You are not the owner of this group")
        for admin_id in admin_ids:
            admin = User.objects.filter(user_id=admin_id).first()
            if not admin:
                return request_failed(4, "User not exist")
            if admin not in group_conversation.administrators.all():
                return request_failed(5, "The user is not an admin")
            # Successful remove
            group_conversation.administrators.remove(admin)
        group_conversation.save()
        return request_success({"Removed": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def set_group_announcement(self, req: HttpRequest):
        """
        群主或管理员设置群公告
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        announcement: str = body.get("announcement")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        if (not user.user_id == group_conversation.owner) and (not user in group_conversation.administrators.all()):
            return request_failed(3, "Permission denied")
        group_conversation.announcement = announcement
        group_conversation.save()
        return request_success({"Set": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_announcement(self, req: HttpRequest):
        """
        获取群公告
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        if not user in group_conversation.members.all():
            return request_failed(3, "You are not in this group")
        return_data = {"Announcement": group_conversation.announcement}
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_owner(self, req: HttpRequest):
        """
        获取群聊的群主
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        if not user in group_conversation.members.all():
            return request_failed(3, "You are not in this group")
        owner_id = group_conversation.owner
        owner = User.objects.filter(user_id=owner_id).first()
        return_data = {
            "owner": {
                "id": owner.user_id,
                "name": owner.name,
                "avatar": owner.avatar
            }
        }
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_administrators(self, req: HttpRequest):
        """
        获取群聊的所有管理员
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        if not user in group_conversation.members.all():
            return request_failed(3, "You are not in this group")
        admins = group_conversation.administrators.all()
        return_data = {
            "administrators": [
                {
                    "id": admin.user_id,
                    "name": admin.name,
                    "avatar": admin.avatar,
                }
                for admin in admins
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_members(self, req: HttpRequest):
        """
        获取群聊的成员信息（不包括群主和管理员）
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        if not user in group_conversation.members.all():
            return request_failed(3, "You are not in this group")
        members = list(group_conversation.members.all())
        # 不返回群主和管理员
        for member in members[:]:
            if (member.user_id == group_conversation.owner) or (member in group_conversation.administrators.all()):
                members.remove(member)

        return_data = {
            "members": [
                {
                    "id": member.user_id,
                    "name": member.name,
                    "avatar": member.avatar,
                }
                for member in members
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_group_members_id(self, req: HttpRequest):
        """
        获取群聊所有成员的id列表
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_failed(2, "Group does not exist")
        if not user in group_conversation.members.all():
            return request_failed(3, "You are not in this group")
        members = group_conversation.members.all()
        return_data = [member.user_id for member in members]
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_member_status(self, req: HttpRequest):
        """
        获取用户在群聊的身份
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get("group")
        group_conversation = Conversation.objects.filter(conversation_id=group_id, is_Private=False).first()
        if not group_conversation:
            return request_success({"Not a group": True})
            # return request_failed(2, "Group does not exist")
        if not user in group_conversation.members.all():
            return request_failed(3, "You are not in this group")
        member_id = body.get("member")
        member = User.objects.filter(user_id=member_id).first()
        if not member:
            return request_failed(4, "Member does not exist")
        return_data = {
            "is_admin": member in group_conversation.administrators.all(),
            "is_owner": member_id == group_conversation.owner
        }
        return request_success(return_data)
        
        

    # endregion

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def set_sticky_conversation(self, req: HttpRequest):
        """
        设置/取消置顶聊天
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        sticky: str = body.get("sticky")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if user not in conversation.members.all():
            return request_failed(3, "You are not in this group")
        if sticky == "True":
            conversation.sticky_members.add(user)
        elif user in conversation.sticky_members.all():
            conversation.sticky_members.remove(user)
        return request_success({"Revised": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_sticky_private_conversations(self, req: HttpRequest):
        """
        获取所有的置顶私聊
        """
        user = get_user(req)
        private_conversation_list = Conversation.objects.filter(members__in=[user], sticky_members__in=[user], is_Private=True)
        r_member_list = [x.members.all() for x in private_conversation_list]
        members = []
        for member_list in r_member_list:
            members += member_list

        for member in members[:]:
            if member.user_id == user.user_id:
                members.remove(member)
        
        return_data = {
            "conversations": [ 
                {
                    "id": conversation.conversation_id,
                    "friend_id": friend.user_id,
                    "friend_name": friend.name,
                    "friend_avatar": friend.avatar,
                    "is_Private": conversation.is_Private,
                    "silent": user in conversation.silent_members.all(),
                    "sticked": True,
                    "disabled": conversation.disabled,
                    "validation": user in conversation.valid_members.all()
                }
                for conversation, friend in zip(private_conversation_list, members)
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_sticky_group_conversations(self, req: HttpRequest):
        """
        获取所有的置顶群聊
        """
        user = get_user(req)
        group_conversation_list = Conversation.objects.filter(members__in=[user], sticky_members__in=[user], is_Private=False)
        return_data = {
            "conversations": [ 
                {
                    "id": conversation.conversation_id,
                    "name": conversation.conversation_name,
                    "avatar": conversation.conversation_avatar,
                    "is_Private": conversation.is_Private,
                    "silent": user in conversation.silent_members.all(),
                    "sticked": True,
                    "disabled": conversation.disabled,
                    "validation": user in conversation.valid_members.all()
                }
                for conversation in group_conversation_list
            ]
        }
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_unread_messages(self, req: HttpRequest):
        """
        用户获取某一聊天的未读消息数，目前已经弃用
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        msg_list = Message.objects.filter(conversation_id=conversation_id).all()
        unread_msg_list = [msg for msg in msg_list if (user not in msg.read_members.all() and user.user_id != msg.sender_id)]
        return request_success(
            {
                "UnreadMessages": len(unread_msg_list),
            }
        )

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def set_read_message(self, req: HttpRequest):
        """
        设置已读的位置
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        # 在两次的之间 获取谁读了这个消息  修改msg里面的信息
        msg_id = body.get("msg_id")
        if msg_id == -1:
            return request_success({"Message List Empty": True})
        msg_list = Message.objects.filter(conversation_id=conversation_id, msg_id__lte=msg_id)
        if msg_list.first() is None:
            return request_failed(3, "Message does not exist")
        # 标记为已读
        for msg in msg_list:          
            msg.read_members.add(user)
        msg.save()
                        
        # 消除被mention的标记
        if user in conversation.mentioned_members.all():
            conversation.mentioned_members.remove(user)
        return request_success({"Set Read Messages": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def set_silent_conversation(self, req: HttpRequest):
        """
        设置/取消聊天免打扰
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        silent: str = body.get("silent")
        if silent == "True":
            conversation.silent_members.add(user)
        elif user in conversation.silent_members.all():
            conversation.silent_members.remove(user)
        return request_success({"Modified": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def query_all_records(self, req: HttpRequest):
        """
        查询所有的聊天记录
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if user not in conversation.members.all():
            return request_failed(3, "User is not in this conversation")
        msg_list = Message.objects.filter(conversation_id=conversation_id).all()
        return_data = {
            "messages": [
                msg.serialize() for msg in msg_list
            ]
        }
        return request_success(return_data)        


    @action(detail=False, methods=["POST"])
    @CheckLogin
    def query_forward_records(self, req: HttpRequest):
        """
        根据消息id查询转发过来的聊天记录  根据消息id
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        msgid_list = body.get("msgidlist")
        if not msgid_list:
            return request_failed(1, "Message id list is empty")
        
        msg_list = Message.objects.filter(msg_id__in=msgid_list).all()
        return_data = {
            "messages": [
                msg.serialize() for msg in msg_list
            ]
        }
        return request_success(return_data)   

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def query_by_sender(self, req: HttpRequest):
        """
        根据发送者查询聊天记录
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if user not in conversation.members.all():
            return request_failed(3, "User is not in this conversation")
        sender_id = body.get("sender")
        msg_list = Message.objects.filter(conversation_id=conversation_id, sender_id=sender_id).all()
        return_data = {
            "messages": [
                msg.serialize() for msg in msg_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def query_by_content(self, req: HttpRequest):
        """
        根据内容查询聊天记录
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if user not in conversation.members.all():
            return request_failed(3, "User is not in this conversation")
        content = body.get("content")
        msg_list = Message.objects.filter(conversation_id=conversation_id, msg_body__contains=content).all()
        return_data = {
            "messages": [
                msg.serialize() for msg in msg_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def query_by_type(self, req: HttpRequest):
        """
        根据类型查询聊天记录 
        """
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        conversation_id = body.get("conversation")
        conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conversation:
            return request_failed(2, "Conversation does not exist")
        if user not in conversation.members.all():
            return request_failed(3, "User is not in this conversation")
        msg_type: str = body.get("type")
        if msg_type == "image":
            msg_list = Message.objects.filter(conversation_id=conversation_id, is_image=True).all()
        elif msg_type == "video":
            msg_list = Message.objects.filter(conversation_id=conversation_id, is_video=True).all()
        elif msg_type == "file":
            msg_list = Message.objects.filter(conversation_id=conversation_id, is_file=True).all()
        elif msg_type == "audio":
            msg_list = Message.objects.filter(conversation_id=conversation_id, is_audio=True).all()
        else:
            return request_failed(4, "Unknown type of message")
        return_data = {
            "messages": [
                msg.serialize() for msg in msg_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_sig(self, req: HttpRequest):
        """
        获取用户sig
        """
        user = get_user(req)
        user_id = user.user_id
        sig = api.gen_sig(user_id)
        print(sig)
        return request_success({"sig": sig})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_mentioned_members(self, req: HttpRequest):
        '''
        获取已读被@的成员
        '''
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        msgid = body.get("msg_id")
        msg = Message.objects.filter(msg_id=msgid).first()
        mention_members = []
        for member in msg.mentioned_members.all():
            mention_members.append({"name": member.name, "read": member in msg.read_members.all(), "avatar": member.avatar})
        return request_success({"mentioned_members": mention_members})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_read_members(self, req: HttpRequest):
        '''
        获取已读本条消息的成员
        '''
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        msgid = body.get("msg_id")
        msg = Message.objects.filter(msg_id=msgid).first()
        read_members = []
        for member in msg.read_members.all():
            read_members.append({"name": member.name, "avatar": member.avatar})
        return request_success({"read_members": read_members})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def voice2text(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        url = body.get("url")
        try:
            cred = credential.Credential("AKIDlQwHRMdmaFhx01d2C6nGSO5VgbIkwsXy", "GIqB9vUr1yhBSUFkyCnAHAsNdeS2Rksl")
            client = asr_client.AsrClient(cred, "")

            # 实例化一个请求对象,每个接口都会对应一个request对象
            req = models.CreateRecTaskRequest()
            params = {
                "EngineModelType": "16k_zh-PY",
                "ChannelNum": 1,
                "ResTextFormat": 0,
                "SourceType": 0,
                "Url": url
            }
            req.from_json_string(json.dumps(params))

            # 返回的resp是一个CreateRecTaskResponse的实例，与请求对象对应
            resp = client.CreateRecTask(req)

            TaskId = resp.Data.TaskId

            req1 = models.DescribeTaskStatusRequest()
            params = {
                "TaskId": TaskId
            }
            req1.from_json_string(json.dumps(params))

            startTime = time.time()
            while True:
                resp1 = client.DescribeTaskStatus(req1)

                if resp1.Data.StatusStr == "success":
                    break
                else:
                    pass
                time.sleep(1)
                endtime = time.time()
                if endtime - startTime > 6:
                    return request_success({"Result": "[获取结果超时]"})
            resp1 = client.DescribeTaskStatus(req1)
            splited = resp1.Data.Result.split()
            if len(splited) >= 2:
                result = splited[1]
            else:
                result = "[Ta似乎什么都没说]"
            return request_success({"Result": result})

        except TencentCloudSDKException as err:
            return request_success({"Result": "[莫名原因失败了]"})

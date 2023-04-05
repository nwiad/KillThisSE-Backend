import json
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.hashers import make_password, check_password

from rest_framework import viewsets
from rest_framework.decorators import action

from user.models import User, Friendship, FriendshipRequest
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, CheckLogin, require
from utils.utils_valid import *
from utils.utils_time import get_timestamp
from utils.utils_sessions import *
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest

def check_for_user_data(body):
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    return name, password

class UserViewSet(viewsets.ViewSet):
    @CheckRequire
    @action(detail=False, methods=["POST"])
    def register(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        name, password = check_for_user_data(body)
        m_password = make_password(password)

        if not name_valid(name):
            return request_failed(1, "Illegal username")
        elif name_exist(name):
            return request_failed(2, "Username already exists")    
        elif not password_valid(password):
            return request_failed(3, "Illegal password")        
        else: # Successful Create
            user = User(name=name, password=m_password)
            user.save()
            bind_session_id(get_session_id(req), user)

        return request_success({"Created": True})
        
    @CheckRequire
    @action(detail=False, methods=["POST"])
    def cancel_account(self, req: HttpRequest):
        user = verify_session_id(req)
        if not user:
            return request_failed(1, "Not logged in")

        user.delete()
        
    @CheckRequire
    @action(detail=False, methods=["POST"])
    def login(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        if verify_session_id(get_session_id(req)):
            return request_failed(4, "Already logged in")

        name, password = check_for_user_data(body)

        if name_valid(name):
            user = name_exist(name)
            if user and user.name == name:
                if check_password(password, user.password): # Password in database is encrypted
                    # Successful Login
                    bind_session_id(get_session_id(req), user)
                    return request_success({"Logged in": True})
                else:
                    return request_failed(3, "Wrong password")
            else:
                return request_failed(2, "User does not exist")
        else:
            return request_failed(1, "Illegal username")
            
    @CheckRequire
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def logout(self, req: HttpRequest):
        disable_session_id(get_session_id(req))
        return request_success({'Logged out': True})

        
    @CheckRequire
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def modify(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))
        new_name = body.get('name')
        new_password = body.get('password')
        new_avatar = body.get('avatar')

        if new_name:
            if not name_valid(new_name):
                return request_failed(1, "Illegal username")
            elif name_exist(new_name):
                return request_failed(2, "Username already exists")
            else:
                user.name = new_name
        
        if new_password:
            if not password_valid(new_password):
                return request_failed(3, "Illegal password")
            else :
                user.password = new_password

        if new_avatar:
            user.avatar = new_avatar

        user.save()
        return request_success({"Modified": True})
    
    
    @CheckRequire
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def send_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()
        if not friend:
            return request_failed(1, "Friend not exist")
        
        if isFriend(user, friend):
            return request_failed(2, "Already become friends")
        
        if requestExists(user, friend):
            return request_failed(3, "Request already exists")
        elif requestExists(friend, user): 
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends": True})
        
        sendFriendRequest(user, friend)
        return request_success({"Send request": True})

    
    @CheckRequire
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def respond_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id)
        if not friend:
            return request_failed(1, "Friend not exist")
        
        response = body.get('response')

        if response == "accept":
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends": True})
        elif response == "reject":
            requestExists(friend, user).delete()
            return request_success({"Become Friends": False})
    

    @CheckRequire
    @action(detail=False, methods=["GET"])
    def users(self, req: HttpRequest):
        users = User.objects.all().order_by('register_time')
        return_data = {
            "users": [
                return_field(user.serialize(), ["user_id", "name", "register_time"]) 
            for user in users],
        }
        return request_success(return_data)
